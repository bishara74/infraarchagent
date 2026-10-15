"""Small allowlisted quality evidence, independent of generated source/diffs."""

import json
import re
from collections import Counter
from pathlib import Path
from uuid import UUID

from app.core.logging import REDACTED, RedactingFilter
from app.domain.enums import PackageStatus
from app.domain.paths import validate_relative_path
from app.domain.review import security_final
from scripts.phase9_common import ROOT, write_json


def safe_text(value: object, redactor: RedactingFilter, limit: int = 500) -> str:
    text = redactor.redact(str(value)).replace(str(ROOT), REDACTED)
    text = re.sub(r"/tmp/(?:infraarch|pytest-of-)[^\s\"'<>]*", REDACTED, text)
    return " ".join(text.split())[:limit]


def quality_snapshot(package: dict, redactor: RedactingFilter) -> dict:
    """Construct every field explicitly: never copy arbitrary report metadata."""
    status = package.get("status")
    if status not in {item.value for item in PackageStatus}:
        status = "unknown"
    validation = package.get("validation_report") or {}
    checks = []
    for raw in validation.get("checks", []):
        if raw.get("status") != "failed":
            continue
        path = raw.get("file_path")
        try:
            path = validate_relative_path(path) if isinstance(path, str) else None
        except ValueError:
            path = None
        checks.append(
            {
                "check_id": safe_text(raw.get("check_id", "unknown"), redactor, 100),
                "message": safe_text(raw.get("message", ""), redactor),
                "file_path": safe_text(path, redactor, 255) if path else None,
                **{
                    key: raw.get(key)
                    if type(raw.get(key)) is int and raw[key] > 0
                    else None
                    for key in ("line_start", "line_end")
                },
            }
        )
    final = security_final(package.get("security_report"))
    findings = Counter(
        safe_text(item.get("rule_id", "unknown"), redactor, 100)
        for item in final.get("remaining_blocking", [])
    )
    remediation = validation.get("remediation") or {}
    return {
        "status": status,
        "review_reasons": sorted(
            {
                safe_text(reason, redactor, 100)
                for reason in package.get("review_reasons", [])
            }
        ),
        "failed_checks": checks,
        "remaining_findings": dict(sorted(findings.items())),
        "counts": {
            "failed_checks": len(checks),
            "remaining_findings": sum(findings.values()),
            "deterministic_repairs": len(remediation.get("deterministic_repairs", [])),
            "validation_repair_rounds": sum(
                r.get("outcome") in {"accepted", "rejected"}
                for r in remediation.get("rounds", [])
            ),
            "security_iterations": package.get("iteration_count")
            if type(package.get("iteration_count")) is int
            else None,
        },
    }


def quality_table(
    packages: list[dict], *, missing: int = 0, unavailable: int = 0
) -> tuple[dict, str]:
    statuses = Counter(p["status"] for p in packages)
    reasons = Counter(reason for p in packages for reason in p["review_reasons"])
    checks = Counter(
        (c["check_id"], c["message"]) for p in packages for c in p["failed_checks"]
    )
    findings: Counter[str] = Counter()
    for package in packages:
        findings.update(package["remaining_findings"])
    ready = statuses["production_ready"]
    total = len(packages)
    result = {
        "counts": {
            "packages": total,
            "missing_variants": missing,
            "unavailable_runs": unavailable,
            "production_ready": ready,
        },
        "production_ready_rate": ready / total if total else None,
        "status_counts": dict(statuses.most_common()),
        "review_reason_counts": dict(reasons.most_common()),
        "failed_check_counts": [
            {"check_id": k[0], "message": k[1], "count": n}
            for k, n in checks.most_common()
        ],
        "remaining_finding_counts": dict(findings.most_common()),
    }
    rate = f"{ready}/{total} ({100 * ready / total:.2f}%)" if total else "unknown"
    lines = [
        f"Production-ready rate among generated packages: **{rate}**.",
        f"Missing variants: {missing}; runs without quality snapshots: {unavailable}.",
    ]
    for title, rows in (
        ("Package status", statuses.most_common()),
        ("Review reason", reasons.most_common()),
        ("Failed check", [(f"{k[0]}: {k[1]}", n) for k, n in checks.most_common(20)]),
        ("Remaining blocking rule", findings.most_common(20)),
    ):
        lines += ["", f"| {title} | Count |", "|---|---:|"]
        lines += [
            f"| {str(key).replace('|', chr(92) + '|')} | {count} |"
            for key, count in rows
        ]
    return result, "\n".join(lines)


def recompute_quality(results_dir: Path, snapshots_dir: Path, output_dir: Path) -> None:
    results_dir, snapshots_dir, output_dir = (
        p.resolve() for p in (results_dir, snapshots_dir, output_dir)
    )
    if any(
        output_dir.is_relative_to(p) or p.is_relative_to(output_dir)
        for p in (results_dir, snapshots_dir)
    ):
        raise ValueError("Quality output must be separate from inputs")
    rows = json.loads((results_dir / "results.json").read_text())["runs"]
    identifiers = sorted(
        {
            str(UUID(row["run_id"]))
            for row in rows
            if row.get("run_id") and row.get("measurement") in {"pr01", "pr03"}
        }
    )
    packages, inputs = [], {}
    missing = unavailable = 0
    redactor = RedactingFilter()
    for run_id in identifiers:
        full = snapshots_dir / f"{run_id}.json"
        compact = snapshots_dir / run_id
        current = {}
        if full.is_file():
            snapshot = json.loads(full.read_text())
            missing += len(snapshot.get("missing_variants", []))
            current = {
                p["variant"]: quality_snapshot(p, redactor)
                for p in snapshot.get("packages", [])
                if p.get("variant") in {"cost", "performance", "security"}
            }
        elif compact.is_dir():
            for variant in ("cost", "performance", "security"):
                path = compact / f"{variant}.json"
                if path.is_file():
                    raw = json.loads(path.read_text())
                    # Re-allowlist historical compact data before exporting it.
                    pseudo = {
                        "status": raw.get("status"),
                        "review_reasons": raw.get("review_reasons", []),
                        "validation_report": {
                            "checks": [
                                {**c, "status": "failed"}
                                for c in raw.get("failed_checks", [])
                            ]
                        },
                        "security_report": {
                            "final": {
                                "remaining_blocking": [
                                    {"rule_id": rule}
                                    for rule, count in raw.get(
                                        "remaining_findings", {}
                                    ).items()
                                    for _ in range(count)
                                ]
                            }
                        },
                    }
                    current[variant] = quality_snapshot(pseudo, redactor)
                    for key in current[variant]["counts"]:
                        value = raw.get("counts", {}).get(key)
                        if type(value) is int and value >= 0:
                            current[variant]["counts"][key] = value
            missing += 3 - len(current)
        else:
            unavailable += 1
            missing += sum(
                row.get(v + "_variant_status") == "failed"
                for row in rows
                if row.get("run_id") == run_id
                for v in ("cost", "performance", "security")
            )
        inputs[run_id] = current
        packages.extend(current.values())
    result, table = quality_table(packages, missing=missing, unavailable=unavailable)
    output_dir.mkdir(parents=True, exist_ok=False)
    for run_id, variants in inputs.items():
        directory = output_dir / "quality" / run_id
        directory.mkdir(parents=True)
        for variant, package in variants.items():
            write_json(directory / f"{variant}.json", package)
    write_json(output_dir / "quality.json", result)
    (output_dir / "summary.md").write_text("# Package quality\n\n" + table + "\n")
