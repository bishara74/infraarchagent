"""Small allowlisted quality evidence, independent of generated source/diffs."""

import json
import re
from collections import Counter
from pathlib import Path
from uuid import UUID

from app.core.logging import REDACTED, RedactingFilter
from app.domain.enums import PackageStatus
from app.domain.paths import validate_relative_path
from app.domain.review import security_final, security_iterations
from app.security.profiles import PROFILE_IDS, assess
from scripts.phase9_common import ROOT, write_json
from scripts.phase9_report import statistics_for
from scripts.phase9c_metrics import number
from scripts.phase9e_metrics import REASONS, measurement, measurement_summary
from scripts.phase9f_metrics import (
    snapshot as phase9f_snapshot,
)
from scripts.phase9f_metrics import (
    summary as phase9f_summary,
)
from scripts.phase9g_metrics import compact_evidence, fixer_evidence


def safe_text(value: object, redactor: RedactingFilter, limit: int = 500) -> str:
    text = redactor.redact(str(value)).replace(str(ROOT), REDACTED)
    text = re.sub(r"/tmp/(?:infraarch|pytest-of-)[^\s\"'<>]*", REDACTED, text)
    return " ".join(text.split())[:limit]


GENERATION_METRICS = (
    "generator_schema_only_context_chars",
    "generator_security_context_chars",
    "generator_schema_context_overflow",
    "generator_schema_omitted_resource_types",
)


def generation_metrics(raw: dict) -> dict:
    """Keep historical absence distinct from a measured zero or no overflow."""
    result = {}
    for key in GENERATION_METRICS:
        if key not in raw:
            continue
        value = raw[key]
        if key.endswith("_chars"):
            result[key] = value if type(value) is int and value >= 0 else None
        elif key.endswith("_overflow"):
            result[key] = value if type(value) is bool else None
        else:
            result[key] = (
                {
                    tier: [
                        name
                        for name in value.get(tier, [])
                        if isinstance(name, str)
                        and re.fullmatch(r"aws_[a-z0-9_]+", name)
                    ]
                    for tier in ("required", "conditional_required")
                }
                if isinstance(value, dict)
                and all(
                    isinstance(value.get(tier, []), list)
                    for tier in ("required", "conditional_required")
                )
                else None
            )
    return result


