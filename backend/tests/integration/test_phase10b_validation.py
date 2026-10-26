"""FR-S-02/07: validation repair cannot bypass exposure preservation."""

from dataclasses import replace

import pytest

from app.agents.budget import AgentBudget
from app.agents.security.fix import FixProposal
from app.agents.validation_repair import ValidationRepair
from app.domain.enums import Variant
from app.domain.models import IaCPackage
from app.domain.validation import RemediationReport, ValidationCheck, ValidationReport
from tests.integration.test_security_agent import ScriptedScanner, agent, setup
from tests.unit.test_phase10b_conformance import plan


@pytest.mark.req("FR-S-02", "FR-S-07", "FR-A-05")
async def test_validation_improvement_never_accepts_internal_flip(db_engines):
    engine, _ = db_engines
    ctx, _ = await setup(engine)
    ctx = replace(ctx, plan=plan())
    files = {"terraform/main.tf": 'resource "aws_lb" "edge" { internal = false }\n'}

    class Flipper:
        async def propose(self, **kwargs):
            return FixProposal(
                kwargs["path"],
                True,
                None,
                kwargs["files"][kwargs["path"]].replace("false", "true"),
                {},
                (),
            )

    class Validator:
        async def validate(self, plan, files):
            return ValidationReport.build(
                [
                    ValidationCheck(
                        check_id="terraform.validate",
                        category="terraform",
                        tool="terraform",
                        status="passed"
                        if "true" in files["terraform/main.tf"]
                        else "failed",
                        message="synthetic",
                        file_path="terraform/main.tf",
                    )
                ],
                terraform_required=True,
            )

    security = agent(engine, ScriptedScanner([]), Flipper())
    package, report, metadata = await ValidationRepair(security, Validator()).run(
        ctx,
        Variant.SECURITY,
        IaCPackage(variant=Variant.SECURITY, files=files),
        rounds=1,
        budget=AgentBudget(60),
        phase="after_security",
        metadata=RemediationReport(),
    )
    assert package.files == files and report.summary.result == "invalid"
    assert metadata.rounds[-1].reason == "plan_conformance_regression"
    assert metadata.rounds[-1].plan_conformance[0]["property"] == "exposure"
    assert security.scanner.calls == 0
