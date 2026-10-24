"""Anonymous OpenRouter metadata and immutable local snapshots; no settings/keys."""

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.domain.model_catalogue import catalogue_id

PUBLIC_BASE = "https://openrouter.ai/api/v1"
SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / ".cache/openrouter/catalogue.json"
MODEL_FIELDS = {
    "id",
    "name",
    "created",
    "canonical_slug",
    "context_length",
    "pricing",
    "supported_parameters",
    "deprecated",
    "expiration_date",
}
ENDPOINT_FIELDS = {
    "provider_name",
    "tag",
    "name",
    "status",
    "supported_parameters",
    "pricing",
    "context_length",
    "max_completion_tokens",
    "max_prompt_tokens",
    "uptime_last_5m",
    "uptime_last_30m",
    "uptime_last_1d",
}


class CatalogueError(ValueError):
    """Fixed operator guidance, never raw provider responses."""


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def model_id(value: str) -> str:
    value = catalogue_id("openrouter", value)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.:-]+", value):
        raise CatalogueError("Invalid metadata model identifier.")
    return value


async def public_get(
    path: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> dict[str, Any]:
    """A fresh client per GET prevents cookies, netrc, proxies and auth inheritance."""
    if path != "/models" and not re.fullmatch(
        r"/models/[A-Za-z0-9_.-]+/[A-Za-z0-9_.:-]+/endpoints", path
    ):
        raise CatalogueError("Unsupported public metadata endpoint.")
    try:
        async with httpx.AsyncClient(
            trust_env=False, follow_redirects=False, timeout=15, transport=transport
        ) as client:
            response = await client.get(PUBLIC_BASE + path)
            if response.status_code != 200:
                raise CatalogueError(
                    "Public metadata unavailable; no authenticated retry attempted."
                )
            body = response.json()
            if not isinstance(body, dict):
                raise ValueError
            return body
    except (httpx.HTTPError, ValueError, TypeError):
        raise CatalogueError(
            "Public metadata unavailable or malformed; no authenticated retry."
        ) from None


async def public_endpoints(
    model: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> list[dict[str, Any]]:
    body = await public_get(
        "/models/" + model_id(model) + "/endpoints", transport=transport
    )
    data = body.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("endpoints"), list):
        raise CatalogueError("Public model endpoint metadata is malformed.")
    return [
        {k: v for k, v in item.items() if k in ENDPOINT_FIELDS}
        for item in data["endpoints"]
        if isinstance(item, dict)
    ]


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, Any]:
    try:
        if any(
            part.startswith(".env") for part in (*path.parts, *path.resolve().parts)
        ):
            raise ValueError
        snapshot = json.loads(path.read_text())
        payload = snapshot["payload"]
        captured = datetime.fromisoformat(snapshot["captured_at"])
        if (
            snapshot["version"] != 1
            or snapshot["source"] != PUBLIC_BASE
            or captured.utcoffset() is None
            or snapshot["sha256"] != digest(payload)
            or not isinstance(payload["models"], list)
            or not isinstance(payload["endpoints"], dict)
        ):
            raise ValueError
        return dict(snapshot)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        raise CatalogueError(
            "Snapshot missing or invalid; run make catalogue-snapshot."
        ) from None


def provenance(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {key: snapshot[key] for key in ("source", "captured_at", "sha256")}


def snapshot_model(snapshot: dict[str, Any], model: str) -> dict[str, Any]:
    matches = [
        m
        for m in snapshot["payload"]["models"]
        if isinstance(m, dict) and m.get("id") == model_id(model)
    ]
    if len(matches) != 1:
        raise CatalogueError("Model absent or ambiguous; run make catalogue-snapshot.")
    return dict(matches[0])


def endpoints_for(snapshot: dict[str, Any], model: str) -> list[dict[str, Any]]:
    snapshot_model(snapshot, model)
    endpoints = snapshot["payload"]["endpoints"].get(model_id(model))
    if (
        not isinstance(endpoints, list)
        or not endpoints
        or any(not isinstance(e, dict) for e in endpoints)
    ):
        raise CatalogueError(
            "Model endpoint evidence missing; run make catalogue-snapshot."
        )
    return endpoints


def provider_key(value: str) -> str:
    return re.sub(r"[\s_-]", "", value).casefold()


def preferred_endpoints(
    endpoints: list[dict[str, Any]], preference: str
) -> list[dict[str, Any]]:
    return [
        e
        for e in endpoints
        if any(
            isinstance(e.get(k), str) and provider_key(e[k]) == provider_key(preference)
            for k in ("provider_name", "tag")
        )
    ]


def provider_order(
    snapshot: dict[str, Any], model: str, preference: str
) -> tuple[str, ...]:
    matches = preferred_endpoints(endpoints_for(snapshot, model), preference)
    if not preference.strip() or not matches:
        raise CatalogueError(
            "Configured provider does not serve this role's model in the snapshot."
        )
    # OpenRouter accepts provider names; prefer its supplied routing tag when present.
    tag = matches[0].get("tag") or matches[0].get("provider_name")
    if not isinstance(tag, str) or not tag:
        raise CatalogueError("Preferred provider lacks a routing identifier.")
    return (tag,)


async def provider_health(
    model: str, preference: str, *, transport: httpx.AsyncBaseTransport | None = None
) -> dict[str, Any]:
    try:
        matches = preferred_endpoints(
            await public_endpoints(model, transport=transport), preference
        )
        healthy = any(
            type(e.get("status")) is int and e["status"] == 0 for e in matches
        )
        return {
            "model": model,
            "preferred_provider": preference,
            "status": "ok" if healthy else "unavailable_or_degraded",
            "endpoints": matches,
            "checked_at": datetime.now(UTC).isoformat(),
        }
    except CatalogueError:
        return {
            "model": model,
            "preferred_provider": preference,
            "status": "unknown",
            "endpoints": [],
            "checked_at": datetime.now(UTC).isoformat(),
        }


def provider_aliases(snapshot: dict[str, Any]) -> dict[str, str]:
    """Compare serving display names with routing tags using captured evidence."""
    return {
        provider_key(e["tag"]): provider_key(e["provider_name"])
        for endpoints in snapshot["payload"]["endpoints"].values()
        for e in endpoints
        if isinstance(e.get("tag"), str) and isinstance(e.get("provider_name"), str)
    }
