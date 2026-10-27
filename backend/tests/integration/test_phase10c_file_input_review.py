"""FR-S-02/06 and NFR-01: real scanner refusal follows existing review states."""

from dataclasses import replace
from unittest.mock import AsyncMock

import pytest

from app.agents.security.fix import FixProposal
from app.agents.validator import ValidatorAgent
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, RunStatus, Variant
from app.domain.models import IaCPackage
from app.domain.review import package_presentation
from app.domain.states import readiness_after_validation
from app.domain.validation import ValidationCheck, ValidationReport
from app.scanners.scan import Scanner
from tests.integration.test_security_agent import agent, setup
from tests.unit.test_phase10b_conformance import plan
from tests.unit.test_phase10c_file_inputs import SafeRunner, files

pytestmark = pytest.mark.req("FR-S-01", "FR-S-02", "FR-S-06", "FR-V-03", "NFR-01")


async def test_blocked_dynamic_hash_reaches_pending_review(db_engines, monkeypatch):
    engine, _ = db_engines
    ctx, _ = await setup(engine, max_iterations=1)
    ctx = replace(ctx, plan=plan(kind="lambda"))
    source = files("filebase64sha256(var.lambda_zip_path)")
    package = IaCPackage(variant=Variant.SECURITY, files=source)

    class NoChange:
        async def propose(self, **kwargs):
            return FixProposal(kwargs["path"], False, "not_fixable", None, {}, ())

    launch = AsyncMock(side_effect=AssertionError("refused Terraform read launched"))
    monkeypatch.setattr("asyncio.create_subprocess_exec", launch)
    scan_status = await agent(engine, Scanner(SafeRunner()), NoChange()).run(
        ctx, Variant.SECURITY, package
    )
    assert scan_status == PackageStatus.SCAN_EXHAUSTED
    launch.assert_not_called()

    class Validator:
        async def validate(self, plan, source):
            return ValidationReport.build(
                [
                    ValidationCheck(
                        check_id="terraform.validate",
                        category="terraform",
                        tool="terraform",
                        status="skipped",
                        message="Dynamic file input cannot be verified offline",
                        skip_reason="uninspectable_file_input",
                        file_path="terraform/main.tf",
                    )
                ],
                terraform_required=True,
            )

    sessions = make_session_factory(engine)
    validation = await ValidatorAgent(Validator(), sessions).run(
        ctx, Variant.SECURITY, package
    )
    assert validation == PackageStatus.VALIDATION_ERROR
    target = readiness_after_validation(scan_status, validation)
    assert target == PackageStatus.PENDING_REVIEW
    await ctx.writer.package_transition(
        ctx.run_id, Variant.SECURITY, target, message="review blocked file input"
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row.files == source
        finding = row.security_report["final"]["remaining_blocking"][0]
        assert finding["rule_id"] == "TERRAFORM_FILE_INPUT"
        presentation = package_presentation(
            RunStatus.PARTIAL_SUCCESS,
            target,
            row.files,
            row.security_report,
            row.validation_report,
            None,
        )
        assert presentation["review_available"] and not presentation["downloadable"]
