"""FR-S-02, FR-A-05: frozen version-8 Fixer request bytes across repair modes."""

import json
from pathlib import Path

import httpx2
import pytest

from app.agents.security.fix import FixAgent
from app.llm.base import RetryPolicy
from app.llm.openai import OpenAIAdapter
from tests.unit.test_llm_providers import success_body
from tests.unit.test_phase10b_conformance import plan

pytestmark = pytest.mark.req("FR-S-02", "FR-A-05", "NFR-01")
GOLDEN = Path(__file__).parents[1] / "fixtures/phase10b-fixer-wire.json"


async def capture(mode, kind, runtime=None, config=None):
    captured = []
    patch = {
        "file": {"path": "terraform/main.tf", "content": "terraform {}\n"},
        "edits": [] if mode == "json_schema" else {},
        "new_files": [] if mode == "json_schema" else {},
        "fixes": [],
    }

    def handler(request):
        captured.append(json.loads(request.content))
        body = success_body("openai")
        body["choices"][0]["message"]["content"] = json.dumps(patch)
        return httpx2.Response(200, json=body)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = OpenAIAdapter(
            "wire-model",
            RetryPolicy(
                attempt_timeout=30,
                max_attempts=1,
                deadline=60,
                backoff_base=0,
                max_output_tokens=4000,
            ),
            "canary-placeholder",
            http_client=client,
            base_url="https://openrouter.ai/api/v1",
        )
        if runtime:
            runtime.bind(adapter, config, "fixer")
        result = await FixAgent(adapter, structured_output=mode).propose(
            path="terraform/main.tf",
            files={"terraform/main.tf": "terraform {}\n"},
            findings=[],
            plan=plan(),
            directive="Preserve planned exposure",
            remaining=20,
            syntax_only=kind == "syntax_repair",
            validation_failures=[{"check_id": "synthetic"}]
            if kind == "validation_repair"
            else [],
        )
        assert result.accepted
    return json.dumps(
        captured[0], ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


@pytest.mark.parametrize("mode", ["json_schema", "json_object", "off"])
@pytest.mark.parametrize(
    "kind", ["security_fixer", "validation_repair", "syntax_repair"]
)
async def test_version_8_complete_wire_bytes(monkeypatch, mode, kind):
    monkeypatch.setattr("app.agents.prompts.security_fix.token_hex", lambda _: "0" * 32)
    golden = json.loads(GOLDEN.read_text())
    body = await capture(mode, kind)
    assert body == golden[mode + ":" + kind]
    decoded = json.loads(body)
    user = decoded["messages"][1]["content"]
    assert (
        json.dumps(
            plan().network.model_dump(mode="json"), ensure_ascii=True, sort_keys=True
        )
        in user
    )
    assert (
        "Leave conflicting findings open for engineer review"
        in decoded["messages"][0]["content"]
    )
    assert user.endswith('</fixer_advisory id="' + "0" * 32 + '">')
