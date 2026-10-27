"""FR-S-03/09: per-iteration validation, selective rollback and syntax gates."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents.budget import AgentBudget
from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixProposal, validate_fix
from app.core.config import get_settings
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationCheck
from app.pipeline.demo_stub import DEMO_PLAN
from app.pipeline.stages import StageContext
from app.scanners.scan import ScanResult

pytestmark = pytest.mark.req("FR-S-03", "FR-S-09", "FR-V-03", "PR-05", "NFR-01")


def checks(count):
    if count is None:
        return [
            ValidationCheck(
                check_id="terraform.validate",
                category="terraform",
                tool="terraform",
                status="skipped",
                message="Unavailable",
                skip_reason="not_installed",
            )
        ]
    return [
        ValidationCheck(
            check_id="terraform.validate",
            category="terraform",
            tool="terraform",
            status="failed",
            file_path="terraform/main.tf",
            line_start=i + 1,
            message="Missing required argument",
        )
        for i in range(count)
    ]


class Verifier:
    def __init__(self, counts):
        self.counts = iter(counts)
        self.last = None
        self.inputs = []

    async def checks(self, files):
        self.inputs.append(dict(files))
        self.last = next(self.counts, self.last)
        return checks(self.last)


class Fix:
    async def propose(self, **kw):
        return FixProposal(
            kw["path"],
            True,
            None,
            kw["files"][kw["path"]] + "# changed\n",
            {"terraform/added.tf": "locals { added = true }\n"}
            if kw["path"].startswith("terraform/")
            else {},
            (),
        )


def setup(counts=(0, 1), new_blocker=False):
    files = {
        "terraform/main.tf": "locals { original = true }\n",
        "ansible/play.yaml": "- hosts: localhost\n  tasks: []\n",
    }
    value = dict(DEMO_PLAN)
    value["file_types"] = ["terraform", "ansible"]
    ctx = StageContext(uuid4(), SimpleNamespace(), DeploymentPlan.model_validate(value))
    baseline = ScanResult([], {"checkov": "ok", "trivy": "ok", "terraform": "ok"})

    class Scanner:
        def __init__(self):
            self.inputs = []

        async def scan(self, files, *a, **kw):
            self.inputs.append(dict(files))
            return ScanResult(
                [
                    Violation(
                        rule_id="NEW",
                        file_path="terraform/main.tf",
                        resource="new",
                        tool="trivy",
                        message="new",
                        blocking=True,
                    )
                ]
                if new_blocker
                else [],
                baseline.tool_status,
            )

    scanner = Scanner()
    verifier = Verifier(counts)
    security = SecurityAgent(
        scanner, Fix(), None, get_settings(), terraform_verifier=verifier
    )
    return files, ctx, security, baseline, scanner, verifier


async def test_regression_restores_terraform_and_new_files_but_keeps_verified_yaml():
    files, ctx, security, baseline, scanner, verifier = setup()
    record = {}
    kept, fixes, diff, _ = await security._fix_iteration(
        ctx,
        Variant.SECURITY,
        files,
        dict.fromkeys(files, []),
        AgentBudget(30),
        baseline,
        record,
        feedback=None,
        validation_failures=[],
    )
    assert kept["terraform/main.tf"] == files["terraform/main.tf"]
    assert "terraform/added.tf" not in kept
    assert kept["ansible/play.yaml"].endswith("# changed\n")
    assert scanner.inputs == [kept]
    assert record["before_failed"] == 0 and record["after_failed"] == 1
    assert record["reasons"] == ["terraform_regression"]
    assert not record["deadline_only"]
    assert "terraform/main.tf" not in diff
    # The added locals block receives one independent fallback evaluation.
    assert len(verifier.inputs) == 3
    assert record["retained_failed"] == 0


@pytest.mark.parametrize(
    "before,after,accepted",
    [(None, None, True), (None, 0, True), (1, 2, False), (1, 1, True)],
)
async def test_unknown_and_equal_counts(before, after, accepted):
    files, ctx, security, baseline, _, _ = setup((before, after))
    record = {}
    kept, _, _, _ = await security._fix_iteration(
        ctx,
        Variant.SECURITY,
        files,
        {"terraform/main.tf": []},
        AgentBudget(30),
        baseline,
        record,
        feedback=None,
        validation_failures=[],
    )
    assert (kept["terraform/main.tf"] != files["terraform/main.tf"]) == accepted
    if before is None and after is None:
        assert record["reasons"] == []
        assert record["unchanged_terraform_unavailability"] == ["not_installed"]
        assert record["retained_failed"] is None


async def test_new_blocker_rolls_back_whole_candidate():
    files, ctx, security, baseline, _, _ = setup((0, 0), new_blocker=True)
    record = {}
    kept, _, _, _ = await security._fix_iteration(
        ctx,
        Variant.SECURITY,
        files,
        dict.fromkeys(files, []),
        AgentBudget(30),
        baseline,
        record,
        feedback=None,
        validation_failures=[],
    )
    assert kept == files
    assert record["reasons"] == ["new_blocking_findings"]


async def test_timeout_records_verification_time_without_claiming_validity():
    files, ctx, security, baseline, _, _ = setup((0,))

    class Waiting(Verifier):
        async def checks(self, files):
            if self.inputs:
                await asyncio.Event().wait()
            return await super().checks(files)

    security.terraform_verifier = Waiting((0,))
    record = {}
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.05):
            await security._fix_iteration(
                ctx,
                Variant.SECURITY,
                files,
                {"terraform/main.tf": []},
                AgentBudget(30),
                baseline,
                record,
                feedback=None,
                validation_failures=[],
            )
    assert record["candidate_created"]
    assert record["terraform_verification_seconds"] > 0
    assert "after_failed" not in record


@pytest.mark.parametrize(
    "path,content,kind",
    [
        ("terraform/main.tf", "resource {", "terraform"),
        ("k8s/app.yaml", "a: [", "kubernetes"),
        ("monitoring/grafana/app.json", "{", "grafana"),
    ],
)
def test_patch_syntax_rejection(path, content, kind):
    value = dict(DEMO_PLAN)
    value["file_types"] = list(dict.fromkeys(["terraform", kind]))
    proposal = validate_fix(
        {"file": {"path": path, "content": content}},
        path=path,
        files={"terraform/main.tf": "locals { clean = true }\n", path: "{}\n"},
        plan=DeploymentPlan.model_validate(value),
    )
    assert not proposal.accepted and proposal.reason == "invalid_syntax"
