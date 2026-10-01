"""FR-S-03/05/06/09: real database state and report audit through the loop."""

import json
from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixProposal
from app.core.config import get_settings
from app.db.models import AgentEvent
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, PackageStatus, Severity, Variant
from app.domain.models import IaCPackage, Violation
from app.domain.plan import DeploymentPlan
from app.events.log import EventLog
from app.events.publisher import NullPublisher
from app.pipeline.demo_stub import DEMO_PLAN
from app.pipeline.stages import StageContext
from app.pipeline.state import PipelineStateWriter
from app.scanners.runner import ToolFailure
from app.scanners.scan import ScanResult


def finding(rule: str, tool: str = "checkov") -> Violation:
    return Violation.model_validate(
        {
            "rule_id": rule,
            "severity": "HIGH",
            "file_path": "terraform/main.tf",
            "resource": "aws_db_instance.db",
            "message": "unencrypted",
            "tool": tool,
            "blocking": True,
        }
    )


class ScriptedScanner:
    def __init__(self, scans: list[list[Violation]]) -> None:
        self.scans = scans
        self.calls = 0

    async def scan(
        self, files: dict[str, str], variant: Variant, *, iteration: int = 0
    ) -> ScanResult:
        self.calls += 1
        return ScanResult(self.scans.pop(0), {"checkov": "ok", "tfsec": "ok"})


class ScriptedFix:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def propose(self, **kwargs: Any) -> FixProposal:
        self.calls.append(kwargs)
        path: str = kwargs["path"]
        old: str = kwargs["files"][path]
        return FixProposal(
            path, True, None, old + f"# pass {len(self.calls)}\n", {}, ()
        )


async def setup(
    engine: AsyncEngine, max_iterations: int = 3
) -> tuple[StageContext, IaCPackage]:
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            run = await RunRepository(session).create(
                "secure infrastructure", LLMProvider.STUB, max_iterations
            )
            repository = PackageRepository(session)
            await repository.create(run.run_id, Variant.SECURITY)
            await repository.save_files(
                run.run_id, Variant.SECURITY, {"terraform/main.tf": "original\n"}
            )
            await repository.transition_status(
                run.run_id, Variant.SECURITY, PackageStatus.GENERATED
            )
    writer = PipelineStateWriter(sessions, EventLog(sessions, NullPublisher()))
    return (
        StageContext(
            run.run_id,
            writer,
            DeploymentPlan.model_validate(DEMO_PLAN),
            max_iterations=max_iterations,
        ),
        IaCPackage(variant=Variant.SECURITY, files={"terraform/main.tf": "original\n"}),
    )


def agent(
    engine: AsyncEngine,
    scanner: ScriptedScanner,
    fix: ScriptedFix,
    *,
    fixing_model: str | None = None,
) -> SecurityAgent:
    return SecurityAgent(  # type: ignore[arg-type]
        scanner,
        fix,
        make_session_factory(engine),
        get_settings(),
        versions={"checkov": "3.3.21", "tfsec": "v1.28.14"},
        fixing_model=fixing_model,
    )


