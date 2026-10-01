"""Evaluate saved Phase 3 packages with local scanners or the full fix loop."""

import argparse
import asyncio
import json
import statistics
import time
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from app.agents.factory import AgentFactory
from app.core.config import Settings, get_settings
from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.db.session import make_app_engine, make_session_factory
from app.domain.enums import PackageStatus, RunStatus, Severity, Variant
from app.domain.models import IaCPackage
from app.domain.paths import validate_file_map
from app.domain.plan import DeploymentPlan
from app.domain.run_config import RunConfig
from app.domain.states import readiness_after_validation
from app.events.log import EventLog
from app.events.publisher import NullPublisher
from app.pipeline.stages import StageContext, UnavailableValidationStage
from app.pipeline.state import PipelineStateWriter
from app.scanners.checkov_parser import parse_checkov
from app.scanners.runner import ProcessToolRunner, ToolFailure, scanner_versions
from app.scanners.scan import Scanner
from app.scanners.tfsec_parser import parse_tfsec
from app.security.policy import classify

ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "docs/evals"
PHASE3 = (
    EVALS / "phase3-generators-20260930T045713473558Z/packages",
    EVALS / "phase3-generators-20260930T060923179316Z/packages",
)
PLANS = Path(__file__).resolve().parent / "fixtures/generators"


def _prices(raw: str | None) -> dict[str, float]:
    if raw is None:
        return {}
    prices: dict[str, float] = {}
    for entry in raw.split(","):
        name, separator, value = entry.partition("=")
        if not separator or not name.strip():
            raise ValueError("prices must use model=rate entries")
        rate = float(value)
        if not 0 <= rate < float("inf"):
            raise ValueError("prices must be finite and nonnegative")
        prices[name.strip()] = rate
    return prices


def _model_folder(model: str) -> str:
    import re

    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", model).strip("._-") or "model"
    return f"{stem[:60]}-{sha256(model.encode()).hexdigest()[:8]}"


def _model_name(folder: Path) -> str:
    results = folder.parents[1] / "results.json"
    if results.is_file():
        data = json.loads(results.read_text(encoding="utf-8"))
        for case in data.get("cases", []):
            model = case.get("model")
            if isinstance(model, str) and _model_folder(model) == folder.name:
                return model
    return folder.name


def _default_packages() -> list[Path]:
    return sorted(
        variant
        for base in PHASE3
        for variant in base.glob("*/*/*")
        if variant.is_dir() and variant.name in Variant._value2member_map_
    )


def _load_files(folder: Path) -> dict[str, str]:
    result = {
        path.relative_to(folder).as_posix(): path.read_text(encoding="utf-8")
        for path in folder.rglob("*")
        if path.is_file()
    }
    if not result:
        raise ValueError(f"empty package directory: {folder}")
    return validate_file_map(result)


def _counts(violations: list[Any]) -> dict[str, int]:
    return dict(Counter(item.severity.value for item in violations if item.blocking))


def _high_counts(violations: list[Any]) -> dict[str, int]:
    values = {
        tool: sum(
            item.tool == tool and item.severity in {Severity.HIGH, Severity.CRITICAL}
            for item in violations
        )
        for tool in ("checkov", "tfsec")
    }
    return {
        "checkov": values["checkov"],
        "tfsec": values["tfsec"],
        "combined": values["checkov"] + values["tfsec"],
    }


def _display(value: Any) -> str:
    return "—" if value is None else str(value)


async def _partial_scan(
    scanner: Scanner, files: dict[str, str], variant: Variant
) -> tuple[list[Any], dict[str, str]]:
    """Keep valid output from one tool if the other rejects generated IaC."""
    with TemporaryDirectory(prefix="infraarch-eval-") as directory:
        root = Path(directory)
        for path, content in files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="")
        names = ("checkov", "tfsec")
        outputs = await asyncio.gather(
            *(scanner.runner.run(name, root) for name in names),
            return_exceptions=True,
        )
        findings: list[Any] = []
        errors: dict[str, str] = {}
        for tool, output in zip(names, outputs, strict=True):
            if isinstance(output, ToolFailure):
                errors[tool] = output.category
                continue
            if isinstance(output, BaseException):
                errors[tool] = "crash"
                continue
            if output.exit_code not in (0, 1):
                errors[tool] = "crash"
                continue
            try:
                parsed = (
                    parse_checkov(output.stdout, root, set(files))
                    if tool == "checkov"
                    else parse_tfsec(output.stdout, root, set(files))
                )
            except ValueError:
                errors[tool] = "invalid_json"
                continue
            findings.extend(parsed)
        return classify(findings, variant, files), errors


