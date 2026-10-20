"""FR-V-03/FR-S-09: automatic acceptance wraps the existing Retry fixer."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.agents.budget import AgentBudget
from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixProposal
from app.agents.validation_repair import ValidationRepair
from app.core.config import get_settings
from app.core.safety import PublicDataSafety
from app.domain.enums import Variant
from app.domain.models import IaCPackage, Violation
from app.domain.plan import DeploymentPlan
from app.domain.validation import RemediationReport, ValidationCheck, ValidationReport
from app.pipeline.demo_stub import DEMO_PLAN
from app.pipeline.stages import StageContext
from app.scanners.runner import ToolFailure
from app.scanners.scan import ScanResult

pytestmark = pytest.mark.req("FR-V-03", "FR-S-09", "NFR-01")


class Log:
    async def append(self, *args, **kwargs):
        pass


class Engine:
    def __init__(self, counts):
        self.counts = iter(counts)
        self.inputs = []

    async def validate(self, plan, files):
        self.inputs.append(dict(files))
        return ValidationReport.build(
            [
                ValidationCheck(
                    check_id="document.parse",
                    category="structure",
                    tool="builtin",
                    status="failed",
                    file_path="terraform/main.tf",
                    line_start=i + 1,
                    message="Document could not be parsed",
                )
                for i in range(next(self.counts))
            ],
            terraform_required=False,
        )


class Scanner:
    def __init__(self, new=False, failure=False):
        self.new, self.failure = new, failure
        self.inputs = []

    async def scan(self, files, variant, **kwargs):
        if self.failure:
            raise ToolFailure("trivy", "crash")
        self.inputs.append(dict(files))
        violations = (
            [
                Violation(
                    rule_id="NEW",
                    tool="trivy",
                    resource="new",
                    file_path="terraform/main.tf",
                    message="finding",
                    blocking=True,
                )
            ]
            if self.new and len(self.inputs) > 1
            else []
        )
        return ScanResult(
            violations, {"trivy": "ok", "checkov": "ok", "terraform": "ok"}
        )


class Fix:
    def __init__(self, accepted=True):
        self.calls = []
        self.accepted = accepted

    async def propose(self, **kwargs):
        self.calls.append(kwargs)
        return FixProposal(
            kwargs["path"],
            self.accepted,
            None,
            kwargs["files"][kwargs["path"]] + "# repaired\n" if self.accepted else None,
            {},
            (),
        )


def setup(counts, *, new=False, accepted=True, failure=False):
    engine, scanner, fixer = Engine(counts), Scanner(new, failure), Fix(accepted)
    security = SecurityAgent(scanner, fixer, None, get_settings())
    ctx = StageContext(
        uuid4(),
        SimpleNamespace(event_log=Log()),
        DeploymentPlan.model_validate(DEMO_PLAN),
    )
    package = IaCPackage(
        variant=Variant.COST, files={"terraform/main.tf": "# original\n"}
    )
    return ValidationRepair(security, engine), ctx, package


@pytest.mark.parametrize(
    "counts,new,accepted,reason",
    [
        ([1, 0], False, True, "improved"),
        ([1, 1], False, True, "no_improvement"),
        ([1, 0], True, True, "new_blocking_findings"),
        ([1], False, False, "invalid_patch"),
    ],
)
async def test_acceptance_and_atomic_rollback(counts, new, accepted, reason):
    repair, ctx, package = setup(counts, new=new, accepted=accepted)
    fixed, report, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=2,
        budget=AgentBudget(30),
        phase="before_security",
        metadata=RemediationReport(),
    )
    assert metadata.rounds[0].reason == reason
    assert (fixed.files != package.files) == (reason == "improved")
    assert report.summary.failed == (0 if reason == "improved" else 1)
    assert len(metadata.rounds) == 1
    assert len(repair.security.scanner.inputs) == (
        2 if reason in {"improved", "new_blocking_findings"} else 0
    )
    call = repair.security.fix_agent.calls[0]
    assert call["validation_failures"][0]["check_id"] == "document.parse"
    assert set(call["validation_failures"][0]) == {
        "check_id",
        "message",
        "file_path",
        "line_start",
        "line_end",
    }


async def test_round_limit_retains_accepted_progress():
    repair, ctx, package = setup([3, 2, 1])
    fixed, report, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=2,
        budget=AgentBudget(30),
        phase="before_security",
        metadata=RemediationReport(),
    )
    assert report.summary.failed == 1
    assert [r.reason for r in metadata.rounds] == [
        "improved",
        "improved",
        "round_limit",
    ]
    assert len(repair.security.fix_agent.calls) == 2
    assert fixed.files["terraform/main.tf"].count("repaired") == 2


async def test_deadline_and_scan_failure_never_apply_patch():
    repair, ctx, package = setup([1])
    now = [0.0]
    budget = AgentBudget(1, clock=lambda: now[0])
    now[0] = 2
    fixed, _, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=2,
        budget=budget,
        phase="before_security",
        metadata=RemediationReport(),
    )
    assert fixed.files == package.files and metadata.rounds[0].reason == "deadline"
    assert not repair.security.fix_agent.calls
    repair, ctx, package = setup([1, 0], failure=True)
    fixed, _, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=2,
        budget=AgentBudget(30),
        phase="before_security",
        metadata=RemediationReport(),
    )
    assert (
        fixed.files == package.files
        and metadata.rounds[0].reason == "verification_unavailable"
    )


async def test_cancellation_propagates_without_mutating_original():
    repair, ctx, package = setup([1])
    started = asyncio.Event()

    async def wait(**kwargs):
        started.set()
        await asyncio.Event().wait()

    repair.security.fix_agent.propose = wait
    task = asyncio.create_task(
        repair.run(
            ctx,
            Variant.COST,
            package,
            rounds=2,
            budget=AgentBudget(30),
            phase="before_security",
            metadata=RemediationReport(),
        )
    )
    await asyncio.wait_for(started.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert package.files == {"terraform/main.tf": "# original\n"}


async def test_new_candidate_canary_is_redacted_before_verification(canary_key):
    repair, ctx, package = setup([1, 0])
    repair.security.safety = PublicDataSafety(canary_key)
    key = canary_key.llm_api_key.get_secret_value()

    async def propose(**kwargs):
        return FixProposal(
            kwargs["path"],
            True,
            None,
            kwargs["files"][kwargs["path"]] + f"# {key}\n",
            {},
            (),
        )

    repair.security.fix_agent.propose = propose
    fixed, report, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=2,
        budget=AgentBudget(30),
        phase="before_security",
        metadata=RemediationReport(),
    )
    assert key not in str(
        (
            fixed.files,
            report,
            metadata,
            repair.engine.inputs,
            repair.security.scanner.inputs,
        )
    )
    assert "[REDACTED]" in fixed.files["terraform/main.tf"]


async def test_call_deadline_rolls_back_and_zero_rounds_never_calls_fixer():
    repair, ctx, package = setup([1])

    async def timeout(**kwargs):
        raise TimeoutError

    repair.security.fix_agent.propose = timeout
    fixed, _, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=2,
        budget=AgentBudget(30),
        phase="before_security",
        metadata=RemediationReport(),
    )
    assert fixed.files == package.files and metadata.rounds[0].reason == "deadline"
    repair, ctx, package = setup([1])
    _, _, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=0,
        budget=AgentBudget(30),
        phase="before_security",
        metadata=RemediationReport(),
    )
    assert not repair.security.fix_agent.calls
    assert metadata.rounds[0].reason == "round_limit"
