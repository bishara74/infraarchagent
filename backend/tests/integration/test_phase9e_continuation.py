"""FR-S-03/04/05/09: real loop continuation retains verified package baselines."""

from dataclasses import replace

import pytest

from app.agents.security.fix import FixProposal
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, Variant
from app.domain.plan import DeploymentPlan
from app.scanners.scan import ScanResult
from tests.integration.test_security_agent import agent, finding, setup
from tests.unit.test_phase9e_iteration import checks

pytestmark = pytest.mark.req(
    "FR-S-03", "FR-S-04", "FR-S-05", "FR-S-09", "PR-05", "NFR-01"
)


@pytest.mark.parametrize(
    "mode",
    [
        "regression",
        "new_blocker",
        "no_change",
        "repeated",
        "always_regress",
        "mixed",
        "timeout",
        "stage_timeout",
        "baseline_timeout",
        "retry_regression",
        "retry_timeout",
        "retry_no_change",
    ],
)
async def test_full_loop_retains_baseline_and_uses_available_allowance(
    db_engines, mode
):
    review_retry = mode.startswith("retry_")
    mode = mode.removeprefix("retry_")
    engine, _ = db_engines
    ctx, package = await setup(engine, max_iterations=4)
    now = [0.0]
    ctx = replace(ctx, clock=lambda: now[0])
    if mode == "mixed":
        files = {
            **package.files,
            "ansible/play.yaml": "- hosts: localhost\n  tasks: []\n",
        }
        package = package.model_copy(update={"files": files})
        ctx = replace(
            ctx,
            plan=DeploymentPlan.model_validate(
                {**ctx.plan.model_dump(), "file_types": ["terraform", "ansible"]}
            ),
        )
        async with make_session_factory(engine)() as session:
            async with session.begin():
                await PackageRepository(session).save_files(
                    ctx.run_id, Variant.SECURITY, files
                )

    class Scanner:
        def __init__(self):
            self.inputs = []

        async def scan(self, files, *args, **kwargs):
            self.inputs.append(dict(files))
            violations = (
                [] if "# fixed" in files["terraform/main.tf"] else [finding("RULE")]
            )
            if mode == "repeated":
                violations = [finding("RULE")]
            if mode == "new_blocker" and "# bad" in files["terraform/main.tf"]:
                violations = [finding("NEW")]
            if mode == "mixed" and "# fixed" not in files["ansible/play.yaml"]:
                violations.append(
                    finding("YAML").model_copy(
                        update={"file_path": "ansible/play.yaml"}
                    )
                )
            return ScanResult(
                violations, {"terraform": "ok", "checkov": "ok", "trivy": "ok"}
            )

    class Fix:
        def __init__(self):
            self.calls = []

        async def propose(self, **kwargs):
            self.calls.append(kwargs)
            path = kwargs["path"]
            tf_attempt = sum(c["path"] == "terraform/main.tf" for c in self.calls)
            if mode == "no_change":
                return FixProposal(path, False, "new_file_exists", None, {}, ())
            bad = mode == "always_regress" or (
                mode in {"regression", "new_blocker", "mixed"}
                and tf_attempt == 1
                and path.startswith("terraform/")
            )
            if mode == "stage_timeout" or (mode == "timeout" and tf_attempt == 1):
                now[0] += 61
            return FixProposal(
                path,
                True,
                None,
                kwargs["files"][path] + ("# bad\n" if bad else "# fixed\n"),
                {"terraform/added.tf": "locals { candidate = true }\n"} if bad else {},
                (),
            )

    class Verifier:
        def __init__(self):
            self.inputs = []

        async def checks(self, files):
            self.inputs.append(dict(files))
            if mode == "baseline_timeout":
                now[0] += 61
            return checks(
                int("# bad" in files["terraform/main.tf"] and mode != "new_blocker")
            )

    scanner, fixer, verifier = Scanner(), Fix(), Verifier()
    security = agent(engine, scanner, fixer)
    security.terraform_verifier = verifier
    if mode == "stage_timeout":
        security.settings = security.settings.model_copy(
            update={"security_deadline_seconds": 70}
        )
    prior = None
    if review_retry:

        class Reject:
            async def propose(self, **kwargs):
                return FixProposal(
                    kwargs["path"], False, "new_file_exists", None, {}, ()
                )

        await agent(engine, scanner, Reject()).run(ctx, Variant.SECURITY, package)
        async with make_session_factory(engine)() as session:
            old = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
            prior = old.security_report["sessions"][0]
            package = package.model_copy(
                update={"security_report": old.security_report}
            )
        for target in (
            PackageStatus.VALIDATING,
            PackageStatus.INVALID,
            PackageStatus.PENDING_REVIEW,
        ):
            await ctx.writer.package_transition(
                ctx.run_id, Variant.SECURITY, target, message="review"
            )
        result = await security.remediate_from_review(
            ctx, Variant.SECURITY, package, "Please repair", []
        )
        assert all(call["feedback"] == "Please repair" for call in fixer.calls)
    else:
        result = await security.run(ctx, Variant.SECURITY, package)
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    report = row.security_report["sessions"][-1]
    if prior is not None:
        assert row.security_report["sessions"][0] == prior
        assert len(row.security_report["sessions"]) == 2
    exhausted = mode in {
        "no_change",
        "repeated",
        "always_regress",
        "stage_timeout",
        "baseline_timeout",
        "retry_regression",
        "retry_timeout",
        "retry_no_change",
    }
    expected = (
        0
        if mode == "baseline_timeout"
        else 4
        if mode in {"no_change", "repeated", "always_regress"}
        else 2
    )
    assert result == (
        PackageStatus.SCAN_EXHAUSTED if exhausted else PackageStatus.SCAN_CLEAN
    )
    assert row.iteration_count == report["fix_passes"] == expected
    assert sum(c["path"] == "terraform/main.tf" for c in fixer.calls) == expected
    assert report["final"]["reason"] == (
        "time budget"
        if mode in {"baseline_timeout", "stage_timeout"}
        else "iteration limit"
        if exhausted
        else None
    )
    assert (
        "# bad" not in row.files["terraform/main.tf"]
        and "terraform/added.tf" not in row.files
    )
    if mode in {"regression", "always_regress", "mixed"}:
        assert all(
            "# bad" not in verifier.inputs[i]["terraform/main.tf"]
            for i in range(0, len(verifier.inputs), 2)
        )
        assert report["iterations"][0]["verification"]["reasons"] == [
            "terraform_regression"
        ]
    if mode == "mixed":
        assert "# fixed" in verifier.inputs[2]["ansible/play.yaml"]
        assert "# fixed" in row.files["ansible/play.yaml"]
    if mode in {
        "regression",
        "no_change",
        "always_regress",
        "mixed",
        "new_blocker",
        "timeout",
    }:
        assert fixer.calls[-1]["previous_attempt"]
    if mode == "timeout":
        assert report["iterations"][0]["verification"]["deadline_only"] is True
        assert (
            row.files["terraform/main.tf"]
            == package.files["terraform/main.tf"] + "# fixed\n"
        )
    if mode == "baseline_timeout":
        assert not fixer.calls and len(verifier.inputs) == 4
