"""Evaluate saved Phase 3 packages with local scanners or the full fix loop."""

import argparse
import asyncio
import json
import statistics
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from pydantic import SecretStr

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
from app.scanners.external_modules import external_module_findings
from app.scanners.runner import ProcessToolRunner, ToolFailure, scanner_versions
from app.scanners.scan import Scanner, ScanObservation
from app.scanners.terraform_parser import parse_terraform
from app.scanners.trivy_parser import parse_trivy
from app.security.policy import classify
from app.security.reports import first_scan_counts

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
            model = case.get("generator_model") or case.get("model")
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
        for tool in ("checkov", "trivy", "terraform")
    }
    return {
        "checkov": values["checkov"],
        "trivy": values["trivy"],
        "terraform": values["terraform"],
        "combined": sum(values.values()),
    }


def _display(value: Any) -> str:
    return "—" if value is None else str(value)


def _count_text(counts: dict[str, int]) -> str:
    return ", ".join(f"{name}:{count}" for name, count in sorted(counts.items())) or "—"


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
        names = ("checkov", "trivy", "terraform")
        outputs = await asyncio.gather(
            *(scanner.run_tool(name, root, attempt=3) for name in names),
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
                    else parse_trivy(output.stdout, root, set(files))
                    if tool == "trivy"
                    else parse_terraform(output.stdout, root, set(files))
                )
            except ValueError:
                errors[tool] = "invalid_json"
                continue
            findings.extend(parsed)
        findings.extend(external_module_findings(files))
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
    packages_limit: int | None = None,
    remediate: bool = False,
    max_iterations: int | None = None,
    price_in: dict[str, float] | None = None,
    price_out: dict[str, float] | None = None,
    save_diffs: bool = False,
    output_root: Path = EVALS,
) -> Path:
    selected = packages if packages is not None else _default_packages()
    if packages_limit is not None:
        if packages_limit < 1:
            raise ValueError("packages_limit must be positive")
        selected = selected[:packages_limit]
    if not selected:
        raise ValueError("no saved packages found")
    limit = max_iterations or settings.max_remediation_iterations
    if limit < 1:
        raise ValueError("max_iterations must be positive")
    output = output_root / (
        "phase5b-security-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    )
    output.mkdir(parents=True, exist_ok=False)
    cases: list[dict[str, Any]] = []
    versions = scanner_versions()
    for folder in selected:
        folder = folder.resolve()
        package_name = "/".join(folder.parts[-3:])
        timeouts: list[dict[str, Any]] = []

        def observe(
            event: ScanObservation,
            package_name: str = package_name,
            timeouts: list[dict[str, Any]] = timeouts,
        ) -> None:
            print(
                f"package={package_name} iteration={event.iteration} "
                f"attempt={event.attempt} tool={event.tool} "
                f"duration={event.duration:.3f}s status={event.category}",
                file=sys.stderr,
                flush=True,
            )
            if event.category == "timeout":
                timeouts.append(
                    {
                        "package": package_name,
                        "iteration": event.iteration,
                        "attempt": event.attempt,
                        "tool": event.tool,
                        "duration_seconds": round(event.duration, 3),
                    }
                )

        scanner = Scanner(ProcessToolRunner(settings.scanner_timeout_seconds))
        scanner.observer = observe
        print(f"package={package_name} status=started", file=sys.stderr, flush=True)
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
        syntax_limited = any(
            item.tool == "terraform" and item.rule_id == "TERRAFORM_SYNTAX"
            for item in violations
        )
        blocking = [item for item in violations if item.blocking]
        high = _high_counts(violations)
        checkov_high = high["checkov"] if "checkov" not in errors else None
        trivy_high = high["trivy"] if "trivy" not in errors else None
        terraform_high = high["terraform"] if "terraform" not in errors else None
        combined_high = high["combined"] if not errors else None
        case: dict[str, Any] = {
            "generator_model": model,
            "plan": plan,
            "variant": variant.value,
            "first_scan_blocking_by_severity": _counts(violations),
            "first_scan_blocking_count": len(blocking),
            "first_scan_advisory_count": sum(not item.blocking for item in violations),
            "first_scan_checkov_high_or_critical": checkov_high,
            "first_scan_trivy_high_or_critical": trivy_high,
            "first_scan_terraform_high_or_critical": terraform_high,
            "first_scan_combined_high_or_critical": combined_high,
            "fr_g_05_pass": checkov_high == 0
            if variant == Variant.SECURITY and checkov_high is not None
            else None,
            "scanner_errors": errors,
            "scan_timeouts": timeouts,
            "syntax_limited": syntax_limited,
            "syntax_findings": [
                {
                    "rule_id": item.rule_id,
                    "file_path": item.file_path,
                    "line_start": item.line_start,
                    "title": item.title,
                }
                for item in violations
                if item.tool == "terraform" and item.rule_id == "TERRAFORM_SYNTAX"
            ],
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
            remaining = report["final"]["remaining_blocking"]
            fixing_model = (
                report.get("fixing_model")
                or settings.security_fix_model
                or settings.llm_model
                or "stub"
            )
            input_rate = (price_in or {}).get(fixing_model)
            output_rate = (price_out or {}).get(fixing_model)
            rejected = [fix for fix in fixes if not fix["accepted"]]
            rejected_by_reason = dict(
                Counter(str(fix.get("reason") or "unknown") for fix in rejected)
            )
            remaining_by_severity = dict(
                Counter(str(item["severity"]) for item in remaining)
            )
            case.update(
                {
                    "outcome": report["final"]["outcome"],
                    "iterations": len(report["iterations"]),
                    "fix_passes": report.get(
                        "fix_passes",
                        sum(bool(entry.get("fixes")) for entry in report["iterations"]),
                    ),
                    "stop_reason": report["final"].get("reason")
                    or report["final"]["outcome"],
                    "fixing_model": fixing_model,
                    "blocking_after_count": len(remaining),
                    "blocking_after_by_severity": remaining_by_severity,
                    "fixes_accepted": sum(bool(fix["accepted"]) for fix in fixes),
                    "fixes_rejected": [
                        {"file": fix["file"], "reason": fix["reason"]}
                        for fix in rejected
                    ],
                    "fixes_rejected_by_reason": rejected_by_reason,
                    "remaining_blocking": remaining,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "estimated_cost": (
                        (input_tokens * input_rate + output_tokens * output_rate)
                        / 1_000_000
                        if input_rate is not None and output_rate is not None
                        else None
                    ),
                }
            )
            if save_diffs and diff:
                path = output / "diffs" / folder.parent.parent.name / plan
                path.mkdir(parents=True, exist_ok=True)
                (path / f"{variant.value}.diff").write_text(diff, encoding="utf-8")
        elif remediate:
            case.update(
                {
                    "outcome": "error",
                    "iterations": 0,
                    "fix_passes": 0,
                    "stop_reason": "scan_error",
                    "fixing_model": None,
                    "blocking_after_count": None,
                    "blocking_after_by_severity": {},
                    "fixes_accepted": 0,
                    "fixes_rejected": [],
                    "fixes_rejected_by_reason": {},
                    "remaining_blocking": [],
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "estimated_cost": None,
                }
            )
        case["elapsed_seconds"] = round(time.monotonic() - started, 3)
        cases.append(case)
        print(
            f"package={package_name} status=finished "
            f"duration={case['elapsed_seconds']:.3f}s",
            file=sys.stderr,
            flush=True,
        )
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
            "first_scan_trivy_high_or_critical": sum(
                first_scan_counts(case).get("trivy") or 0 for case in group
            ),
            "first_scan_terraform_high_or_critical": sum(
                first_scan_counts(case).get("terraform") or 0 for case in group
            ),
            "first_scan_combined_high_or_critical": sum(
                case["first_scan_combined_high_or_critical"] or 0 for case in group
            ),
            "scanner_error_count": sum(bool(case["scanner_errors"]) for case in group),
            "syntax_limited_count": sum(case["syntax_limited"] for case in group),
            "fr_g_05_pass": bool(security)
            and all(case["fr_g_05_pass"] is True for case in security),
        }
    fixing_aggregate: dict[str, Any] = {}
    for model in sorted(
        {case["fixing_model"] for case in cases if case.get("fixing_model")}
    ):
        group = [case for case in cases if case.get("fixing_model") == model]
        before = sum(case["first_scan_blocking_count"] for case in group)
        after = sum(case["blocking_after_count"] for case in group)
        fixing_aggregate[model] = {
            "packages": len(group),
            "blocking_before": before,
            "blocking_after": after,
            "total_reduction_percent": 100 * (before - after) / before
            if before
            else 0.0,
            "clean_rate": sum(case["outcome"] == "clean" for case in group)
            / len(group),
            "mean_remaining": statistics.mean(
                case["blocking_after_count"] for case in group
            ),
        }
    result = {
        "mode": "remediate" if remediate else "scan_only",
        "scanners": versions,
        "cases": cases,
        "aggregate": aggregate,
        "fixing_aggregate": fixing_aggregate,
    }
    (output / "results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = ["# Phase 5b security evaluation", "", f"Mode: {result['mode']}", ""]
    lines += [
        "| Model | Plan | Variant | Scan | Blocking | Advisory | "
        "Checkov HIGH/CRITICAL | Trivy HIGH/CRITICAL | "
        "Terraform HIGH/CRITICAL | Combined | FR-G-05 |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for case in cases:
        error = (
            ", ".join(
                f"{tool}:{category}"
                for tool, category in case["scanner_errors"].items()
            )
            if case["scanner_errors"]
            else "syntax-limited (TERRAFORM_SYNTAX)"
            if case["syntax_limited"]
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
            first_scan_counts(case).get("trivy"),
            first_scan_counts(case).get("terraform"),
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
            f"Trivy HIGH/CRITICAL {values['first_scan_trivy_high_or_critical']}; "
            "Terraform HIGH/CRITICAL "
            f"{values['first_scan_terraform_high_or_critical']}; "
            f"combined {values['first_scan_combined_high_or_critical']}; "
            f"scanner errors {values['scanner_error_count']}; "
            f"syntax-limited scans {values['syntax_limited_count']}; "
            f"FR-G-05 {'PASS' if values['fr_g_05_pass'] else 'FAIL'}"
        )
    if remediate:
        lines.extend(["", "## Remediation results", ""])
        lines.extend(
            [
                "| Generator | Plan | Variant | Fixing model | Blocking "
                "before → after | Fix passes | Stop reason | Remaining by "
                "severity | Fixes accepted / rejected | Rejection reasons | "
                "Elapsed seconds | Tokens in / out | Cost |",
                "| --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | "
                "--- | ---: | ---: | ---: |",
            ]
        )
        for case in cases:
            fields = [
                case["generator_model"],
                case["plan"],
                case["variant"],
                case["fixing_model"],
                f"{case['first_scan_blocking_count']} → "
                f"{_display(case['blocking_after_count'])}",
                case["fix_passes"],
                case["stop_reason"],
                _count_text(case["blocking_after_by_severity"]),
                f"{case['fixes_accepted']} / {len(case['fixes_rejected'])}",
                _count_text(case["fixes_rejected_by_reason"]),
                case["elapsed_seconds"],
                f"{case['input_tokens']} / {case['output_tokens']}",
                f"{case['estimated_cost']:.6f}"
                if case["estimated_cost"] is not None
                else "—",
            ]
            lines.append("| " + " | ".join(map(str, fields)) + " |")
        lines.extend(["", "## Fixing model aggregates", ""])
        for model, values in fixing_aggregate.items():
            lines.append(
                f"- {model}: blocking {values['blocking_before']} → "
                f"{values['blocking_after']}; reduction "
                f"{values['total_reduction_percent']:.1f}%; clean rate "
                f"{values['clean_rate']:.1%}; mean remaining "
                f"{values['mean_remaining']:.2f}"
            )
    (output / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", nargs="+", type=Path)
    parser.add_argument("--packages-limit", type=_positive_int)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scan-only", action="store_true")
    mode.add_argument("--remediate", action="store_true")
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--price-in")
    parser.add_argument("--price-out")
    parser.add_argument("--save-diffs", action="store_true")
    args = parser.parse_args()
    settings = (
        get_settings()
        if args.remediate
        else Settings.model_construct(
            database_url=SecretStr("unused"),
            migration_database_url=SecretStr("unused"),
            test_database_url=SecretStr("unused"),
            test_migration_database_url=SecretStr("unused"),
        )
    )
    output = asyncio.run(
        run_evaluation(
            settings,
            packages=args.packages,
            packages_limit=args.packages_limit,
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
