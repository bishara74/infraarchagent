"""Provider metadata normalization; never infer capabilities from model names."""

from typing import Any

import httpx

from app.core.credentials import CredentialMaterial

PRESETS = {
    "openrouter": ("https://openrouter.ai/api/v1", "chat_completions"),
    "openai": ("https://api.openai.com/v1", "chat_completions"),
    "anthropic": ("https://api.anthropic.com/v1", "messages"),
}


def normalize(item: dict[str, Any], provider: str) -> dict[str, Any]:
    supported = item.get("supported_parameters")
    declared = item.get("capabilities", {})
    if not isinstance(declared, dict):
        declared = {}
    if provider == "anthropic" and isinstance(declared.get("thinking"), dict):
        reasoning = declared["thinking"].get("supported")
        structured = (declared.get("structured_outputs") or {}).get("supported")
        effort = declared.get("effort") or {}
        modes = [
            m
            for m in ("low", "medium", "high")
            if (effort.get(m) or {}).get("supported")
        ]
        modes = ["off", *modes] if reasoning else []
    else:
        reasoning = (
            ("reasoning" in supported)
            if isinstance(supported, list)
            else declared.get("reasoning")
        )
        structured = (
            any(p in supported for p in ("structured_outputs", "response_format"))
            if isinstance(supported, list)
            else declared.get("structured_output")
        )
        modes = (
            declared.get("thinking_modes", ["off", "low", "medium", "high"])
            if reasoning is True
            else []
        )
    return {
        "id": str(item.get("id", ""))[:128],
        "name": str(item.get("name") or item.get("display_name") or item.get("id", ""))[
            :200
        ],
        "context_length": item.get("context_length", item.get("max_input_tokens")),
        "pricing": {
            k: v
            for k, v in (item.get("pricing") or {}).items()
            if k in {"prompt", "completion"} and isinstance(v, (str, int, float))
        },
        "structured_output": structured if isinstance(structured, bool) else None,
        "reasoning": reasoning if isinstance(reasoning, bool) else None,
        "thinking_modes": [m for m in modes if m in {"off", "low", "medium", "high"}],
        "source": "provider"
        if isinstance(supported, list)
        or (provider == "anthropic" and isinstance(declared.get("thinking"), dict))
        else "admin"
        if declared
        else "unknown",
        "thinking_types": (declared.get("thinking") or {}).get("types", {})
        if provider == "anthropic"
        else {},
    }


async def probe(
    material: CredentialMaterial, client: httpx.AsyncClient | None = None
) -> dict[str, Any]:
    headers = {"Authorization": "Bearer " + material.secret.get_secret_value()}
    if material.provider == "anthropic":
        headers = {
            "x-api-key": material.secret.get_secret_value(),
            "anthropic-version": "2023-06-01",
        }
    owned = client is None
    transport = client or httpx.AsyncClient(timeout=10, follow_redirects=False)
    try:
        response = await transport.get(
            material.base_url.rstrip("/") + "/models", headers=headers
        )
        if response.status_code in {401, 403}:
            return {"status": "invalid", "models": []}
        if response.status_code == 402:
            return {"status": "no_credit", "models": []}
        if response.status_code != 200:
            return {"status": "unavailable", "models": []}
        body = response.json()
        models = [
            normalize(item, material.provider)
            for item in body.get("data", [])
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        state = "ok"
        if material.provider == "openrouter":
            key = await transport.get(
                material.base_url.rstrip("/") + "/key", headers=headers
            )
            if key.status_code in {401, 403}:
                state = "invalid"
            elif key.status_code == 402:
                state = "no_credit"
            elif key.status_code == 200:
                data = key.json().get("data", {})
                balance = data.get("limit_remaining")
                if isinstance(balance, (int, float)) and balance <= 0:
                    state = "no_credit"
            credits = await transport.get(
                material.base_url.rstrip("/") + "/credits", headers=headers
            )
            if credits.status_code == 200:
                data = credits.json().get("data", {})
                data = data if isinstance(data, dict) else {}
                total, usage = data.get("total_credits"), data.get("total_usage")
                if (
                    isinstance(total, (int, float))
                    and isinstance(usage, (int, float))
                    and total - usage <= 0
                ):
                    state = "no_credit"
        return {"status": state, "models": models}
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        return {"status": "unavailable", "models": []}
    finally:
        if owned:
            await transport.aclose()
