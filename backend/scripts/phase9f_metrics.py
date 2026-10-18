"""Allowlisted Phase 9f quality evidence; never copy source, diffs or summaries."""

from collections import Counter

from app.core.logging import REDACTED, RedactingFilter
from app.domain.review import security_iterations
from scripts.phase9_common import ROOT
from scripts.phase9_report import statistics_for
from scripts.phase9c_metrics import number

LIMITS = (
    "fix_attempt_timeout_seconds",
    "iteration_timeout_seconds",
    "security_stage_timeout_seconds",
    "fix_max_resources",
    "fix_max_findings",
    "partial_max_groups",
)
STATUSES = {"proposed", "retained", "rejected", "skipped"}


def count(value):
    return value if type(value) is int and value >= 0 else None


def snapshot(package: dict, redactor: RedactingFilter) -> dict:
    def safe(value):
        return (
            redactor.redact(value).replace(str(ROOT), REDACTED)[:255]
            if isinstance(value, str)
            else None
        )

    report = package.get("security_report") or {}
    raw_sessions = report.get("sessions")
    sessions = raw_sessions if isinstance(raw_sessions, list) else [report]
    configurations, calls = [], []
    measured = False
    for session in sessions:
        if not isinstance(session, dict):
            continue
        measured |= "fix_max_findings" in session
        model = safe(session.get("fixing_model"))
        configurations.append(
            {
                "model": model,
                "provider": safe(session.get("fixing_provider")),
                "reasoning": safe(session.get("fixing_reasoning_effort")),
                **{
                    key: session[key]
                    if type(session.get(key)) in {int, float}
                    and 0 < session[key] < float("inf")
                    else None
                    for key in LIMITS
                },
            }
        )
        for iteration in session.get("iterations", []):
            for fix in iteration.get("fixes", []):
                if (
                    fix.get("call_attempted") is False
                    or fix.get("schema_context_reason") == "not_attempted"
                ):
                    continue
                calls.append(
                    {
                        "model": model,
                        "findings": count(fix.get("findings_sent")),
                        "resources": count(fix.get("resources_sent")),
                    }
                )
    catalogue, templates = [], []
    groups: Counter[str] = Counter()
    normalized = recovered = 0
    for iteration in security_iterations(report):
        verification = iteration.get("verification") or {}
        measured |= "catalogue" in verification
        for entry in verification.get("catalogue", []):
            catalogue.append(
                {
                    "control": safe(entry.get("control")),
                    "resource": safe(entry.get("resource")),
                    "status": entry.get("status")
                    if entry.get("status") in STATUSES
                    else "unknown",
                    "reason": safe(entry.get("reason")),
                    "rules": [
                        safe(r) for r in entry.get("rule_ids", []) if isinstance(r, str)
                    ],
                }
            )
        for entry in verification.get("templates", []):
            templates.append(
                {
                    "template": safe(entry.get("template")),
                    "status": entry.get("status")
                    if entry.get("status") in STATUSES
                    else "unknown",
                    "reason": safe(entry.get("reason")),
                    "introduced_rules": dict(
                        Counter(
                            safe(f.get("rule_id"))
                            for f in entry.get("introduced_findings", [])
                            if isinstance(f.get("rule_id"), str)
                        )
                    ),
                }
            )
        groups.update(
            entry.get("status")
            if entry.get("status") in {"kept", "discarded", "unevaluated"}
            else "unknown"
            for entry in verification.get("partial_groups", [])
        )
        for fix in iteration.get("fixes", []):
            normalized += bool(fix.get("normalized_existing_paths"))
            recovered += fix.get("recovered_existing_proposal") is True
    remediation = (package.get("validation_report") or {}).get("remediation") or {}
    raw_syntax = remediation.get("generation_syntax")
    syntax = raw_syntax if isinstance(raw_syntax, dict) else {}
    syntax_path = syntax.get("path")
    syntax_paths = {
        "unchanged",
        "normalization",
        "syntax_round_1",
        "syntax_round_2",
        "regeneration",
        "unresolved",
        "deadline",
    }
    return {
        "measured": measured,
        "catalogue": catalogue,
        "templates": templates,
        "partial_groups": dict(groups) if measured else None,
        "existing_file_proposals": {"normalized": normalized, "retained": recovered}
        if measured
        else None,
        "fixer_calls": calls,
        "fixer_configurations": configurations,
        "generator_checklist_chars": count(
            remediation.get("generator_security_context_chars")
        ),
        "generator_context_truncated": remediation.get("generator_context_truncated")
        if type(remediation.get("generator_context_truncated")) is bool
        else None,
        "generation_syntax": {
            "path": syntax_path
            if isinstance(syntax_path, str) and syntax_path in syntax_paths
            else None,
            "normalizations": len(syntax.get("normalizations", [])) if syntax else None,
            "rounds": len(syntax.get("rounds", [])) if syntax else None,
            "regeneration": syntax.get("regeneration")
            if isinstance(syntax.get("regeneration"), str)
            and syntax.get("regeneration")
            in {
                "not_needed",
                "attempted",
                "accepted",
                "unparsable",
                "deadline",
                "failed",
            }
            else None,
        },
        "iteration_timings": [
            {
                key: number((it.get("verification") or {}).get(key))
                for key in (
                    "scan_seconds",
                    "construction_seconds",
                    "syntax_verification_seconds",
                    "terraform_verification_seconds",
                    "security_verification_seconds",
                    "cancellation_seconds",
                    "restoration_seconds",
                    "publication_seconds",
                    "iteration_elapsed_seconds",
                    "deadline_overrun_seconds",
                    "fault_recovery_seconds",
                )
            }
            for it in security_iterations(report)
        ],
        "deadline_phases": [
            {
                key: number(
                    (it.get("verification", {}).get("deadline_timings") or {}).get(key)
                )
                for key in (
                    "complete_iteration",
                    "workspace",
                    "event_publication",
                    "closing_state_event",
                )
            }
            for it in security_iterations(report)
        ],
    }


