import json
import logging
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr

from app.agents.factory import AgentFactory
from app.core.config import Settings
from app.domain.enums import LLMProvider
from app.llm.errors import LLMPermanentError
from app.llm.stub import StubAdapter
from scripts import eval_architect
from scripts.eval_architect import (
    CASES,
    _checks,
    _plan,
    _service,
    _storage,
    run_evaluation,
)


def settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://app:secret@localhost/db",
        migration_database_url="postgresql+asyncpg://owner:secret@localhost/db",
        test_database_url="postgresql+asyncpg://app:secret@localhost/test",
        test_migration_database_url="postgresql+asyncpg://owner:secret@localhost/test",
        llm_provider=LLMProvider.STUB,
        _env_file=None,
    )


@pytest.mark.req("FR-A-01", "FR-A-02")
@pytest.mark.parametrize(
    ("case", "check", "service_aws", "storage_aws", "storage_kind"),
    [
        (
            "three_tier",
            "relational database",
            "RDS PostgreSQL",
            "PostgreSQL",
            "relational_db",
        ),
        ("three_tier", "object storage", "s3", "Object store", "object_storage"),
        ("static_site", "CDN service", "cLoUdFrOnT", "cLoUdFrOnT", "other"),
        ("data_pipeline", "queue service", "sQs", "sQs", "other"),
    ],
)
def test_soft_checks_accept_service_and_storage_placements(
    case: str,
    check: str,
    service_aws: str,
    storage_aws: str,
    storage_kind: str,
) -> None:
    service_plan = _plan(
        [_service("web", "ECS", "Serve"), _service("resource", service_aws, "Use")],
        [],
        ["web"],
        ["resource"],
        [],
        ["terraform"],
    )
    storage_plan = _plan(
        [_service("web", "ECS", "Serve")],
        [],
        ["web"],
        [],
        [_storage("resource", storage_kind, storage_aws, ["web"])],
        ["terraform"],
    )
    for raw_plan in (service_plan, storage_plan):
        plan = eval_architect.DeploymentPlan.model_validate(raw_plan)
        assert _checks(case, plan)[check]
    missing_plan = eval_architect.DeploymentPlan.model_validate(
        _plan([_service("web", "ECS", "Serve")], [], ["web"], [], [], ["terraform"])
    )
    assert not _checks(case, missing_plan)[check]


@pytest.mark.req("FR-A-01", "FR-A-02")
def test_relational_database_accepts_aurora_service_and_kind_without_rds() -> None:
    aurora = eval_architect.DeploymentPlan.model_validate(
        _plan(
            [_service("web", "ECS", "Serve"), _service("db", "aUrOrA", "Store")],
            [],
            ["web"],
            ["db"],
            [],
            ["terraform"],
        )
    )
    storage = eval_architect.DeploymentPlan.model_validate(
        _plan(
            [_service("web", "ECS", "Serve")],
            [],
            ["web"],
            [],
            [_storage("db", "relational_db", "PostgreSQL", ["web"])],
            ["terraform"],
        )
    )
    misclassified_storage = eval_architect.DeploymentPlan.model_validate(
        _plan(
            [_service("web", "ECS", "Serve")],
            [],
            ["web"],
            [],
            [_storage("db", "other", "RDS PostgreSQL", ["web"])],
            ["terraform"],
        )
    )
    assert _checks("three_tier", aurora)["relational database"]
    assert _checks("three_tier", storage)["relational database"]
    assert not _checks("three_tier", misclassified_storage)["relational database"]
    assert not _checks("three_tier", None)["relational database"]


@pytest.mark.req("FR-A-01", "FR-A-02", "FR-A-03")
async def test_offline_evaluation_passes_all_checks_and_correction(
    tmp_path: Path,
) -> None:
    output = await run_evaluation(
        settings(), provider=LLMProvider.STUB, output_root=tmp_path
    )
    summary = (output / "summary.md").read_text(encoding="utf-8")
    assert "FAIL" not in summary
    assert "correction diagnostic" in summary
    assert "Plan attempts: 2" in summary
    expected_error = "dependencies.0.target: unknown service 'unknown-service'"
    assert expected_error in summary
    diagnostic = json.loads(
        (output / "correction_diagnostic.json").read_text(encoding="utf-8")
    )
    assert diagnostic["validation_errors_by_attempt"] == [
        {"attempt": 1, "errors": [expected_error]}
    ]
    assert diagnostic["plan"]["cloud_provider"] == "aws"
    three_tier = json.loads((output / "three_tier.json").read_text(encoding="utf-8"))
    assert three_tier["checks"]["relational database"]
    assert "RDS service" not in three_tier["checks"]
    assert len(list(output.glob("*.json"))) == len(CASES) + 1
    assert "user_description" not in summary


@pytest.mark.req("FR-A-04")
async def test_llm_failure_category_is_reported_without_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(eval_architect, "CASES", CASES[:1])

    def failed_agent(*args: object) -> object:
        agent = AgentFactory(settings()).create_architect()
        assert isinstance(agent.llm_adapter, StubAdapter)
        agent.llm_adapter.load_script([LLMPermanentError("request")])
        return agent

    monkeypatch.setattr(eval_architect, "_agent", failed_agent)
    output = await run_evaluation(
        settings(), provider=LLMProvider.OPENAI, output_root=tmp_path
    )
    report = json.loads((output / "three_tier.json").read_text(encoding="utf-8"))
    summary = (output / "summary.md").read_text(encoding="utf-8")
    assert report["plan"] is None
    assert report["error_category"] == "llm_failure"
    assert report["llm_category"] == "request"
    assert "LLM category: `request`" in summary


@pytest.mark.req("FR-A-04", "NFR-01")
async def test_redacting_info_logger_emits_attempt_metrics_to_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = logging.getLogger()
    prior_handlers = root.handlers[:]
    prior_level = root.level
    for handler in prior_handlers:
        root.removeHandler(handler)
    try:
        canary = "sk-test-CANARY-ARCHITECT-EVAL"
        eval_architect.configure_logging(
            settings().model_copy(
                update={"log_level": "INFO", "llm_api_key": SecretStr(canary)}
            )
        )
        logging.getLogger("eval-canary").info("key=%s", canary)
        await run_evaluation(
            settings(), provider=LLMProvider.STUB, output_root=tmp_path
        )
        stderr = capsys.readouterr().err
        assert "provider=stub model=stub attempt=1 outcome=success" in stderr
        assert "latency=" in stderr and "input_tokens=" in stderr
        assert "<user_description>" not in stderr
        assert '"cloud_provider"' not in stderr
        assert canary not in stderr
        assert "[REDACTED]" in stderr
    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        for handler in prior_handlers:
            root.addHandler(handler)
        root.setLevel(prior_level)


@pytest.mark.req("FR-A-04", "NFR-01")
def test_cli_configures_info_logging_before_evaluation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: list[str] = []

    async def fake_evaluation(*args: object, **kwargs: object) -> Path:
        assert seen == ["INFO"]
        return tmp_path

    def fake_logging(config: Settings) -> None:
        seen.append(config.log_level)

    monkeypatch.setattr(sys, "argv", ["eval_architect.py", "--provider", "stub"])
    monkeypatch.setattr(eval_architect, "get_settings", settings)
    monkeypatch.setattr(eval_architect, "configure_logging", fake_logging)
    monkeypatch.setattr(eval_architect, "run_evaluation", fake_evaluation)
    eval_architect.main()
    assert seen == ["INFO"]