async def _remediate(
    settings: Settings,
    scanner: Scanner,
    folder: Path,
    package: IaCPackage,
    max_iterations: int,
) -> tuple[dict[str, Any], str]:
    plan_path = PLANS / f"{folder.parent.name}.json"
    if not plan_path.is_file():
        raise ValueError(f"no saved plan for {folder.parent.name}")
    plan = DeploymentPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
    engine = make_app_engine(settings)
    sessions = make_session_factory(engine)
    config = RunConfig(max_iterations=max_iterations)
    resolved = config.resolve(settings)
    writer = PipelineStateWriter(sessions, EventLog(sessions, NullPublisher()))
    factory = AgentFactory(
        settings,
        session_factory=sessions,
        scanner=scanner,
        scanner_versions={
            tool: details["version"] if isinstance(details["version"], str) else None
            for tool, details in scanner_versions().items()
        },
    )
    try:
        async with sessions() as session:
            async with session.begin():
                run = await RunRepository(session).create(
                    f"Security evaluation of {folder}",
                    resolved.provider,
                    max_iterations,
                    model=resolved.model,
                )
                repository = PackageRepository(session)
                await repository.create(run.run_id, package.variant)
                await repository.save_files(run.run_id, package.variant, package.files)
        await writer.run_transition(
            run.run_id, RunStatus.RUNNING, message="evaluation started"
        )
        await writer.package_transition(
            run.run_id,
            package.variant,
            PackageStatus.GENERATED,
            message="evaluation package loaded",
        )
        ctx = StageContext(run.run_id, writer, plan, max_iterations=max_iterations)
        outcome = await factory.create_security_agent(config).run(
            ctx, package.variant, package
        )
        if outcome != PackageStatus.SCAN_ERROR:
            validation = await UnavailableValidationStage().run(
                ctx, package.variant, package
            )
            target = readiness_after_validation(outcome, validation)
            await writer.package_transition(
                run.run_id, package.variant, target, message="evaluation pending review"
            )
        await writer.run_transition(
            run.run_id,
            RunStatus.FAILED
            if outcome == PackageStatus.SCAN_ERROR
            else RunStatus.PARTIAL_SUCCESS,
            message="evaluation finished",
        )
        async with sessions() as session:
            row = await PackageRepository(session).get(run.run_id, package.variant)
            assert row is not None and row.security_report is not None
            return row.security_report["sessions"][-1], row.remediation_diff or ""
    finally:
        await engine.dispose()