@pytest.mark.req("FR-S-03", "FR-S-04", "FR-S-06", "FR-G-05")
async def test_two_fix_passes_and_three_first_scan_counts(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    ctx, package = await setup(engine)
    scanner = ScriptedScanner(
        [
            [finding("CKV_AWS_16"), finding("aws-rds-encrypt", "tfsec")],
            [finding("CKV_AWS_17")],
            [],
        ]
    )
    fix = ScriptedFix()
    status = await agent(engine, scanner, fix, fixing_model="fixture-fixer").run(
        ctx, Variant.SECURITY, package
    )
    assert status == PackageStatus.SCAN_CLEAN
    assert scanner.calls == 3
    assert len(fix.calls) == 2
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None
        assert row.iteration_count == 2
        assert row.original_files == {"terraform/main.tf": "original\n"}
        assert row.files["terraform/main.tf"].endswith("# pass 2\n")
        report = row.security_report
        assert report is not None
        assert report["fixing_model"] == "fixture-fixer"
        assert report["sessions"][0]["fixing_model"] == "fixture-fixer"
        first = report["sessions"][0]["final"]
        assert report["final"] == first
        assert first["first_scan_checkov_high_or_critical"] == 1
        assert first["first_scan_tfsec_high_or_critical"] == 1
        assert first["first_scan_combined_high_or_critical"] == 2
        assert report["sessions"][0]["fix_passes"] == 2
        assert len(report["sessions"][0]["iterations"]) == 3
        assert "# pass 1" in row.remediation_diff
        assert "# pass 2" in row.remediation_diff


@pytest.mark.req("FR-S-01", "FR-S-02", "FR-S-03")
async def test_syntax_fix_pass_rescans_full_package(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    ctx, _ = await setup(engine)
    invalid = 'locals "x" { a = 1 }\n'
    valid = "locals { a = 1 }\n"
    package = IaCPackage(variant=Variant.SECURITY, files={"terraform/main.tf": invalid})
    async with make_session_factory(engine)() as session:
        async with session.begin():
            await PackageRepository(session).save_files(
                ctx.run_id, Variant.SECURITY, package.files
            )

    class SyntaxScanner(ScriptedScanner):
        def __init__(self) -> None:
            super().__init__([])

        async def scan(
            self, files: dict[str, str], variant: Variant, *, iteration: int = 0
        ) -> ScanResult:
            self.calls += 1
            if files["terraform/main.tf"] == invalid:
                syntax = finding("TERRAFORM_SYNTAX", "tfsec").model_copy(
                    update={
                        "severity": Severity.CRITICAL,
                        "line_start": 1,
                        "line_end": 1,
                    }
                )
                return ScanResult(
                    [syntax], {"checkov": "ok", "tfsec": "syntax_limited"}, True
                )
            assert files["terraform/main.tf"] == valid
            return ScanResult([], {"checkov": "ok", "tfsec": "ok"})

    class SyntaxFix(ScriptedFix):
        async def propose(self, **kwargs: Any) -> FixProposal:
            self.calls.append(kwargs)
            return FixProposal(kwargs["path"], True, None, valid, {}, ())

    scanner = SyntaxScanner()
    fixer = SyntaxFix()
    assert (
        await agent(engine, scanner, fixer).run(ctx, Variant.SECURITY, package)
        == PackageStatus.SCAN_CLEAN
    )
    assert scanner.calls == 2
    assert len(fixer.calls) == 1
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None and row.security_report is not None
        assert row.files["terraform/main.tf"] == valid
        assert row.original_files == package.files
        iterations = row.security_report["sessions"][0]["iterations"]
        assert iterations[0]["scan"]["syntax_limited"] is True
        assert iterations[0]["scan"]["tfsec_other_findings_unavailable"] is True
        assert iterations[1]["scan"]["syntax_limited"] is False
        assert row.security_report["final"]["first_scan_tfsec_high_or_critical"] == 1


@pytest.mark.req("FR-S-02", "FR-S-04", "NFR-01")
async def test_safe_fix_rejection_reason_is_persisted(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    ctx, package = await setup(engine)

    class RejectFix(ScriptedFix):
        async def propose(self, **kwargs: Any) -> FixProposal:
            self.calls.append(kwargs)
            return FixProposal(
                kwargs["path"], False, "schema:file.content.missing", None, {}, ()
            )

    scanner = ScriptedScanner([[finding("CKV_AWS_16")], [finding("CKV_AWS_16")]])
    fixer = RejectFix()
    assert (
        await agent(engine, scanner, fixer).run(ctx, Variant.SECURITY, package)
        == PackageStatus.SCAN_EXHAUSTED
    )
    assert len(fixer.calls) == 1
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None and row.security_report is not None
        fixes = row.security_report["sessions"][0]["iterations"][0]["fixes"]
        assert fixes[0]["reason"] == "schema:file.content.missing"
        assert fixes[0]["accepted"] is False


@pytest.mark.req("FR-S-05", "FR-S-07", "FR-S-09")
async def test_no_progress_then_retry_appends_session_and_keeps_baseline(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    ctx, package = await setup(engine)
    scanner = ScriptedScanner([[finding("CKV_AWS_16")], [finding("CKV_AWS_16")]])
    fix = ScriptedFix()
    security = agent(engine, scanner, fix)
    assert (
        await security.run(ctx, Variant.SECURITY, package)
        == PackageStatus.SCAN_EXHAUSTED
    )
    assert scanner.calls == 2
    assert len(fix.calls) == 1
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None and row.security_report is not None
        old_session = deepcopy(row.security_report["sessions"][0])
        assert old_session["final"]["reason"] == "no progress"
        current = IaCPackage(variant=Variant.SECURITY, files=dict(row.files))
    for target in (
        PackageStatus.VALIDATING,
        PackageStatus.VALIDATION_ERROR,
        PackageStatus.PENDING_REVIEW,
    ):
        await ctx.writer.package_transition(
            ctx.run_id, Variant.SECURITY, target, message="review"
        )
    retry_scanner = ScriptedScanner([[]])
    retry_fix = ScriptedFix()
    retry = agent(engine, retry_scanner, retry_fix)
    assert (
        await retry.remediate_from_review(
            ctx, Variant.SECURITY, current, "Please fix", []
        )
        == PackageStatus.SCAN_CLEAN
    )
    assert len(retry_fix.calls) == 1
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None and row.security_report is not None
        assert row.original_files == {"terraform/main.tf": "original\n"}
        assert row.security_report["sessions"][0] == old_session
        assert row.security_report["sessions"][1]["kind"] == "review_retry"
        latest = row.security_report["sessions"][1]["final"]
        assert row.security_report["final"] == latest
        assert row.iteration_count == 1
        assert "# pass 1" in row.remediation_diff
        assert row.remediation_diff.count("# pass 1") == 2


@pytest.mark.req("FR-S-09")
@pytest.mark.parametrize("with_target", [True, False])
async def test_validation_only_and_feedback_only_review_retry(
    db_engines: tuple[AsyncEngine, AsyncEngine], with_target: bool
) -> None:
    engine, _ = db_engines
    ctx, package = await setup(engine)
    assert (
        await agent(engine, ScriptedScanner([[]]), ScriptedFix()).run(
            ctx, Variant.SECURITY, package
        )
        == PackageStatus.SCAN_CLEAN
    )
    for target in (
        PackageStatus.VALIDATING,
        PackageStatus.VALIDATION_ERROR,
        PackageStatus.PENDING_REVIEW,
    ):
        await ctx.writer.package_transition(
            ctx.run_id, Variant.SECURITY, target, message="review"
        )
    failures = (
        [{"file_path": "terraform/main.tf", "check": "bad reference", "line_start": 1}]
        if with_target
        else []
    )
    fixer = ScriptedFix()
    retry = agent(engine, ScriptedScanner([[]]), fixer)
    assert (
        await retry.remediate_from_review(
            ctx, Variant.SECURITY, package, "Please repair", failures
        )
        == PackageStatus.SCAN_CLEAN
    )
    assert len(fixer.calls) == int(with_target)
    if with_target:
        assert fixer.calls[0]["feedback"] == "Please repair"
        assert fixer.calls[0]["validation_failures"] == failures
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None and row.security_report is not None
        retry_session = row.security_report["sessions"][1]
        if not with_target:
            assert retry_session["iterations"][0]["notice"] == (
                "no file could be targeted; feedback was not applied"
            )
            notices = list(await session.scalars(select(AgentEvent)))
            assert any(
                item.payload.get("notice")
                == "no file could be targeted; feedback was not applied"
                for item in notices
            )


@pytest.mark.req("FR-S-05")
async def test_time_budget_stops_before_fix_call(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    ctx, package = await setup(engine)
    now = [0.0]
    ctx = replace(ctx, clock=lambda: now[0])

    class ExpiringScanner(ScriptedScanner):
        async def scan(
            self, files: dict[str, str], variant: Variant, *, iteration: int = 0
        ) -> ScanResult:
            now[0] = 239.5
            return await super().scan(files, variant)

    fixer = ScriptedFix()
    result = await agent(engine, ExpiringScanner([[finding("CKV_AWS_16")]]), fixer).run(
        ctx, Variant.SECURITY, package
    )
    assert result == PackageStatus.SCAN_EXHAUSTED
    assert fixer.calls == []
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None and row.security_report is not None
        assert row.security_report["sessions"][0]["final"]["reason"] == "time budget"


@pytest.mark.req("NFR-01")
async def test_scanner_finding_does_not_store_canary_key(
    db_engines: tuple[AsyncEngine, AsyncEngine], canary_key: Any
) -> None:
    engine, _ = db_engines
    ctx, package = await setup(engine)
    key = canary_key.require_llm_key()
    advisory = finding("CKV_UNKNOWN").model_copy(
        update={
            "blocking": False,
            "title": key,
            "message": key,
            "severity": Severity.UNKNOWN,
        }
    )
    scanner = ScriptedScanner([[advisory]])
    security = SecurityAgent(  # type: ignore[arg-type]
        scanner,
        ScriptedFix(),
        make_session_factory(engine),
        canary_key,
    )
    assert (
        await security.run(ctx, Variant.SECURITY, package) == PackageStatus.SCAN_CLEAN
    )
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        events = list(await session.scalars(select(AgentEvent)))
        assert row is not None
        assert key not in json.dumps(row.security_report)
        assert key not in json.dumps([item.payload for item in events])


@pytest.mark.req("FR-S-01", "FR-G-05")
async def test_scan_error_has_no_first_scan_counts(
    db_engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    engine, _ = db_engines
    ctx, package = await setup(engine)

    class FailingScanner:
        async def scan(
            self, files: dict[str, str], variant: Variant, *, iteration: int = 0
        ) -> ScanResult:
            raise ToolFailure("checkov", "invalid_json")

    security = agent(engine, FailingScanner(), ScriptedFix())  # type: ignore[arg-type]
    assert (
        await security.run(ctx, Variant.SECURITY, package) == PackageStatus.SCAN_ERROR
    )
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
        assert row is not None and row.security_report is not None
        final = row.security_report["final"]
        assert final["first_scan_checkov_high_or_critical"] is None
        assert final["first_scan_tfsec_high_or_critical"] is None
        assert final["first_scan_combined_high_or_critical"] is None
