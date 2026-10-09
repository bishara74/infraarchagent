"""Validate original Phase 3 packages offline, without a database or LLM."""

import argparse
import asyncio
import json
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from app.domain.enums import Variant
from app.domain.package_layout import classify_path
from app.domain.paths import validate_file_map, validate_relative_path
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationCheck, ValidationReport
from app.validation.engine import ValidationEngine
from app.validation.tools import DEFAULT_MIRROR, mirror_present

ROOT = Path(__file__).resolve().parents[2]
PHASE3 = (
    ROOT / "docs/evals/phase3-generators-20260930T045713473558Z/packages",
    ROOT / "docs/evals/phase3-generators-20260930T060923179316Z/packages",
)
PLANS = Path(__file__).resolve().parent / "fixtures/generators"
SEMANTIC_GAP = (
    "An Aurora cluster without database instances is a semantic deployment gap: "
    "none of these static checks detects it. Valid does not prove deployability."
)


def default_packages() -> list[Path]:
    return sorted(
        folder
        for root in PHASE3
        for folder in root.glob("*/*/*")
        if folder.is_dir() and folder.name in Variant._value2member_map_
    )


def load_files(folder: Path) -> dict[str, str]:
    if folder.is_symlink():
        raise ValueError("unsafe evaluation input")
    paths = sorted(path for path in folder.rglob("*") if path.is_file())
    # Validate every path before reading any content, including dotenv files.
    for path in paths:
        relative = validate_relative_path(path.relative_to(folder).as_posix())
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(folder.resolve())
            or any(part.startswith(".env") for part in path.parts)
            or relative != "README.md"
            and classify_path(relative) is None
        ):
            raise ValueError("unsafe evaluation input")
    if not paths:
        raise ValueError("empty evaluation input")
    return validate_file_map(
        {
            path.relative_to(folder).as_posix(): path.read_text(encoding=("utf-8"))
            for path in paths
        }
    )


def source_digest(files: dict[str, str]) -> str:
    digest = sha256()
    for path, source in sorted(files.items()):
        digest.update(path.encode() + b"\0" + source.encode() + b"\0")
    return digest.hexdigest()


def _count_text(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items())) or "—"