async def run_evaluation(
    settings: Settings,
    *,
    packages: list[Path] | None = None,
    remediate: bool = False,
    max_iterations: int | None = None,
    price_in: dict[str, float] | None = None,
    price_out: dict[str, float] | None = None,
    save_diffs: bool = False,
    output_root: Path = EVALS,
) -> Path:
    selected = packages if packages is not None else _default_packages()
    if not selected:
        raise ValueError("no saved packages found")
    limit = max_iterations or settings.max_remediation_iterations
    if limit < 1:
        raise ValueError("max_iterations must be positive")
    output = output_root / (
        "phase5-security-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    )
    output.mkdir(parents=True, exist_ok=False)
    scanner = Scanner(ProcessToolRunner(settings.scanner_timeout_seconds))
    cases: list[dict[str, Any]] = []
    versions = scanner_versions()
    for folder in selected:
        folder = folder.resolve()
        variant = Variant(folder.name)
        model = _model_name(folder.parent.parent)
        plan = folder.parent.name
        files = _load_files(folder)
        package = IaCPackage(variant=variant, files=files)
        started = time.monotonic()
        errors: dict[str, str] = {}
        try:
            scan = await scanner.scan(files, variant)
            violations = scan.violations
        except ToolFailure:
            violations, errors = await _partial_scan(scanner, files, variant)
        blocking = [item for item in violations if item.blocking]
        high = _high_counts(violations)
        checkov_high = high["checkov"] if "checkov" not in errors else None
        tfsec_high = high["tfsec"] if "tfsec" not in errors else None
        combined_high = high["combined"] if not errors else None
        case: dict[str, Any] = {
            "generator_model": model,
            "plan": plan,
            "variant": variant.value,
            "first_scan_blocking_by_severity": _counts(violations),
            "first_scan_blocking_count": len(blocking),
            "first_scan_advisory_count": sum(not item.blocking for item in violations),
            "first_scan_checkov_high_or_critical": checkov_high,
            "first_scan_tfsec_high_or_critical": tfsec_high,
            "first_scan_combined_high_or_critical": combined_high,
            "fr_g_05_pass": checkov_high == 0
            if variant == Variant.SECURITY and checkov_high is not None
            else None,
            "scanner_errors": errors,
            "top_rule_ids": [
                rule
                for rule, _ in Counter(item.rule_id for item in blocking).most_common(
                    10
                )
            ],
        }
        if remediate and not errors:
            report, diff = await _remediate(settings, scanner, folder, package, limit)
            fixes = [
                fix for entry in report["iterations"] for fix in entry.get("fixes", [])
            ]
            input_tokens = sum(fix.get("input_tokens") or 0 for fix in fixes)
            output_tokens = sum(fix.get("output_tokens") or 0 for fix in fixes)
            case.update(
                {
                    "outcome": report["final"]["outcome"],
                    "iterations": len(report["iterations"]),
                    "fixes_accepted": sum(bool(fix["accepted"]) for fix in fixes),
                    "fixes_rejected": [
                        {"file": fix["file"], "reason": fix["reason"]}
                        for fix in fixes
                        if not fix["accepted"]
                    ],
                    "remaining_blocking": report["final"]["remaining_blocking"],
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "estimated_cost": (
                        input_tokens * (price_in or {}).get(model, 0)
                        + output_tokens * (price_out or {}).get(model, 0)
                    )
                    / 1_000_000,
                }
            )
            if save_diffs and diff:
                path = output / "diffs" / folder.parent.parent.name / plan
                path.mkdir(parents=True, exist_ok=True)
                (path / f"{variant.value}.diff").write_text(diff, encoding="utf-8")
        case["elapsed_seconds"] = round(time.monotonic() - started, 3)
        cases.append(case)
    aggregate: dict[str, Any] = {}
    for model in sorted({case["generator_model"] for case in cases}):
        group = [case for case in cases if case["generator_model"] == model]
        security = [case for case in group if case["variant"] == "security"]
        aggregate[model] = {
            "mean_blocking_per_package": statistics.mean(
                case["first_scan_blocking_count"] for case in group
            ),
            "clean_first_scan_share": sum(
                case["first_scan_blocking_count"] == 0 for case in group
            )
            / len(group),
            "first_scan_checkov_high_or_critical": sum(
                case["first_scan_checkov_high_or_critical"] or 0 for case in group
            ),
            "first_scan_tfsec_high_or_critical": sum(
                case["first_scan_tfsec_high_or_critical"] or 0 for case in group
            ),
            "first_scan_combined_high_or_critical": sum(
                case["first_scan_combined_high_or_critical"] or 0 for case in group
            ),
            "scanner_error_count": sum(bool(case["scanner_errors"]) for case in group),
            "fr_g_05_pass": bool(security)
            and all(case["fr_g_05_pass"] is True for case in security),
        }
    result = {
        "mode": "remediate" if remediate else "scan_only",
        "scanners": versions,
        "cases": cases,
        "aggregate": aggregate,
    }
    (output / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = ["# Phase 5 security evaluation", "", f"Mode: {result['mode']}", ""]
    lines += [
        "| Model | Plan | Variant | Scan | Blocking | Advisory | "
        "Checkov HIGH/CRITICAL | tfsec HIGH/CRITICAL | Combined | FR-G-05 |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in cases:
        error = (
            ", ".join(
                f"{tool}:{category}"
                for tool, category in case["scanner_errors"].items()
            )
            if case["scanner_errors"]
            else "ok"
        )
        fields = [
            case["generator_model"],
            case["plan"],
            case["variant"],
            error,
            case["first_scan_blocking_count"],
            case["first_scan_advisory_count"],
            case["first_scan_checkov_high_or_critical"],
            case["first_scan_tfsec_high_or_critical"],
            case["first_scan_combined_high_or_critical"],
            case["fr_g_05_pass"],
        ]
        lines.append("| " + " | ".join(_display(value) for value in fields) + " |")
    lines.extend(["", "## Generator model aggregates", ""])
    for model, values in aggregate.items():
        lines.append(
            f"- {model}: mean blocking {values['mean_blocking_per_package']:.2f}; "
            f"clean first scan {values['clean_first_scan_share']:.1%}; "
            f"Checkov HIGH/CRITICAL {values['first_scan_checkov_high_or_critical']}; "
            f"tfsec HIGH/CRITICAL {values['first_scan_tfsec_high_or_critical']}; "
            f"combined {values['first_scan_combined_high_or_critical']}; "
            f"scanner errors {values['scanner_error_count']}; "
            f"FR-G-05 {'PASS' if values['fr_g_05_pass'] else 'FAIL'}"
        )
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", nargs="+", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scan-only", action="store_true")
    mode.add_argument("--remediate", action="store_true")
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--price-in")
    parser.add_argument("--price-out")
    parser.add_argument("--save-diffs", action="store_true")
    args = parser.parse_args()
    output = asyncio.run(
        run_evaluation(
            get_settings(),
            packages=args.packages,
            remediate=args.remediate,
            max_iterations=args.max_iterations,
            price_in=_prices(args.price_in),
            price_out=_prices(args.price_out),
            save_diffs=args.save_diffs,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
