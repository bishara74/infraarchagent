"""Author-run anonymous catalogue capture and offline experiment estimates.

Never imports operator settings or credential code. No inference endpoint exists here.
"""

import argparse
import asyncio
import hashlib
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.core.public_catalogue import (
    MODEL_FIELDS,
    PUBLIC_BASE,
    SNAPSHOT_PATH,
    CatalogueError,
    digest,
    endpoints_for,
    load_snapshot,
    model_id,
    preferred_endpoints,
    provenance,
    public_endpoints,
    public_get,
    snapshot_model,
)

ROOT = Path(__file__).resolve().parents[2]
BASELINE_FOLDERS = (
    "phase9-bench-broad-20261020T234203035108Z",
    "phase9-bench-broad-20261021T200436165739Z",
)


def pinned_sonnet(item: dict) -> bool:
    identity = item.get("id", "")
    return (
        isinstance(identity, str)
        and identity.startswith("anthropic/")
        and "sonnet" in identity.lower()
        and any(c.isdigit() for c in identity)
        and "~" not in identity
        and "latest" not in identity.lower()
        and ":" not in identity
        and item.get("deprecated") is not True
    )


def capability(endpoint: dict, parameter: str) -> bool:
    return parameter in (endpoint.get("supported_parameters") or [])


def eligible_endpoints(snapshot: dict, model: str, preference=None) -> list[dict]:
    endpoints = endpoints_for(snapshot, model)
    if preference:
        endpoints = preferred_endpoints(endpoints, preference)
    return [
        e
        for e in endpoints
        if capability(e, "structured_outputs") and capability(e, "reasoning")
    ]


def candidates(snapshot: dict) -> list[dict]:
    rows = []
    for item in snapshot["payload"]["models"]:
        if not pinned_sonnet(item):
            continue
        try:
            endpoints = endpoints_for(snapshot, item["id"])
        except CatalogueError:
            endpoints = []
        rows.append(
            {
                "id": item["id"],
                "created": item.get("created"),
                "context_length": item.get("context_length"),
                "pricing": item.get("pricing"),
                "json_schema_declared": any(
                    capability(e, "structured_outputs") for e in endpoints
                ),
                "reasoning_declared": any(
                    capability(e, "reasoning") for e in endpoints
                ),
                "eligible": any(
                    capability(e, "structured_outputs") and capability(e, "reasoning")
                    for e in endpoints
                ),
                "providers": [
                    {
                        k: e.get(k)
                        for k in (
                            "provider_name",
                            "tag",
                            "status",
                            "context_length",
                            "pricing",
                            "supported_parameters",
                        )
                    }
                    for e in endpoints
                ],
            }
        )
    return sorted(
        rows,
        key=lambda r: (-(r["created"] if type(r["created"]) is int else 0), r["id"]),
    )


def recommendation(snapshot: dict) -> str | None:
    return next((r["id"] for r in candidates(snapshot) if r["eligible"]), None)


def safe_model(item: dict) -> dict:
    clean = {k: item[k] for k in MODEL_FIELDS if k in item}
    clean["pricing"] = {
        k: v
        for k, v in (item.get("pricing") or {}).items()
        if k in {"prompt", "completion", "request"} and isinstance(v, (str, int, float))
    }
    return clean


