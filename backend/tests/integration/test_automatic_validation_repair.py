"""FR-V-03: security-introduced invalidity is repaired and verified durably."""

from types import SimpleNamespace

import pytest

from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixProposal
from app.agents.validator import ValidatorAgent
from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, PackageStatus, Variant
from app.domain.run_config import RunConfig
from app.domain.validation import ValidationCheck, ValidationReport
from app.pipeline.orchestrator import PipelineOrchestrator
from app.scanners.runner import ToolFailure
from tests.integration.test_security_agent import ScriptedScanner, finding, setup


@pytest.mark.req("FR-V-03", "FR-V-04", "FR-S-07", "FR-S-09")
@pytest.mark.parametrize("final_scan_fails", [False, True])
async def test_final_security_and_validation_describe_repaired_files(
    db_engines, final_scan_fails
):
    engine, _ = db_engines
    ctx, package = await setup(engine)
    sessions = make_session_factory(engine)
    settings = get_settings()
    validations = []
    fixes = []

    class Engine:
        async def validate(self, plan, files):
            validations.append(dict(files))
            checks = (
                [
                    ValidationCheck(
                        check_id="terraform.validate",
                        category="terraform",
                        tool="terraform",
                        status="failed",
                        file_path="terraform/main.tf",
                        line_start=1,
                        message="Unsupported argument",
                    )
                ]
                if "broken" in files["terraform/main.tf"]
                else []
            )
            return ValidationReport.build(checks, terraform_required=False)

    class Fix:
        async def propose(self, **kwargs):
            fixes.append(kwargs)
            old = kwargs["files"][kwargs["path"]]
            content = (
                old.replace("# broken\n", "")
                if kwargs["validation_failures"]
                else old + "# broken\n"
            )
            return FixProposal(kwargs["path"], True, None, content, {}, ())

    class Scanner(ScriptedScanner):
        async def scan(self, *args, **kwargs):
            if final_scan_fails and self.calls == 4:
                raise ToolFailure("trivy", "crash")
            return await super().scan(*args, **kwargs)

    scanner = Scanner([[finding("FIRST")], [], [], [], []])
    security = SecurityAgent(scanner, Fix(), sessions, settings)
    orchestrator = PipelineOrchestrator(
        ctx.run_id,
        "Deploy infrastructure",
        RunConfig(),
        factory=SimpleNamespace(settings=settings),
        session_factory=sessions,
        writer=ctx.writer,
        security_stage=security,
        validation_stage=ValidatorAgent(Engine(), sessions, settings=settings),
    )
    outcome = await orchestrator._post_generation(ctx, Variant.SECURITY, package)
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    assert row.original_files == package.files
    assert any("broken" in f["terraform/main.tf"] for f in validations)
    assert len(fixes) == 2 and fixes[1]["validation_failures"]
    if final_scan_fails:
        assert outcome == PackageStatus.SCAN_ERROR
    else:
        assert outcome == PackageStatus.PRODUCTION_READY
        assert row.files == package.files == validations[-1]
        assert row.validation_report["summary"]["result"] == "valid"
        assert (
            row.validation_report["remediation"]["rounds"][0]["phase"]
            == "after_security"
        )
        assert row.security_report["final"]["remaining_blocking"] == []
        assert "final_verification" in row.security_report
        assert row.iteration_count == 1


@pytest.mark.req("FR-S-09", "FR-V-04")
async def test_engineer_retry_preserves_automatic_repair_history(
    db_engines, monkeypatch
):
    from tests.integration.test_pipeline_review import (
        client_for,
        install_retry,
        pending_app,
        review_url,
        state,
    )

    engine, _ = db_engines
    app, run_id = await pending_app(engine)
    metadata = {
        "deterministic_repairs": [
            {
                "file": "terraform/variables.tf",
                "kind": "missing_variable",
                "name": "region",
            }
        ],
        "rounds": [],
    }
    async with app.state.session_factory() as session:
        async with session.begin():
            row = await PackageRepository(session).get_for_update(run_id, Variant.COST)
            row.validation_report = {**row.validation_report, "remediation": metadata}
    install_retry(app, monkeypatch)
    async with client_for(app) as client:
        response = await client.post(review_url(run_id), json={"action": "retry"})
        assert response.status_code == 202
        import asyncio

        await asyncio.gather(*app.state.runner.tasks.values())
    _, row = await state(app, run_id)
    assert row.validation_report["remediation"] == metadata


@pytest.mark.req("FR-V-03", "NFR-01")
@pytest.mark.parametrize("provider", [LLMProvider.STUB, LLMProvider.OPENAI])
async def test_review_demo_bypass_is_scoped_to_stub_runs(db_engines, provider):
    engine, _ = db_engines
    ctx, package = await setup(engine)
    sessions = make_session_factory(engine)
    settings = get_settings().model_copy(update={"pipeline_demo_scenario": "review"})

    class Engine:
        async def validate(self, plan, files):
            return ValidationReport.build([], terraform_required=False)

    scanner = ScriptedScanner([[], []])
    security = SecurityAgent(scanner, None, sessions, settings)
    orchestrator = PipelineOrchestrator(
        ctx.run_id,
        "Deploy infrastructure",
        RunConfig(provider=provider, model="fake"),
        factory=SimpleNamespace(settings=settings, pipeline_demo_stub=True),
        session_factory=sessions,
        writer=ctx.writer,
        security_stage=security,
        validation_stage=ValidatorAgent(Engine(), sessions, settings=settings),
    )
    assert (
        await orchestrator._post_generation(ctx, Variant.SECURITY, package)
        == PackageStatus.PRODUCTION_READY
    )
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    assert (row.validation_report.get("remediation") is None) == (
        provider == LLMProvider.STUB
    )
    assert scanner.calls == (1 if provider == LLMProvider.STUB else 2)
