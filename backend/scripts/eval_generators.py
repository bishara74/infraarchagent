"""Evaluate generator variants against fixed plans; never store prompts or keys."""

import argparse
import asyncio
import html
import json
import re
import statistics
import time
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.agents.factory import AgentFactory
from app.agents.generators.base import (
    GeneratorError,
    GeneratorIncompletePackage,
    GeneratorLLMFailure,
)
from app.core.config import Settings, get_settings
from app.core.logging import RedactingFilter, configure_logging
from app.domain.directive_checks import check_directive
from app.domain.enums import LLMProvider, Variant
from app.domain.models import IaCPackage
from app.domain.plan import DeploymentPlan
from app.domain.run_config import RunConfig
from app.llm.base import LLMResponse
from app.llm.stub import StubAdapter

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures/generators"
EVALS = ROOT / "docs/evals"
PLAN_NAMES = ("three_tier", "kubernetes_monitoring")


def _selected(raw: str | None, choices: tuple[str, ...]) -> list[str]:
    values = [item.strip() for item in raw.split(",")] if raw else list(choices)
    if not values or any(not value or value not in choices for value in values):
        raise ValueError(f"choices must be drawn from {', '.join(choices)}")
    return list(dict.fromkeys(values))


def _prices(raw: str | None) -> dict[str, float]:
    prices: dict[str, float] = {}
    if raw is None:
        return prices
    for entry in raw.split(","):
        model, separator, value = entry.partition("=")
        if not separator or not model.strip():
            raise ValueError("prices must use model=rate entries")
        rate = float(value)
        if not 0 <= rate < float("inf"):
            raise ValueError("prices must be finite and nonnegative")
        prices[model.strip()] = rate
    return prices


def _fixture_plan(name: str) -> DeploymentPlan:
    return DeploymentPlan.model_validate(
        json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    )


def _stub_package(name: str, variant: Variant) -> dict[str, Any]:
    packages = json.loads((FIXTURES / "packages.json").read_text(encoding="utf-8"))
    result = packages[name][variant.value]
    assert isinstance(result, dict)
    return result


def _stub_script(name: str, variant: Variant) -> list[LLMResponse]:
    complete = _stub_package(name, variant)
    replies = [complete]
    if name == "kubernetes_monitoring" and variant is Variant.COST:
        replies.insert(
            0,
            {
                "files": {"terraform/main.tf": complete["files"]["terraform/main.tf"]},
                "notes": "First attempt omitted planned file types.",
            },
        )
    return [
        LLMResponse(json.dumps(reply), input_tokens=1000, output_tokens=2000)
        for reply in replies
    ]


