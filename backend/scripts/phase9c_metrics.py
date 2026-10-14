"""Strict allowlists for generator attempt evidence; never retain raw payloads."""

import math
from collections import Counter

from app.llm.errors import SAFE_MESSAGES, LLMResponseFormatError

FAILURES = set(SAFE_MESSAGES) | {"deadline", "incomplete_package", "generator_error"}
OUTCOMES = FAILURES | {"success", "cancelled", "invalid_json", "truncated", "timeout"}


def number(value):
    return (
        value
        if type(value) in {int, float} and math.isfinite(value) and value >= 0
        else None
    )


def integer(value):
    return value if type(value) is int and value >= 0 else None


def attempt_details(value):
    if not isinstance(value, list):
        return None
    rows = []
    for item in value:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("outcome"), str)
            or item.get("outcome") not in OUTCOMES
        ):
            continue
        reason = item.get("format_reason")
        reason = (
            LLMResponseFormatError(reason).reason if isinstance(reason, str) else None
        )
        rows.append(
            {
                "attempt": integer(item.get("attempt")),
                "package_attempt": integer(item.get("package_attempt")),
                "outcome": item["outcome"],
                "category": item.get("category")
                if isinstance(item.get("category"), str)
                and item.get("category") in OUTCOMES
                else None,
                "format_reason": reason,
                "elapsed_seconds": number(item.get("elapsed_seconds")),
                "input_tokens": integer(item.get("input_tokens")),
                "output_tokens": integer(item.get("output_tokens")),
                "response_characters": integer(item.get("response_characters")),
                "deadline_exceeded": item.get("deadline_exceeded")
                if type(item.get("deadline_exceeded")) is bool
                else None,
                "overrun_seconds": number(item.get("overrun_seconds")),
            }
        )
    return rows


def generator_evidence(events):
    """Prefer terminal metrics per variant, falling back to older success events."""
    chosen = {}
    for event in events:
        if not event["agent"].startswith("generator_"):
            continue
        if event["kind"] == "package_generated" and event["variant"] not in chosen:
            chosen[event["variant"]] = event
        elif event["kind"] == "agent_state" and event["status"] in {
            "completed",
            "failed",
        }:
            if event.get("metrics") or event.get("failure_category"):
                chosen[event["variant"]] = event
    details = []
    known = len(chosen) == 3
    failures = {}
    deadlines = {}
    for variant, event in chosen.items():
        metrics = event.get("metrics", {})
        attempts = metrics.get("llm_attempt_details")
        if attempts is None:
            known = False
        else:
            details.extend({"variant": variant, **attempt} for attempt in attempts)
        if event.get("failure_category"):
            failures[variant] = event["failure_category"]
        deadlines[variant] = {
            "deadline_exceeded": metrics.get("deadline_exceeded"),
            "overrun_seconds": metrics.get("overrun_seconds"),
            "generator_elapsed_seconds": metrics.get("elapsed_seconds"),
        }
    counts = dict(Counter(item["format_reason"] or "none" for item in details))
    return {
        "generator_attempt_count": len(details) if known else None,
        "generator_attempts_by_format_reason": counts if details else None,
        "generator_output_tokens_per_attempt": [
            {key: item[key] for key in ("variant", "attempt", "output_tokens")}
            for item in details
        ]
        if details
        else None,
        "generator_attempt_details": details if details else None,
        "generator_deadlines": deadlines,
        "failure_categories": failures,
    }
