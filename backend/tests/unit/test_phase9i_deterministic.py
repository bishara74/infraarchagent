"""FR-V-03/NFR-01: deterministic proposals retain the existing strict guards."""

from types import SimpleNamespace

import pytest

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationCheck, ValidationReport
from app.pipeline.demo_stub import DEMO_PLAN
from app.scanners.runner import ToolFailure
from app.scanners.scan import ScanResult
from app.validation.formats import repair_formats

pytestmark = pytest.mark.req("FR-V-03", "FR-V-04", "FR-S-09", "NFR-01")

FILES = {"monitoring/grafana/app.json": '{"dashboard":{"panels":[]}}'}


def report(failed):
    checks = (
        [
            ValidationCheck(
                check_id="grafana.panels",
                category="structure",
                tool="builtin",
                status="failed",
                message="Dashboard panels missing",
                file_path="monitoring/grafana/app.json",
            )
        ]
        if failed
        else []
    )
    return ValidationReport.build(checks, terraform_required=False)


class Engine:
    def __init__(self, failed):
        self.failed, self.calls = failed, 0

    async def validate(self, plan, files):
        self.calls += 1
        return report(self.failed)


class Scanner:
    def __init__(self, mode):
        self.mode, self.calls = mode, 0

    async def scan(self, files, variant):
        self.calls += 1
        if self.calls > 1 and self.mode == "unavailable":
            raise ToolFailure("trivy", "tool_error")
        findings = (
            [
                Violation(
                    tool="trivy",
                    rule_id="NEW",
                    resource="dashboard",
                    file_path="monitoring/grafana/app.json",
                    message="New blocking finding",
                    blocking=True,
                )
            ]
            if self.calls > 1 and self.mode == "new_blocker"
            else []
        )
        return ScanResult(findings, {"trivy": "ok", "checkov": "ok", "terraform": "ok"})


class Verifier:
    async def checks(self, files):
        return []


@pytest.mark.parametrize(
    "mode,failed,reason",
    [
        ("clean", False, "improved"),
        ("clean", True, "no_improvement"),
        ("new_blocker", False, "new_blocking_findings"),
        ("unavailable", False, "verification_unavailable"),
    ],
)
async def test_deterministic_wrapper_records_guards_and_retains_rejected_bytes(
    mode, failed, reason
):
    engine, scanner = Engine(failed), Scanner(mode)
    security = SimpleNamespace(scanner=scanner, terraform_verifier=Verifier())
    before = report(True)
    files, final, records = await checked_one(
        FILES,
        DeploymentPlan.model_validate(DEMO_PLAN),
        Variant.COST,
        before,
        engine,
        security,
        AgentBudget(30),
        repair_formats,
    )
    accepted = reason == "improved"
    assert (files != FILES) is accepted
    assert records[0]["outcome"] == ("accepted" if accepted else "rejected")
    assert records[0]["reason"] == reason
    assert records[0]["before_hash"] != records[0]["after_hash"]
    if not accepted:
        assert final == before
    else:
        assert repair_formats(files) == (files, [])


async def test_expired_budget_keeps_proposal_audit_without_running_tools():
    now = [0.0]
    budget = AgentBudget(1, clock=lambda: now[0])
    now[0] = 2.0
    engine, scanner = Engine(False), Scanner("clean")
    files, _, records = await checked_one(
        FILES,
        DeploymentPlan.model_validate(DEMO_PLAN),
        Variant.COST,
        report(True),
        engine,
        SimpleNamespace(scanner=scanner, terraform_verifier=Verifier()),
        budget,
        repair_formats,
    )
    assert files == FILES and scanner.calls == engine.calls == 0
    assert records[0]["outcome"] == "rejected"
    assert records[0]["reason"] == "verification_unavailable"