def _safe_model_folder(model: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("._-") or "model"
    return f"{stem[:60]}-{sha256(model.encode()).hexdigest()[:8]}"


def _save_package(
    output: Path, model: str, plan_name: str, package: IaCPackage
) -> None:
    folder = output / "packages" / _safe_model_folder(model) / plan_name
    folder = folder / package.variant.value
    for path, content in package.files.items():
        destination = folder / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


async def _run_variant(
    *,
    agent: Any,
    plan: DeploymentPlan,
    model: str,
    plan_name: str,
    output: Path,
    save_packages: bool,
    redactor: RedactingFilter,
) -> dict[str, Any]:
    package: IaCPackage | None = None
    error_category: str | None = None
    llm_category: str | None = None
    missing_types: list[str] = []
    try:
        package = await agent.generate(plan.model_copy(deep=True))
    except GeneratorError as error:
        error_category = error.category
        if isinstance(error, GeneratorLLMFailure):
            llm_category = error.llm_category
        if isinstance(error, GeneratorIncompletePackage):
            missing_types = [kind.value for kind in error.missing_types]
    info = agent.last_run
    if package is not None and save_packages:
        _save_package(output, model, plan_name, package)
    checks = (
        [
            {"name": check.name, "passed": check.passed, "detail": check.detail}
            for check in check_directive(agent.variant, package.files, plan)
        ]
        if package is not None
        else []
    )
    return {
        "model": model,
        "plan": plan_name,
        "variant": agent.variant.value,
        "success": package is not None,
        "error_category": error_category,
        "llm_category": llm_category,
        "missing_types": missing_types,
        "checks": checks,
        "notes": redactor.redact(info.notes) if info and info.notes else None,
        "package_attempts": info.package_attempts if info else None,
        "llm_attempts": info.total_llm_attempts if info else None,
        "elapsed_seconds": info.elapsed_seconds if info else None,
        "input_tokens": info.input_tokens if info else None,
        "output_tokens": info.output_tokens if info else None,
        "file_count": info.file_count if info else None,
        "total_characters": info.total_characters if info else None,
        "prompt_version": info.prompt_version if info else None,
        "structure_error_counts": list(info.structure_error_counts) if info else [],
    }


async def run_evaluation(
    settings: Settings,
    *,
    models: list[str] | None = None,
    plans: list[str] | None = None,
    mode: str = "parallel",
    pause_seconds: float = 0,
    save_packages: bool = False,
    price_in: dict[str, float] | None = None,
    price_out: dict[str, float] | None = None,
    output_root: Path = EVALS,
) -> Path:
    if mode not in {"parallel", "sequential"} or pause_seconds < 0:
        raise ValueError("invalid evaluation mode or pause")
    selected_models = models or [settings.llm_model or "stub"]
    selected_plans = plans or list(PLAN_NAMES)
    if any(name not in PLAN_NAMES for name in selected_plans):
        raise ValueError("unknown plan name")
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = output_root / f"phase3-generators-{timestamp}"
    output.mkdir(parents=True, exist_ok=False)
    redactor = RedactingFilter(
        settings.llm_api_key.get_secret_value() if settings.llm_api_key else None
    )
    cases: list[dict[str, Any]] = []
    triples: list[dict[str, Any]] = []
    for model in selected_models:
        provider = LLMProvider.STUB if model == "stub" else settings.llm_provider
        for index, name in enumerate(selected_plans):
            if index and pause_seconds:
                await asyncio.sleep(pause_seconds)
            plan = _fixture_plan(name)
            agents = AgentFactory(settings).create_generators(
                RunConfig(provider=provider, model=model)
            )
            if provider is LLMProvider.STUB:
                for agent in agents:
                    assert isinstance(agent.llm_adapter, StubAdapter)
                    agent.llm_adapter.load_script(_stub_script(name, agent.variant))
            started = time.monotonic()
            if mode == "parallel":
                results = await asyncio.gather(
                    *(
                        _run_variant(
                            agent=agent,
                            plan=plan,
                            model=model,
                            plan_name=name,
                            output=output,
                            save_packages=save_packages,
                            redactor=redactor,
                        )
                        for agent in agents
                    )
                )
            else:
                results = []
                for variant_index, agent in enumerate(agents):
                    if variant_index and pause_seconds:
                        await asyncio.sleep(pause_seconds)
                    results.append(
                        await _run_variant(
                            agent=agent,
                            plan=plan,
                            model=model,
                            plan_name=name,
                            output=output,
                            save_packages=save_packages,
                            redactor=redactor,
                        )
                    )
            triples.append(
                {
                    "model": model,
                    "plan": name,
                    "wall_seconds": time.monotonic() - started,
                    "mode": mode,
                }
            )
            cases.extend(results)
    totals = _totals(cases, selected_models, price_in or {}, price_out or {})
    data = {"cases": cases, "triples": triples, "totals": totals}
    (output / "results.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output / "summary.md").write_text(
        _summary(cases, triples, totals, selected_plans, selected_models),
        encoding="utf-8",
    )
    return output


def _totals(
    cases: list[dict[str, Any]],
    models: list[str],
    price_in: dict[str, float],
    price_out: dict[str, float],
) -> dict[str, dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    for model in models:
        rows = [row for row in cases if row["model"] == model]
        checks = [check for row in rows for check in row["checks"]]
        times = [
            row["elapsed_seconds"] for row in rows if row["elapsed_seconds"] is not None
        ]
        known_tokens = all(
            row["input_tokens"] is not None and row["output_tokens"] is not None
            for row in rows
        )
        input_tokens = sum(row["input_tokens"] or 0 for row in rows)
        output_tokens = sum(row["output_tokens"] or 0 for row in rows)
        cost = (
            (input_tokens * price_in[model] + output_tokens * price_out[model])
            / 1_000_000
            if known_tokens and model in price_in and model in price_out
            else None
        )
        totals[model] = {
            "success_rate": sum(bool(row["success"]) for row in rows) / len(rows),
            "compliance_rate": (
                sum(bool(check["passed"]) for check in checks) / len(checks)
                if checks
                else None
            ),
            "median_seconds": statistics.median(times) if times else None,
            "input_tokens": input_tokens if known_tokens else None,
            "output_tokens": output_tokens if known_tokens else None,
            "total_tokens": input_tokens + output_tokens if known_tokens else None,
            "estimated_cost": cost,
        }
    return totals


def _summary(
    cases: list[dict[str, Any]],
    triples: list[dict[str, Any]],
    totals: dict[str, dict[str, Any]],
    plans: list[str],
    models: list[str],
) -> str:
    lines = ["# Phase 3 GeneratorAgent evaluation", ""]
    for name in plans:
        lines.extend([f"## {name}", ""])
        model_headers = " | ".join(
            f"{model} outcome | {model} time/tokens" for model in models
        )
        lines.append(f"| Variant | {model_headers} |")
        lines.append("| --- | " + " | ".join("--- | ---" for _ in models) + " |")
        for variant in Variant:
            cells: list[str] = []
            for model in models:
                row = next(
                    row
                    for row in cases
                    if row["model"] == model
                    and row["plan"] == name
                    and row["variant"] == variant.value
                )
                outcome = "PASS" if row["success"] else f"FAIL {row['error_category']}"
                timing = (
                    f"{row['elapsed_seconds']:.3f}s / "
                    f"{row['input_tokens']}/{row['output_tokens']}"
                )
                cells.extend((outcome, timing))
            lines.append(f"| {variant.value} | " + " | ".join(cells) + " |")
        lines.append("")
        for triple in triples:
            if triple["plan"] == name:
                lines.append(
                    f"- {triple['model']} three-variant {triple['mode']} wall time: "
                    f"{triple['wall_seconds']:.3f}s"
                )
        lines.append("")
    lines.extend(["## Directive compliance and notes", ""])
    for row in cases:
        lines.append(f"### {row['model']} / {row['plan']} / {row['variant']}")
        lines.append("")
        safe_notes = html.escape(row["notes"] or "(none)").replace("\n", " ")
        lines.append(f"- Notes: {safe_notes}")
        lines.append(
            f"- Package/LLM attempts: {row['package_attempts']}/{row['llm_attempts']}"
        )
        lines.append(f"- Structure error counts: {row['structure_error_counts']}")
        for check in row["checks"]:
            result = "PASS" if check["passed"] else "FAIL"
            lines.append(f"- {result}: {check['name']} — {check['detail']}")
        lines.append("")
    lines.extend(["## Totals", ""])
    for model in models:
        total = totals[model]
        rate = total["compliance_rate"]
        compliance = f"{rate:.1%}" if rate is not None else "n/a"
        cost = total["estimated_cost"]
        cost_text = f"{cost:.6f}" if cost is not None else "n/a"
        lines.append(
            f"- {model}: success {total['success_rate']:.1%}; compliance "
            f"{compliance}; median {total['median_seconds']:.3f}s; "
            f"tokens {total['total_tokens']}; estimated cost {cost_text}"
        )
    return "\n".join(lines) + "\n"


def _offline_settings() -> Settings:
    placeholder = "postgresql+asyncpg://unused:unused@localhost/unused"
    return Settings(
        _env_file=None,
        database_url=placeholder,
        migration_database_url=placeholder,
        test_database_url=placeholder,
        test_migration_database_url=placeholder,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models")
    parser.add_argument("--plans")
    parser.add_argument(
        "--mode", choices=("parallel", "sequential"), default="parallel"
    )
    parser.add_argument("--pause-seconds", type=float, default=0)
    parser.add_argument("--save-packages", action="store_true")
    parser.add_argument("--price-in")
    parser.add_argument("--price-out")
    parser.add_argument("--no-env-file", action="store_true")
    args = parser.parse_args()
    settings = _offline_settings() if args.no_env_file else get_settings()
    configure_logging(settings.model_copy(update={"log_level": "INFO"}))
    selected_models = (
        [value.strip() for value in args.models.split(",")]
        if args.models
        else [settings.llm_model or "stub"]
    )
    if not selected_models or any(not value for value in selected_models):
        parser.error("--models requires model names")
    output = asyncio.run(
        run_evaluation(
            settings,
            models=selected_models,
            plans=_selected(args.plans, PLAN_NAMES),
            mode=args.mode,
            pause_seconds=args.pause_seconds,
            save_packages=args.save_packages,
            price_in=_prices(args.price_in),
            price_out=_prices(args.price_out),
        )
    )
    print(output)


if __name__ == "__main__":
    main()