async def run_evaluation(
    *,
    packages: list[Path] | None = None,
    output_root: Path = ROOT / "docs/evals",
    engine: ValidationEngine | None = None,
) -> Path:
    validator = engine or ValidationEngine()
    selected = default_packages() if packages is None else sorted(packages)
    if not selected:
        raise ValueError("no packages selected")
    cases = []
    for folder in selected:
        names = [validate_relative_path(part) for part in folder.parts[-3:]]
        model, plan_name, variant = names
        identifier = "/".join(names)
        print(f"package={identifier} status=started", file=sys.stderr, flush=True)
        started = time.monotonic()
        digest = None
        try:
            if plan_name not in {"three_tier", "kubernetes_monitoring"}:
                raise ValueError("unknown evaluation plan")
            plan = DeploymentPlan.model_validate_json(
                (PLANS / f"{plan_name}.json").read_text()
            )
            files = load_files(folder)
            digest = source_digest(files)
            report = await validator.validate(plan, files)
        except (ValueError, OSError):
            report = ValidationReport.build(
                [
                    ValidationCheck(
                        check_id="evaluation.input",
                        category="structure",
                        tool="builtin",
                        status="skipped",
                        skip_reason="input_unavailable",
                        message="Evaluation input unavailable or unsafe",
                    )
                ],
                terraform_required=True,
                tool_versions=validator.versions,
                abort_reason="internal_error",
            )
        case = {
            ("package"): identifier,
            ("model"): model,
            ("plan"): plan_name,
            ("variant"): variant,
            "source_sha256": digest,
            "result": report.summary.result,
            ("failed_by_category"): dict(
                sorted(
                    Counter(
                        c.category for c in report.checks if c.status == ("failed")
                    ).items()
                )
            ),
            "warnings": report.summary.warnings,
            "skipped": report.summary.skipped,
            ("skip_reasons"): dict(
                sorted(
                    Counter(
                        c.skip_reason for c in report.checks if c.status == ("skipped")
                    ).items()
                )
            ),
            "duration_seconds": round(time.monotonic() - started, 6),
            "tool_versions": report.tool_versions,
            "report": report.model_dump(mode="json"),
        }
        cases.append(case)
        print(
            f"package={identifier} result={report.summary.result} "
            f"duration={case['duration_seconds']}",
            file=sys.stderr,
            flush=True,
        )
    totals = {
        result: sum(case[("result")] == result for case in cases)
        for result in (("valid"), ("invalid"), ("error"))
    }
    known_syntax = {}
    for plan_name, variant, path, line in (
        ("kubernetes_monitoring", "cost", "terraform/main.tf", 172),
        ("three_tier", "performance", "terraform/ecs.tf", 24),
    ):
        matches = [
            case
            for case in cases
            if case[("model")].startswith("openai_gpt-oss")
            and case[("plan")] == plan_name
            and case[("variant")] == variant
        ]
        if matches:
            known_syntax[f"gpt-oss/{plan_name}/{variant}"] = any(
                c["tool"] == "terraform"
                and c["status"] == "failed"
                and c["file_path"] == path
                and c["line_start"] == line
                for case in matches
                for c in case["report"]["checks"]
            )
    timestamp = datetime.now(UTC)
    output = output_root / f"phase6-validation-{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}"
    output.mkdir(parents=True, exist_ok=False)
    data = {
        "created_at": timestamp.isoformat(),
        "offline": True,
        "mirror_present": mirror_present(validator.mirror),
        "tool_versions": validator.versions,
        "totals": totals,
        "cases": cases,
        "known_syntax_failures_confirmed": known_syntax,
        "semantic_gap": SEMANTIC_GAP,
    }
    (output / "results.json").write_text(json.dumps(data, indent=2) + "\n")
    lines = [
        "# Phase 6 offline validation",
        "",
        f"{len(cases)} original packages: {_count_text(totals)}.",
        "",
        (
            "Local tools only, black-hole proxies, no data"
            "base or LLM. Original files are unchanged; so"
            "urce hashes identify the inputs."
        ),
        "",
        (
            "| Package | Result | Failures by category | W"
            "arnings | Skips/reasons | Seconds |"
        ),
        "|---|---|---|---:|---|---:|",
    ]
    for case in cases:
        failures = _count_text(case["failed_by_category"])
        skips = _count_text(case["skip_reasons"])
        lines.append(
            f"| {case['package']} | {case['result']} | {failures} | "
            f"{case['warnings']} | {skips} | {case['duration_seconds']:.3f} |"
        )
    lines.extend(
        [
            "",
            ("Tool versions: ")
            + ("; ").join(
                f"{name}: {version or ('not installed')}"
                for name, version in sorted(validator.versions.items())
            ),
            "",
        ]
    )
    for name, confirmed in known_syntax.items():
        evidence = (
            "confirmed from Terraform diagnostics" if confirmed else "NOT confirmed"
        )
        lines.append(f"Known syntax failure {name}: {evidence}.")
    lines.extend(
        [
            "",
            SEMANTIC_GAP,
            "",
            (
                "Full checks, file/line locations, skip reason"
                "s, omitted counts and remediation targets are"
                " in results.json."
            ),
            "",
        ]
    )
    (output / "summary.md").write_text("\n".join(lines))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, action="append")
    parser.add_argument("--output-root", type=Path, default=ROOT / "docs/evals")
    parser.add_argument("--mirror", type=Path, default=DEFAULT_MIRROR)
    args = parser.parse_args()
    output = asyncio.run(
        run_evaluation(
            packages=args.package,
            output_root=args.output_root,
            engine=ValidationEngine(mirror=args.mirror),
        )
    )
    print(output)


if __name__ == "__main__":
    main()