async def capture(path: Path, extra_models: list[str], *, transport=None) -> dict:
    body = await public_get("/models", transport=transport)
    if not isinstance(body.get("data"), list):
        raise CatalogueError("Public models metadata is malformed.")
    models = [
        safe_model(m)
        for m in body["data"]
        if isinstance(m, dict) and isinstance(m.get("id"), str)
    ]
    wanted = {model_id(m) for m in extra_models}
    wanted.update(m["id"] for m in models if pinned_sonnet(m))
    available = {m["id"] for m in models}
    if wanted - available:
        raise CatalogueError(
            "Requested model missing from public catalogue; no snapshot replaced."
        )
    endpoints = {}
    for identity in sorted(wanted):
        endpoints[identity] = await public_endpoints(identity, transport=transport)
    payload = {"models": models, "endpoints": endpoints}
    snapshot = {
        "version": 1,
        "source": PUBLIC_BASE,
        "captured_at": datetime.now(UTC).isoformat(),
        "payload": payload,
        "sha256": digest(payload),
        "source_urls": [
            PUBLIC_BASE + "/models",
            *[PUBLIC_BASE + "/models/" + i + "/endpoints" for i in sorted(wanted)],
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(snapshot, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)
    return snapshot


def price(value) -> Decimal:
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0:
            raise ValueError
        return number
    except (InvalidOperation, ValueError, TypeError):
        raise CatalogueError(
            "Snapshot lacks usable pricing; recapture public metadata."
        ) from None


def charge(tokens: tuple[int, int], pricing: dict, calls=1) -> Decimal:
    return (
        tokens[0] * price(pricing.get("prompt"))
        + tokens[1] * price(pricing.get("completion"))
        + calls * price(pricing.get("request", "0"))
    )


def broad_usage(root: Path = ROOT) -> list[dict]:
    records = []
    for folder in BASELINE_FOLDERS:
        directory = root / "docs/evals" / folder
        raw = (directory / "results.json").read_bytes()
        data = json.loads(raw)
        environment = json.loads((directory / "environment.json").read_text())
        if environment.get("mode") != "real" or len(data["runs"]) != 20:
            raise CatalogueError("Baseline cost evidence is incomplete.")
        for row in data["runs"]:
            seen, calls = set(), []
            for call in row.get("telemetry", []):
                if call.get("kind") == "llm" and call.get("role") == "architect":
                    identity = call.get("call_id") or call.get("id")
                    if not identity or identity in seen:
                        continue
                    seen.add(identity)
                    if any(
                        type(call.get(k)) is not int or call[k] < 0
                        for k in ("input_tokens", "output_tokens")
                    ):
                        raise CatalogueError(
                            "Baseline Architect token usage is unknown."
                        )
                    calls.append(call)
            if not calls or not row.get("complete") or row.get("cost_usd") is None:
                raise CatalogueError("Baseline run cost or Architect usage is unknown.")
            records.append(
                {
                    "folder": folder,
                    "results_sha256": hashlib.sha256(raw).hexdigest(),
                    "run_id": row["run_id"],
                    "scenario_id": row["scenario_id"],
                    "cost_usd": price(row["cost_usd"]),
                    "calls": calls,
                }
            )
    return records


def estimate(
    snapshot: dict, architect_model: str, *, architect_provider=None, usage=None
) -> dict:
    """Token replay projection, not a quote or bound on a different model's usage."""
    if not architect_model:
        raise CatalogueError(
            "Explicit ARCHITECT_MODEL is required; recommendation is advisory."
        )
    if "~" in architect_model or "latest" in architect_model.lower():
        raise CatalogueError("Experiment requires an explicit pinned Architect model.")
    selected = snapshot_model(snapshot, architect_model)
    endpoints = eligible_endpoints(snapshot, architect_model)
    if not endpoints:
        raise CatalogueError(
            "Selected model lacks declared schema/reasoning endpoint support."
        )
    if architect_provider and not eligible_endpoints(
        snapshot, architect_model, architect_provider
    ):
        raise CatalogueError(
            "Architect provider lacks declared schema/reasoning support."
        )
    usages = broad_usage() if usage is None else usage
    if not usages:
        raise CatalogueError("Baseline usage evidence is empty.")
    # Expected catalogue price; conservative maximum across eligible fallback endpoints.
    expected_pricing = selected.get("pricing") or {}
    if architect_provider:
        expected_pricing = (
            eligible_endpoints(snapshot, architect_model, architect_provider)[0].get(
                "pricing"
            )
            or {}
        )
    by_scenario = defaultdict(list)
    projections = []
    for record in usages:
        tokens = tuple(
            sum(c[k] for c in record["calls"])
            for k in ("input_tokens", "output_tokens")
        )
        old = sum(
            (
                charge(
                    (c["input_tokens"], c["output_tokens"]),
                    snapshot_model(snapshot, c["model"]).get("pricing") or {},
                )
                for c in record["calls"]
            ),
            Decimal(0),
        )
        new = charge(tokens, expected_pricing, len(record["calls"]))
        upper = max(
            charge(tokens, e.get("pricing") or {}, len(record["calls"]))
            for e in endpoints
        )
        extra = new - old
        total = max(Decimal(0), record["cost_usd"] + extra)
        guard = max(Decimal(0), record["cost_usd"] + max(Decimal(0), upper - old))
        projection = {
            "scenario_id": record["scenario_id"],
            "architect_usd": new,
            "extra_usd": extra,
            "full_run_usd": total,
            "conservative_full_run_usd": guard,
            "input_tokens": tokens[0],
            "output_tokens": tokens[1],
        }
        projections.append(projection)
        by_scenario[record["scenario_id"]].append(projection)

    def mean(records, field):
        return sum((r[field] for r in records), Decimal(0)) / len(records)

    def totals(ids):
        return {
            field: float(sum((mean(by_scenario[i], field) for i in ids), Decimal(0)))
            for field in ("architect_usd", "extra_usd", "full_run_usd")
        }

    return {
        "explicit_architect_model": architect_model,
        "recommended_architect_model": recommendation(snapshot),
        "recommendation_advisory": True,
        "thinking_recommendation": "medium",
        "snapshot": provenance(snapshot),
        "baseline_runs": len(usages),
        "baseline_sources": sorted(
            {(r["folder"], r["results_sha256"]) for r in usages}
        ),
        "expected_pricing_per_token": expected_pricing,
        "per_run": {
            field: float(mean(projections, field))
            for field in ("architect_usd", "extra_usd", "full_run_usd")
        },
        "conservative_full_run_usd": float(
            max(r["conservative_full_run_usd"] for r in projections)
        ),
        "smoke_6_9_10": totals([6, 9, 10])
        if {6, 9, 10} <= by_scenario.keys()
        else None,
        "round_20": totals(list(range(1, 11)) * 2)
        if set(range(1, 11)) <= by_scenario.keys()
        else None,
        "mean_architect_input_tokens": float(mean(projections, "input_tokens")),
        "mean_architect_output_tokens": float(mean(projections, "output_tokens")),
        "assumption": (
            "Historical token replay including retries; reasoning is already in "
            "output usage. Different model/thinking can change usage, cost and "
            "latency. Conservative is a projection, not a spending bound."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["snapshot", "inspect", "estimate"])
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path(os.environ.get("OPENROUTER_CATALOGUE_SNAPSHOT") or SNAPSHOT_PATH),
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("PHASE9_CATALOGUE_MODELS") or "openai/gpt-oss-120b",
    )
    parser.add_argument("--architect-model", default=os.environ.get("ARCHITECT_MODEL"))
    parser.add_argument(
        "--architect-provider", default=os.environ.get("ARCHITECT_PROVIDER_PREFERENCE")
    )
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            if not args.snapshot.resolve().is_relative_to(
                (ROOT / ".cache/openrouter").resolve()
            ):
                raise CatalogueError(
                    "Snapshot destination must be under ignored .cache/openrouter/."
                )
            snapshot = asyncio.run(
                capture(args.snapshot, [s for s in args.models.split(",") if s])
            )
        else:
            snapshot = load_snapshot(args.snapshot)
        result = (
            estimate(
                snapshot,
                args.architect_model,
                architect_provider=args.architect_provider,
            )
            if args.command == "estimate"
            else {
                "snapshot": provenance(snapshot),
                "candidates": candidates(snapshot),
                "recommended_architect_model": recommendation(snapshot),
                "recommendation_advisory": True,
                "thinking_recommendation": "medium",
                "wire": (
                    "Architect retains JSON-object output with local validation; "
                    "reasoning.effort=medium. require_parameters is a router flag, "
                    "not a model capability. Strict-schema support is declared "
                    "metadata, not an inference test."
                ),
            }
        )
        print(json.dumps(result, indent=2))
    except (CatalogueError, OSError, ValueError, KeyError):
        raise SystemExit(
            "Catalogue/estimate unavailable; run make catalogue-snapshot and "
            "explicitly set ARCHITECT_MODEL. No inference or authenticated "
            "metadata retry was attempted."
        ) from None


if __name__ == "__main__":
    main()
