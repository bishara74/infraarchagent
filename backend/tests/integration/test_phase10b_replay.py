"""FR-S-02/03/07: fixed synthetic author run-3/run-4 regression replays."""

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest

from app.agents.security.fix import FixProposal
from app.agents.validator import ValidatorAgent
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, RunStatus, Variant
from app.domain.models import IaCPackage, Violation
from app.domain.plan import DeploymentPlan
from app.domain.review import package_presentation
from app.domain.states import readiness_after_validation
from app.domain.validation import ValidationCheck, ValidationReport
from app.security.plan_conformance import SERVICE_TYPES, View, label, plan_regressions
from tests.integration.test_security_agent import agent, setup

CASES = json.loads(
    (Path(__file__).parents[1] / "fixtures/phase10b-author-exposure.json").read_text()
)["cases"]
pytestmark = pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-07", "FR-A-05")


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_complete_retained_author_candidate_is_rejected(case):
    plan = DeploymentPlan.model_validate(case["plan"])
    assert case["synthetic"]
    conflicts = plan_regressions(plan, case["original_files"], case["candidate_files"])
    assert any(
        c["property"] == "exposure" and c["expected"] == "public" for c in conflicts
    )


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
async def test_actual_security_loop_retains_public_files_and_requires_review(
    db_engines, case
):
    engine, _ = db_engines
    ctx, _ = await setup(engine, max_iterations=1)
    plan = DeploymentPlan.model_validate(case["plan"])
    ctx = replace(ctx, plan=plan)
    variant = Variant(case["source"]["variant"])
    files = case["original_files"]
    view = View(files)
    service = next(
        s
        for s in plan.services
        if s.name in plan.network.public_services
        and label(s.aws_service) in SERVICE_TYPES
        and SERVICE_TYPES[label(s.aws_service)] & {"aws_lb", "aws_alb", "aws_elb"}
    )
    lb = view.bind(service.name, SERVICE_TYPES[label(service.aws_service)], True)
    assert lb is not None and view.exposure(lb) == "public"
    violation = Violation(
        rule_id="AWS-0053",
        resource=lb.address,
        file_path=lb.path,
        message="Load balancer exposed to the internet",
        tool="trivy",
        blocking=True,
    )

    class Scanner:
        async def scan(self, source, variant, *, iteration=0):
            from app.scanners.scan import ScanResult

            updated = View(source)
            item = updated.resources.get((lb.module, lb.address))
            return ScanResult(
                [violation] if item and updated.exposure(item) == "public" else [],
                {"checkov": "ok", "trivy": "ok"},
            )

    class Fixer:
        async def propose(self, **kwargs):
            path = kwargs["path"]
            source = kwargs["files"][path]
            if path.endswith(".json"):
                data = json.loads(source)
                data["resource"][lb.type][lb.name]["internal"] = True
                source = json.dumps(data)
            else:
                source, count = re.subn(
                    r"\binternal\s*=\s*false\b", "internal = true", source, count=1
                )
                assert count == 1
            return FixProposal(path, True, None, source, {}, ())

    sessions = make_session_factory(engine)
    async with sessions() as session, session.begin():
        repository = PackageRepository(session)
        if variant != Variant.SECURITY:
            await repository.create(ctx.run_id, variant)
            await repository.transition_status(
                ctx.run_id, variant, PackageStatus.GENERATED
            )
    security = agent(engine, Scanner(), Fixer())
    outcome = await security.run(ctx, variant, IaCPackage(variant=variant, files=files))
    assert outcome == PackageStatus.SCAN_EXHAUSTED
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, variant)
        assert (
            View(row.files).exposure(View(row.files).resources[(lb.module, lb.address)])
            == "public"
        )
        assert (
            row.security_report["final"]["remaining_blocking"][0]["rule_id"]
            == "AWS-0053"
        )
        retained = IaCPackage(variant=variant, files=row.files)

    class Validator:
        async def validate(self, plan, source):
            # Recorded valid outcome isolates readiness; no deployment is claimed.
            return ValidationReport.build(
                [
                    ValidationCheck(
                        check_id="terraform.validate",
                        category="terraform",
                        tool="terraform",
                        status="passed",
                        message="Recorded valid replay outcome",
                    )
                ],
                terraform_required=True,
            )

    validation = await ValidatorAgent(Validator(), sessions).run(ctx, variant, retained)
    target = readiness_after_validation(outcome, validation)
    await ctx.writer.package_transition(
        ctx.run_id, variant, target, message="recorded replay readiness"
    )
    assert target == PackageStatus.PENDING_REVIEW
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, variant)
        presentation = package_presentation(
            RunStatus.PARTIAL_SUCCESS,
            target,
            row.files,
            row.security_report,
            row.validation_report,
            None,
        )
        assert (
            presentation["plan_conflicts"]
            and "plan_conformance_conflict" in presentation["review_reasons"]
        )
