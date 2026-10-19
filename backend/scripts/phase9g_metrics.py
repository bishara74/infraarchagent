"""Safe fixer-attempt evidence across security, validation and syntax repair."""

from collections import Counter

from app.domain.review import security_iterations
from scripts.phase9c_metrics import attempt_details


def fixer_evidence(package: dict) -> dict:
    """Missing historical/cancelled-call telemetry is unknown, never zero."""
    calls = []
    for iteration in security_iterations(package.get("security_report")):
        for fix in iteration.get("fixes", []):
            if fix.get("call_attempted") is False:
                continue
            calls.append(("security_fixer", fix.get("attempt_details")))
    remediation = (package.get("validation_report") or {}).get("remediation") or {}
    for repair in remediation.get("rounds", []):
        if repair.get("attempted"):
            calls.append(("validation_repair", repair.get("fixer_attempts")))
    syntax = remediation.get("generation_syntax") or {}
    for repair in syntax.get("rounds", []):
        for action in repair.get("actions", []):
            calls.append(("syntax_repair", action.get("attempt_details")))
    details = []
    missing = 0
    for kind, raw in calls:
        clean = attempt_details(raw)
        if not clean:
            missing += 1
        details.extend({"call_kind": kind, **a} for a in clean or [])
    return {
        "attempt_count": len(details) if calls and not missing else None,
        "unmeasured_calls_or_rounds": missing if calls else None,
        "attempt_details": details or None,
        "outcomes": dict(Counter(a["outcome"] for a in details)) or None,
        "format_reasons": dict(Counter(a["format_reason"] or "none" for a in details))
        or None,
    }


def compact_evidence(raw: object) -> dict:
    """Re-allowlist saved compact telemetry before exporting it again."""
    from scripts.phase9c_metrics import integer

    data = raw if isinstance(raw, dict) else {}
    details = []
    for item in data.get("attempt_details") or []:
        if isinstance(item, dict) and item.get("call_kind") in {
            "security_fixer",
            "validation_repair",
            "syntax_repair",
        }:
            details.extend(
                {"call_kind": item["call_kind"], **a}
                for a in attempt_details([item]) or []
            )
    return {
        "attempt_count": len(details)
        if integer(data.get("attempt_count")) == len(details) and details
        else None,
        "unmeasured_calls_or_rounds": integer(data.get("unmeasured_calls_or_rounds")),
        "attempt_details": details or None,
        "outcomes": dict(Counter(a["outcome"] for a in details)) or None,
        "format_reasons": dict(Counter(a["format_reason"] or "none" for a in details))
        or None,
    }
