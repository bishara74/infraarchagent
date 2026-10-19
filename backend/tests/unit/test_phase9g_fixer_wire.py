"""FR-S-02/09: the same strict patch transport for all models and repair paths."""

import json

import httpx2
import pytest

from app.agents.security.fix import FixAgent
from app.agents.security.fix_schema import validate_output, wire_schema
from app.llm.base import RetryPolicy
from app.llm.openai import OpenAIAdapter
from tests.unit.test_llm_providers import success_body
from tests.unit.test_security_fix import PLAN


@pytest.mark.req("FR-S-02", "FR-S-09", "NFR-01")
@pytest.mark.parametrize(
    "model", ["openai/gpt-oss-scripted", "anthropic/claude-haiku-scripted"]
)
@pytest.mark.parametrize("mode", ["json_schema", "json_object", "off"])
@pytest.mark.parametrize(
    "kind", ["security_fixer", "validation_repair", "syntax_repair"]
)
async def test_shared_patch_wire_format(model, mode, kind):
    requests = []
    patch = {
        "file": {"path": "terraform/main.tf", "content": "terraform {}\n"},
        "edits": [] if mode == "json_schema" else {},
        "new_files": [] if mode == "json_schema" else {},
        "fixes": [],
    }

    def handler(request):
        requests.append(json.loads(request.content))
        body = success_body("openai")
        body["choices"][0]["message"]["content"] = json.dumps(patch)
        return httpx2.Response(200, json=body)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        adapter = OpenAIAdapter(
            model,
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
        agent = FixAgent(adapter, structured_output=mode)
        result = await agent.propose(
            path="terraform/main.tf",
            files={"terraform/main.tf": "terraform {}\n"},
            findings=[],
            plan=PLAN,
            directive="Fix requested issues",
            remaining=20,
            syntax_only=kind == "syntax_repair",
            validation_failures=[{"check_id": "synthetic"}]
            if kind == "validation_repair"
            else [],
        )
    assert result.accepted and result.call_kind == kind
    assert (
        len(result.attempt_details) == 1
        and result.attempt_details[0].outcome == "success"
    )
    body = requests[0]
    if mode == "json_schema":
        assert body["response_format"] == {
            "type": "json_schema",
            "json_schema": {
                "name": "fix_patch",
                "strict": True,
                "schema": wire_schema(),
            },
        }
        assert body["provider"] == {"require_parameters": True}
    elif mode == "json_object":
        assert body["response_format"] == {"type": "json_object"}
    else:
        assert "response_format" not in body


@pytest.mark.req("FR-S-02", "NFR-01")
@pytest.mark.parametrize("response_kind", ["prose", "malformed", "unsupported"])
async def test_generator_equivalent_salvage_errors_and_no_silent_downgrade(
    response_kind,
):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        if response_kind == "unsupported":
            return httpx2.Response(400, json={"error": {"message": "UNTRUSTED-CANARY"}})
        patch = {
            "file": {"path": "terraform/main.tf", "content": "terraform {}\n"},
            "edits": [],
            "new_files": [],
            "fixes": [],
        }
        body = success_body("openai")
        body["choices"][0]["message"]["content"] = (
            "Explanation: " + json.dumps(patch)
            if response_kind == "prose"
            else "UNTRUSTED-CANARY"
        )
        return httpx2.Response(200, json=body)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        agent = FixAgent(
            OpenAIAdapter(
                "anthropic/haiku-scripted",
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
        )
        result = await agent.propose(
            path="terraform/main.tf",
            files={"terraform/main.tf": "terraform {}\n"},
            findings=[],
            plan=PLAN,
            directive="Fix requested issues",
            remaining=20,
        )
    assert result.accepted is (response_kind == "prose")
    assert "UNTRUSTED-CANARY" not in str(result)
    assert all(r["response_format"]["type"] == "json_schema" for r in requests)
    assert len(result.attempt_details) == 1
    if response_kind == "prose":
        assert result.attempt_details[0].format_reason == "salvaged"


@pytest.mark.req("FR-S-02", "NFR-01")
def test_strict_patch_rejects_duplicate_paths_and_normalizes_maps():
    patch = {
        "file": {"path": "a", "content": "a"},
        "edits": [{"path": "b", "content": "b"}],
        "new_files": [],
        "fixes": [],
    }
    assert validate_output(patch, wire_files=True)["edits"] == {"b": "b"}
    patch["edits"] *= 2
    with pytest.raises(ValueError, match="duplicate"):
        validate_output(patch, wire_files=True)


@pytest.mark.req("FR-S-02", "FR-S-09", "NFR-01")
async def test_patch_schema_retry_retains_mode_and_normalizes_supporting_paths():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        patch = {
            "file": {"path": "terraform/main.tf", "content": "terraform {}\n"},
            "edits": [],
            "new_files": [{"path": "terraform/extra.tf", "content": "terraform {}\n"}],
            "fixes": [{"rule_id": "R", "resource": "r", "summary": "s"}],
        }
        if len(requests) == 1:
            patch["fixes"][0]["UNTRUSTED"] = "rejected extra field"
        body = success_body("openai")
        body["choices"][0]["message"]["content"] = json.dumps(patch)
        return httpx2.Response(200, json=body)

    async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as client:
        agent = FixAgent(
            OpenAIAdapter(
                "mock-family",
                RetryPolicy(30, 2, 60, 0, 4000),
                "canary-placeholder",
                http_client=client,
                base_url="https://openrouter.ai/api/v1",
            )
        )
        result = await agent.propose(
            path="terraform/main.tf",
            files={"terraform/main.tf": "terraform {}\n"},
            findings=[],
            plan=PLAN,
            directive="Fix issues",
            remaining=20,
        )
    assert result.accepted
    assert result.new_files == {"terraform/extra.tf": "terraform {}\n"}
    assert result.summaries == ("s",)
    assert [a.outcome for a in result.attempt_details] == ["invalid_json", "success"]
    assert result.attempt_details[0].format_reason == "schema_invalid"
    assert all(r["response_format"]["json_schema"]["strict"] for r in requests)
    assert all(r["provider"] == {"require_parameters": True} for r in requests)


@pytest.mark.req("PR-01", "NFR-01")
def test_fixer_telemetry_covers_paths_and_preserves_unknown_history():
    from scripts.phase9g_metrics import compact_evidence, fixer_evidence

    attempt = {"attempt": 1, "outcome": "invalid_json", "format_reason": "prose_before"}
    package = {
        "security_report": {
            "iterations": [{"fixes": [{"attempt_details": [attempt]}]}]
        },
        "validation_report": {
            "remediation": {
                "rounds": [{"attempted": True, "fixer_attempts": [attempt]}],
                "generation_syntax": {
                    "rounds": [{"actions": [{"attempt_details": [attempt]}]}]
                },
            }
        },
    }
    value = fixer_evidence(package)
    assert value["attempt_count"] == 3
    assert value["format_reasons"] == {"prose_before": 3}
    assert {a["call_kind"] for a in value["attempt_details"]} == {
        "security_fixer",
        "validation_repair",
        "syntax_repair",
    }
    assert compact_evidence(value) == value
    package["security_report"]["iterations"][0]["fixes"].append({})
    value = fixer_evidence(package)
    assert value["attempt_count"] is None
    assert value["unmeasured_calls_or_rounds"] == 1
    assert len(value["attempt_details"]) == 3
    assert fixer_evidence({})["attempt_count"] is None