def summary(packages: list[dict]) -> tuple[dict, str]:
    measured = [p["phase9f"] for p in packages if p.get("phase9f", {}).get("measured")]
    near_misses = {"1": 0, "2-3": 0, "4+": 0}
    for package in packages:
        n = sum(package["remaining_findings"].values())
        if package.get("validation_result") == "valid" and n:
            near_misses["1" if n == 1 else "2-3" if n <= 3 else "4+"] += 1
    catalogue = Counter(
        r
        for p in measured
        for e in p["catalogue"]
        if e["status"] == "retained"
        for r in e["rules"]
    )
    template_statuses = Counter(
        (e["template"], e["status"]) for p in measured for e in p["templates"]
    )
    introduced: Counter[str] = Counter()
    partial: Counter[str] = Counter()
    for p in measured:
        partial.update(p["partial_groups"] or {})
        for e in p["templates"]:
            introduced.update(e["introduced_rules"])
    configurations = [
        c
        for p in packages
        for c in p.get("phase9f", {}).get("fixer_configurations", [])
    ]
    models = sorted({c["model"] for c in configurations if c.get("model")})
    model_rows = []
    for model in models:
        selected = [c for c in configurations if c["model"] == model]
        calls = [
            c
            for p in packages
            for c in p.get("phase9f", {}).get("fixer_calls", [])
            if c.get("model") == model
        ]
        model_rows.append(
            {
                "model": model,
                "sessions": len(selected),
                **{
                    key: sorted({c[key] for c in selected if c.get(key) is not None})
                    for key in LIMITS
                },
                "findings_per_call": statistics_for(
                    [c["findings"] for c in calls if c["findings"] is not None]
                ),
                "calls_missing_measurements": sum(c["findings"] is None for c in calls),
            }
        )
    result = {
        "generation_syntax_paths": dict(
            Counter(
                p.get("phase9f", {}).get("generation_syntax", {}).get("path")
                or "unknown"
                for p in packages
            )
        ),
        "packages_measured": len(measured),
        "packages_unknown": len(packages) - len(measured),
        "near_misses": near_misses,
        "validation_unknown": sum(p.get("validation_result") is None for p in packages),
        "catalogue_retained_by_rule": dict(catalogue),
        "template_outcomes": [
            {"template": k[0], "status": k[1], "count": n}
            for k, n in sorted(template_statuses.items())
        ],
        "template_introduced_rules": dict(introduced),
        "partial_groups": dict(partial),
        "existing_file_proposals": {
            key: sum(p["existing_file_proposals"][key] for p in measured)
            for key in ("normalized", "retained")
        },
        "fixer_models": model_rows,
    }
    lines = ["", "| Valid package remaining blockers | Packages |", "|---|---:|"]
    lines.extend(f"| {key} | {value} |" for key, value in near_misses.items())
    lines += [
        "",
        "Phase 9f measured/unknown packages: "
        + str((len(measured), len(packages) - len(measured))),
        "Catalogue retained by rule: " + str(dict(catalogue)),
        "Template outcomes: " + str(result["template_outcomes"]),
        "Template introduced rules: " + str(dict(introduced)),
        "Partial groups: " + str(dict(partial)),
        "Existing-file proposal recovery: " + str(result["existing_file_proposals"]),
        "Generation syntax recovery: " + str(result["generation_syntax_paths"]),
        "Fixer model limits and calls: " + str(model_rows),
    ]
    return result, "\n".join(lines)