def quality_snapshot(package: dict, redactor: RedactingFilter) -> dict:
    """Construct every field explicitly: never copy arbitrary report metadata."""
    status = package.get("status")
    legacy = package.get("legacy_label_mapped") is True or status in {
        "production_ready",
        "not_production_ready",
    }
    if status == "production_ready":
        final = security_final(package.get("security_report"))
        valid = (package.get("validation_report") or {}).get("summary", {}).get(
            "result"
        ) == "valid"
        status = (
            "engineer_approved"
            if (package.get("review_decision") or {}).get("action") == "approve"
            else "checks_passed"
            if final.get("outcome") == "clean"
            and not final.get("remaining_blocking")
            and valid
            else "pending_review"
        )
    elif status == "not_production_ready":
        status = "rejected"
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
                "origin": raw.get("origin")
                if raw.get("origin") in {"generated", "security_fix", "repair"}
                else "unknown",
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
    proposal_contexts = [
        {
            "file_type": "terraform"
            if str(f.get("file") or "").startswith("terraform/")
            else "other"
            if f.get("file")
            else "unknown",
            "chars": f.get("schema_context_chars")
            if type(f.get("schema_context_chars")) is int
            and f["schema_context_chars"] >= 0
            else None,
            "reason": f.get("schema_context_reason")
            if f.get("schema_context_reason")
            in {
                "not_terraform",
                "schema_available",
                "unparseable_document",
                "no_schema_entries",
                "not_attempted",
            }
            else "unknown",
        }
        for iteration in security_iterations(package.get("security_report"))
        for f in iteration.get("fixes", [])
    ]
    remediation = validation.get("remediation") or {}
    gate = remediation.get("gate") or {}
    rounds = [
        {
            "phase": r.get("phase")
            if r.get("phase") in {"generation", "before_security", "after_security"}
            else "unknown",
            "outcome": r.get("outcome")
            if r.get("outcome") in {"accepted", "rejected", "stopped"}
            else "unknown",
            "reason": r.get("reason")
            if r.get("reason")
            in {
                "improved",
                "no_improvement",
                "new_blocking_findings",
                "invalid_patch",
                "verification_unavailable",
                "deadline",
                "round_limit",
                "no_targets",
            }
            else "unknown",
            "error_classes": [
                safe_text(c, redactor)
                for c in r.get("error_classes", [])
                if isinstance(c, str)
            ],
            "schema_context_chars": r.get("schema_context_chars")
            if type(r.get("schema_context_chars")) is int
            and r["schema_context_chars"] >= 0
            else None,
        }
        for r in remediation.get("rounds", [])
    ]
    assessments = assess(package)
    for view in assessments.values():
        view["excepted"] = [
            {
                key: safe_text(value, redactor) if isinstance(value, str) else value
                for key, value in finding.items()
            }
            for finding in view["excepted"]
        ]
    return {
        "status": status,
        "legacy_label_mapped": legacy,
        "profile_assessments": assessments,
        "validation_result": validation.get("summary", {}).get("result")
        if validation.get("summary", {}).get("result") in {"valid", "invalid", "error"}
        else None,
        "phase9f": phase9f_snapshot(package, redactor),
        "fixer_attempts": fixer_evidence(package),
        "review_reasons": sorted(
            {
                safe_text(reason, redactor, 100)
                for reason in package.get("review_reasons", [])
            }
        ),
        "failed_checks": checks,
        "remaining_findings": dict(sorted(findings.items())),
        "phase9e": {
            **generation_metrics(remediation),
            "security_context_measurements": proposal_contexts,
            "generator_schema_context_chars": remediation.get(
                "generator_schema_context_chars"
            )
            if type(remediation.get("generator_schema_context_chars")) is int
            and remediation["generator_schema_context_chars"] >= 0
            else None,
            "initialization": {
                key: value
                for key, raw in (remediation.get("initialization") or {}).items()
                if key
                in {
                    "init_runs",
                    "init_reused",
                    "reinitializations",
                    "init_seconds",
                    "validate_seconds",
                }
                and (value := number(raw)) is not None
            }
            or None,
            "gate_outcome": gate.get("outcome")
            if gate.get("outcome")
            in {"passed", "failed", "error", "valid", "invalid", "deadline"}
            else "unknown",
            "gate_failed_checks": [
                {
                    "check_id": safe_text(c.get("check_id", "unknown"), redactor, 100),
                    "message": safe_text(c.get("message", ""), redactor),
                }
                for c in gate.get("failed_checks", [])
                if isinstance(c, dict)
            ],
            "init_categories": [
                safe_text(r.get("init_outcome", "unknown"), redactor, 100)
                for r in gate.get("terraform", [])
            ],
            "repair_rounds": rounds,
            "measurements": [
                m
                for raw in remediation.get("measurements", [])
                if (m := measurement(raw)) is not None
            ],
            "security_schema_context_chars": [
                f["schema_context_chars"]
                for iteration in security_iterations(package.get("security_report"))
                for f in iteration.get("fixes", [])
                if type(f.get("schema_context_chars")) is int
                and f["schema_context_chars"] >= 0
            ],
            "security_iteration_repairs": [
                {
                    "outcome": v.get("outcome")
                    if v.get("outcome")
                    in {"accepted", "rolled_back", "no_change", "stopped"}
                    else "unknown",
                    "error_classes": [
                        safe_text(c, redactor)
                        for c in v.get("error_classes", [])
                        if isinstance(c, str)
                    ],
                    "reasons": [
                        r
                        for r in v.get("reasons", [])
                        if isinstance(r, str) and r in REASONS
                    ],
                }
                for iteration in security_iterations(package.get("security_report"))
                if isinstance(v := iteration.get("verification"), dict)
            ],
        },
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
    ready = statuses["checks_passed"]
    total = len(packages)
    result = {
        "counts": {
            "packages": total,
            "missing_variants": missing,
            "unavailable_runs": unavailable,
            "checks_passed": ready,
        },
        "checks_passed_rate": ready / total if total else None,
        "legacy_labels_mapped": sum(
            bool(p.get("legacy_label_mapped")) for p in packages
        ),
        "status_counts": dict(statuses.most_common()),
        "profile_rates": {
            name: {
                "passed": sum(
                    p.get("profile_assessments", {}).get(name, {}).get("checks_passed")
                    is True
                    for p in packages
                ),
                "packages": total,
            }
            for name in PROFILE_IDS
        },
        "review_reason_counts": dict(reasons.most_common()),
        "failed_check_counts": [
            {"check_id": k[0], "message": k[1], "count": n}
            for k, n in checks.most_common()
        ],
        "remaining_finding_counts": dict(findings.most_common()),
    }
    if not packages or not all(
        "contextual-v2" in p.get("profile_assessments", {}) for p in packages
    ):
        result["profile_rates"]["contextual-v2"]["passed"] = None
    origins = Counter(
        c.get("origin", "unknown") for p in packages for c in p["failed_checks"]
    )
    outcomes = Counter(
        (r["phase"], r["outcome"], r["reason"], error)
        for p in packages
        for r in p.get("phase9e", {}).get("repair_rounds", [])
        for error in (r["error_classes"] or ["unknown"])
    )
    measured, measured_table = measurement_summary(
        [m for p in packages for m in p.get("phase9e", {}).get("measurements", [])]
    )
    result.update(
        final_failure_origins=dict(origins),
        measurements=measured,
        repair_outcomes_by_class=[
            {
                "phase": k[0],
                "outcome": k[1],
                "reason": k[2],
                "error_class": k[3],
                "count": n,
            }
            for k, n in sorted(outcomes.items())
        ],
    )
    initialization = [p.get("phase9e", {}).get("initialization") for p in packages]
    result["gate_outcomes"] = dict(
        Counter(p.get("phase9e", {}).get("gate_outcome", "unknown") for p in packages)
    )
    result["init_categories"] = dict(
        Counter(
            c for p in packages for c in p.get("phase9e", {}).get("init_categories", [])
        )
    )
    context_records = [
        r
        for p in packages
        for r in p.get("phase9e", {}).get("security_context_measurements", [])
    ]
    result["security_context_coverage"] = {
        kind: {
            "total": len(selected),
            "positive": sum((r["chars"] or 0) > 0 for r in selected),
            "zero": sum(r["chars"] == 0 for r in selected),
            "missing": sum(r["chars"] is None for r in selected),
            "reasons": dict(Counter(r["reason"] for r in selected)),
        }
        for kind in ("terraform", "other", "unknown")
        for selected in [[r for r in context_records if r["file_type"] == kind]]
    }
    result["schema_context_chars"] = {
        "generator": statistics_for(
            [
                n
                for p in packages
                if type(n := p.get("phase9e", {}).get("generator_schema_context_chars"))
                is int
            ]
        ),
        "repair": statistics_for(
            [
                r["schema_context_chars"]
                for p in packages
                for r in p.get("phase9e", {}).get("repair_rounds", [])
                if r["schema_context_chars"] is not None
            ]
        ),
        "security": statistics_for(
            [
                n
                for p in packages
                for n in p.get("phase9e", {}).get("security_schema_context_chars", [])
            ]
        ),
    }
    measured_generation = [
        p.get("phase9e", {})
        for p in packages
        if type(p.get("phase9e", {}).get("generator_schema_only_context_chars")) is int
    ]
    if measured_generation:
        result["schema_context_chars"]["generator_schema_only"] = statistics_for(
            [
                n
                for p in measured_generation
                if type(n := p.get("generator_schema_only_context_chars")) is int
            ]
        )
        result["generator_schema_overflow"] = {
            "measured_packages": len(measured_generation),
            "overflow_packages": sum(
                p.get("generator_schema_context_overflow") is True
                for p in measured_generation
            ),
            "unknown_packages": len(packages)
            - sum(
                type(p.get("phase9e", {}).get("generator_schema_context_overflow"))
                is bool
                for p in packages
            ),
            "omitted_types": {
                tier: dict(
                    Counter(
                        name
                        for p in measured_generation
                        for name in (
                            p.get("generator_schema_omitted_resource_types") or {}
                        ).get(tier, [])
                    )
                )
                for tier in ("required", "conditional_required")
            },
        }
    result["security_outcomes_by_class"] = [
        {"outcome": k[0], "reason": k[1], "error_class": k[2], "count": n}
        for k, n in sorted(
            Counter(
                (r["outcome"], ",".join(r["reasons"]), error)
                for p in packages
                for r in p.get("phase9e", {}).get("security_iteration_repairs", [])
                for error in (r["error_classes"] or ["unknown"])
            ).items()
        )
    ]
    result["package_initialization"] = {
        "packages_measured": sum(value is not None for value in initialization),
        "packages_unknown": sum(value is None for value in initialization),
        **{
            key: sum((value or {}).get(key, 0) for value in initialization)
            for key in (
                "init_runs",
                "init_reused",
                "reinitializations",
                "init_seconds",
                "validate_seconds",
            )
        },
    }
    rate = f"{ready}/{total} ({100 * ready / total:.2f}%)" if total else "unknown"
    lines = [
        f"Checks-passed rate among generated packages: **{rate}**.",
        f"Legacy labels mapped: {result['legacy_labels_mapped']}. "
        f"Missing variants: {missing}; runs without quality snapshots: {unavailable}.",
        "Strict / contextual-v1 / contextual-v2 assessments: "
        + "; ".join(
            (
                f"{name}: unavailable"
                if view["passed"] is None
                else f"{name}: {view['passed']}/{total}"
            )
            for name, view in result["profile_rates"].items()
        )
        + ". Contextual results are experimental and never change package labels.",
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
    lines += [
        "",
        "Final failure origins: " + str(dict(origins)),
        "",
        "| Repair phase / outcome / reason | Error class | Count |",
        "|---|---|---:|",
    ]
    lines += [
        f"| {' / '.join(k[:3])} | {k[3].replace('|', '/')} | {n} |"
        for k, n in sorted(outcomes.items())
    ]
    lines += [
        "",
        measured_table,
        "",
        "Package initialization totals: " + str(result["package_initialization"]),
        "Gate outcomes: " + str(result["gate_outcomes"]),
        "Init categories: " + str(result["init_categories"]),
        "Schema context sizes (characters): " + str(result["schema_context_chars"]),
        *(
            ["Schema guidance overflow: " + str(result["generator_schema_overflow"])]
            if "generator_schema_overflow" in result
            else []
        ),
        "Security context coverage: " + str(result["security_context_coverage"]),
        "Security iteration outcomes by class: "
        + str(result["security_outcomes_by_class"]),
    ]
    result["phase9f"], phase9f_table = phase9f_summary(packages)
    lines.append(phase9f_table)
    return result, "\n".join(lines)


def compact_phase9f(raw: object, redactor: RedactingFilter) -> dict:
    """Only known source-free metrics survive historical compact reloading."""
    keys = set(
        (
            "measured catalogue templates partial_groups "
            "existing_file_proposals fixer_calls fixer_configurations "
            "generator_checklist_chars generator_context_truncated "
            "generation_syntax iteration_timings deadline_phases control "
            "resource status reason rules template introduced_rules normalized"
            " retained model provider reasoning findings resources path "
            "normalizations rounds regeneration fix_attempt_timeout_seconds "
            "iteration_timeout_seconds security_stage_timeout_seconds "
            "fix_max_resources fix_max_findings partial_max_groups kept "
            "discarded unevaluated unknown scan_seconds construction_seconds "
            "syntax_verification_seconds terraform_verification_seconds "
            "security_verification_seconds cancellation_seconds "
            "restoration_seconds publication_seconds iteration_elapsed_seconds"
            " deadline_overrun_seconds fault_recovery_seconds "
            "complete_iteration workspace event_publication "
            "closing_state_event"
        ).split()
    )

    def clean(value):
        if isinstance(value, dict):
            return {
                key: clean(item)
                for key, item in value.items()
                if key in keys
                or re.fullmatch(r"(?:CKV[A-Z0-9_]*|AWS-[0-9]+|KSV-[0-9]+)", key)
            }
        if isinstance(value, list):
            return [clean(item) for item in value]
        if isinstance(value, str):
            return safe_text(value, redactor)
        return value if value is None or type(value) in {bool, int, float} else None

    return clean(raw) if isinstance(raw, dict) else {}


def compact_snapshot(raw: dict, redactor: RedactingFilter) -> dict:
    """Re-allowlist saved compact data without discarding measured extensions."""
    extra = raw.get("phase9e", {})
    # Re-allowlist historical compact data before exporting it.
    pseudo = {
        "status": raw.get("status"),
        "legacy_label_mapped": raw.get("legacy_label_mapped") is True,
        "review_reasons": raw.get("review_reasons", []),
        "validation_report": {
            "summary": {"result": raw.get("validation_result")},
            "checks": [{**c, "status": "failed"} for c in raw.get("failed_checks", [])],
            "remediation": {
                **generation_metrics(extra),
                "initialization": extra.get("initialization"),
                "generator_schema_context_chars": extra.get(
                    "generator_schema_context_chars"
                ),
                "rounds": extra.get("repair_rounds", []),
                "measurements": extra.get("measurements", []),
                "gate": {
                    "outcome": extra.get("gate_outcome"),
                    "failed_checks": extra.get("gate_failed_checks", []),
                    "terraform": [
                        {"init_outcome": c} for c in extra.get("init_categories", [])
                    ],
                },
            },
        },
        "security_report": {
            "iterations": [
                *[
                    {"verification": v}
                    for v in extra.get("security_iteration_repairs", [])
                ],
                {
                    "fixes": [
                        {
                            "schema_context_chars": r.get("chars"),
                            "schema_context_reason": r.get("reason"),
                            "file": "terraform/context.tf"
                            if r.get("file_type") == "terraform"
                            else "other"
                            if r.get("file_type") == "other"
                            else None,
                        }
                        for r in extra.get("security_context_measurements", [])
                    ]
                    if "security_context_measurements" in extra
                    else [
                        {"schema_context_chars": n}
                        for n in extra.get("security_schema_context_chars", [])
                    ]
                },
            ],
            "final": {
                "outcome": "clean"
                if raw.get("status") == "checks_passed"
                else "exhausted",
                "remaining_blocking": [
                    {"rule_id": rule}
                    for rule, count in raw.get("remaining_findings", {}).items()
                    for _ in range(count)
                ],
            },
        },
    }
    result = quality_snapshot(pseudo, redactor)
    result["fixer_attempts"] = compact_evidence(raw.get("fixer_attempts"))
    for key in result["counts"]:
        value = raw.get("counts", {}).get(key)
        if type(value) is int and value >= 0:
            result["counts"][key] = value
    result["phase9f"] = compact_phase9f(raw.get("phase9f"), redactor)
    if (
        raw.get("status") == "production_ready"
        and raw.get("validation_result") == "valid"
        and not raw.get("remaining_findings")
    ):
        result["status"] = "checks_passed"
    profiles = raw.get("profile_assessments", {})
    result["profile_assessments"] = {}
    for name in PROFILE_IDS:
        view = profiles.get(name)
        if not isinstance(view, dict):
            continue
        result["profile_assessments"][name] = {
            "checks_passed": view.get("checks_passed") is True,
            "remaining_blocking": max(0, view.get("remaining_blocking", 0)),
            "excepted": [
                {
                    key: safe_text(entry[key], redactor)
                    for key in (
                        "rule_id",
                        "file_path",
                        "resource",
                        "classification",
                        "entry_id",
                        "justification",
                    )
                    if key in entry
                }
                for entry in view.get("excepted", [])
            ],
        }
    return result


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
            missing += max(0, 3 - len(snapshot.get("packages", [])))
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
                    current[variant] = compact_snapshot(raw, redactor)
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
