"""Measure LLM package-generation latency without retaining generated content."""

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.llm.base import LLMAdapter, RetryPolicy
from app.llm.errors import LLMError, LLMRetryExhausted, ResponseStats
from app.llm.factory import build_adapter

ROOT = Path(__file__).resolve().parents[2]
GROUPS = (
    "Terraform",
    "Kubernetes",
    "Helm",
    "Dockerfile",
    "Nginx",
    "Jenkinsfile",
    "Ansible",
    "Prometheus",
    "Grafana",
)
DEPLOYMENT = (
    "Three-tier AWS web app: public ALB; two independently deployable app "
    "services in private subnets; RDS PostgreSQL in isolated subnets; S3 "
    "for assets; CloudWatch logs and alarms. Include networking, IAM, "
    "secrets references, deployment configuration, and monitoring."
)
STOP_REASONS = {"end_turn", "stop", "max_tokens", "tool_use"}


def prompt_for(groups: tuple[str, ...]) -> str:
    return (
        f"Deployment plan: {DEPLOYMENT}\n"
        f"Generate these file groups: {', '.join(groups)}. "
        'Return only a strict JSON object: {"files": {"relative/path": "content"}}. '
        "Include complete file contents for every requested group."
    )


def call_record(
    *,
    group: str,
    latency: float,
    stats: ResponseStats | None,
    parsed: bool,
    data: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    files = data.get("files") if data else None
    file_map = files if isinstance(files, dict) else {}
    safe_reason = stats.stop_reason if stats else None
    if safe_reason not in STOP_REASONS:
        safe_reason = "other" if safe_reason else None
    return {
        "group": group,
        "latency_seconds": round(latency, 6),
        "input_tokens": stats.input_tokens if stats else None,
        "output_tokens": stats.output_tokens if stats else None,
        "stop_reason": safe_reason,
        "json_parsed": parsed,
        "truncated": safe_reason == "max_tokens" or error == "truncated",
        "file_count": len(file_map),
        "total_characters": sum(
            len(content) for content in file_map.values() if isinstance(content, str)
        ),
        "response_characters": stats.response_characters if stats else 0,
        "error_category": error,
    }


async def measure_call(
    adapter: LLMAdapter, group: str, groups: tuple[str, ...]
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        result = await adapter.complete_json(prompt_for(groups))
    except LLMError as error:
        category = (
            error.last_category
            if isinstance(error, LLMRetryExhausted)
            else type(error).__name__
        )
        stats = error.stats if isinstance(error, LLMRetryExhausted) else None
        return call_record(
            group=group,
            latency=time.monotonic() - started,
            stats=stats,
            parsed=False,
            error=category,
        )
    return call_record(
        group=group,
        latency=time.monotonic() - started,
        stats=result.response.stats(),
        parsed=True,
        data=result.data,
    )


def summarize(results: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    selected = [result for result in results if result["mode"] == mode]
    wall_times = [result["wall_seconds"] for result in selected]
    calls = [call for result in selected for call in result["calls"]]
    parsed = sum(bool(call["json_parsed"]) for call in calls)
    truncated = sum(bool(call["truncated"]) for call in calls)
    tokens = sum(call["output_tokens"] or 0 for call in calls)
    wall_total = sum(wall_times)
    fits = max(wall_times) <= 30 and parsed == len(calls) and truncated == 0
    return {
        "mode": mode,
        "runs": len(selected),
        "median_seconds": statistics.median(wall_times),
        "max_seconds": max(wall_times),
        "tokens_per_second": tokens / wall_total if wall_total else 0.0,
        "parsed": parsed,
        "calls": len(calls),
        "truncated": truncated,
        "fits": fits,
    }


def markdown_summary(metadata: dict[str, Any]) -> str:
    rows = [
        "# Phase 1 LLM timing spike",
        "",
        f"Provider: `{metadata['provider']}`; "
        f"max output tokens: {metadata['max_output_tokens']}.",
        "",
        "| Mode | Runs | Median wall s | Max wall s | Output tokens/s | "
        "Parsed calls | Truncated calls |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in metadata["summaries"]:
        rows.append(
            f"| {summary['mode']} | {summary['runs']} | "
            f"{summary['median_seconds']:.3f} | {summary['max_seconds']:.3f} | "
            f"{summary['tokens_per_second']:.2f} | "
            f"{summary['parsed']}/{summary['calls']} | "
            f"**{summary['truncated']}/{summary['calls']}** |"
        )
    rows.append("")
    for summary in metadata["summaries"]:
        verdict = "fits 30 s" if summary["fits"] else "does not fit 30 s"
        rows.append(
            f"- {summary['mode']}: **{verdict}**; "
            f"truncated {summary['truncated']}/{summary['calls']} calls; "
            f"parsed {summary['parsed']}/{summary['calls']}; "
            f"max wall {summary['max_seconds']:.3f} s."
        )
    return "\n".join(rows) + "\n"


async def run_spike(
    settings: Settings,
    *,
    provider: str | None = None,
    model: str | None = None,
    runs: int = 3,
    mode: str = "both",
    max_output_tokens: int | None = None,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    if runs < 1 or mode not in {"full", "split", "both"}:
        raise ValueError("runs must be positive and mode must be full, split, or both")
    tokens = (
        settings.llm_max_output_tokens
        if max_output_tokens is None
        else max_output_tokens
    )
    if tokens < 1:
        raise ValueError("max output tokens must be positive")
    policy = replace(
        RetryPolicy.from_settings(settings),
        attempt_timeout=240,
        max_attempts=1,
        deadline=240,
        max_output_tokens=tokens,
    )
    adapter = build_adapter(settings, provider=provider, model=model, policy=policy)
    results: list[dict[str, Any]] = []
    try:
        for run in range(1, runs + 1):
            if mode in {"full", "both"}:
                started = time.monotonic()
                calls = [await measure_call(adapter, "all", GROUPS)]
                results.append(
                    {
                        "mode": "full",
                        "run": run,
                        "wall_seconds": time.monotonic() - started,
                        "calls": calls,
                    }
                )
            if mode in {"split", "both"}:
                started = time.monotonic()
                calls = await asyncio.gather(
                    *(measure_call(adapter, group, (group,)) for group in GROUPS)
                )
                results.append(
                    {
                        "mode": "split",
                        "run": run,
                        "wall_seconds": time.monotonic() - started,
                        "calls": calls,
                    }
                )
    finally:
        client = getattr(adapter, "client", None)
        if client is not None:
            await client.close()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = output_dir or ROOT / "docs" / "spikes"
    destination.mkdir(parents=True, exist_ok=True)
    stem = f"phase1-llm-timing-{adapter.provider}-{timestamp}"
    json_path = destination / f"{stem}.json"
    md_path = destination / f"{stem}.md"
    active_modes = [
        candidate for candidate in ("full", "split") if mode in (candidate, "both")
    ]
    metadata = {
        "provider": adapter.provider,
        "model": adapter.model,
        "timestamp_utc": timestamp,
        "max_output_tokens": tokens,
        "runs": results,
        "summaries": [summarize(results, candidate) for candidate in active_modes],
    }
    json_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown_summary(metadata), encoding="utf-8")
    return json_path, md_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("anthropic", "openai", "stub"))
    parser.add_argument("--model")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--mode", choices=("full", "split", "both"), default="both")
    parser.add_argument("--max-output-tokens", type=int)
    args = parser.parse_args()
    paths = asyncio.run(
        run_spike(
            get_settings(),
            provider=args.provider,
            model=args.model,
            runs=args.runs,
            mode=args.mode,
            max_output_tokens=args.max_output_tokens,
        )
    )
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
