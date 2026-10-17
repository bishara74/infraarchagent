"""FR-S-02/04: configured OpenRouter model through mocked HTTP and persisted loop."""

import json

import httpx2
import pytest
from pydantic import SecretStr

from app.agents.factory import AgentFactory
from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import LLMProvider, PackageStatus, Variant
from app.domain.models import IaCPackage
from app.domain.run_config import RunConfig
from app.llm.openai import OpenAIAdapter
from app.scanners.scan import ScanResult
from tests.integration.test_security_agent import setup
from tests.unit.test_llm_providers import success_body
from tests.unit.test_security_focus_recovery import FILES, finding, raw


@pytest.mark.req("FR-S-02", "FR-S-04", "FR-S-09", "NFR-01", "PR-05")
@pytest.mark.parametrize(
    "model,reasoning",
    [
        ("openai/gpt-oss-120b:nitro", "low"),
        ("anthropic/claude-haiku-scripted", "off"),
    ],
)
async def test_fixer_model_switch_reaches_http_guards_and_report(
    db_engines, model, reasoning
):
    engine, _ = db_engines
    ctx, _ = await setup(engine)
    sessions = make_session_factory(engine)
    async with sessions() as session:
        async with session.begin():
            await PackageRepository(session).save_files(
                ctx.run_id, Variant.SECURITY, FILES
            )
    requests = []

    def handler(request):
        requests.append(request)
        body = success_body("openai")
        body["model"] = model
        body["choices"][0]["message"]["content"] = json.dumps(raw())
        return httpx2.Response(200, json=body)

    class Scanner:
        async def scan(self, source, variant, **kwargs):
            return ScanResult(
                []
                if "default = true" in source["terraform/variables.tf"]
                else [finding("original.target")],
                {},
            )

    class Verifier:
        async def checks(self, source):
            return []

    settings = get_settings().model_copy(
        update={
            "llm_provider": LLMProvider.OPENAI,
            "llm_model": "architect-generator",
            "llm_api_key": SecretStr("canary-placeholder"),
            "security_fix_model": model,
            "security_fix_reasoning_effort": reasoning,
            "llm_response_format": "json_object",
            "fix_attempt_timeout_seconds": 45.0,
        }
    )
    security = AgentFactory(
        settings, session_factory=sessions, scanner=Scanner()
    ).create_security_agent(
        RunConfig(provider=LLMProvider.OPENAI, model="architect-generator")
    )
    security.terraform_verifier = Verifier()
    adapter = security.fix_agent.adapter
    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter.client = OpenAIAdapter(
            model,
            adapter.policy,
            "canary-placeholder",
            http_client=client,
            base_url="https://openrouter.ai/api/v1",
        ).client
        status = await security.run(
            ctx, Variant.SECURITY, IaCPackage(variant=Variant.SECURITY, files=FILES)
        )
        clipped = await security.fix_agent.propose(
            path="terraform/main.tf",
            files=FILES,
            findings=[finding("original.target")],
            plan=ctx.plan,
            directive="secure",
            remaining=20,
        )
        assert clipped.accepted
        assert 0 < requests[-1].extensions["timeout"]["read"] <= 20
    assert status == PackageStatus.SCAN_CLEAN
    payload = json.loads(requests[0].content)
    assert payload["model"] == model
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["reasoning"] == (
        {"effort": "low"} if reasoning == "low" else {"enabled": False}
    )
    assert 0 < requests[0].extensions["timeout"]["read"] <= 45
    async with sessions() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    report = row.security_report["sessions"][0]
    assert (
        report["fixing_model"] == model
        and report["fixing_reasoning_effort"] == reasoning
    )
    assert report["fix_attempt_timeout_seconds"] == 45
    assert report["iteration_timeout_seconds"] == 60
    assert report["security_stage_timeout_seconds"] == 240
    assert report["iterations"][0]["fixes"][0]["recovered_existing_proposal"]
    assert "canary-placeholder" not in json.dumps(row.security_report)
