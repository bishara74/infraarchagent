"""Bounded, redacted facts about the previous candidate, never current failures."""

import json
from typing import Any

from app.core.logging import RedactingFilter

MAX_ATTEMPT_FEEDBACK = 4000


def attempt_feedback(
    record: dict[str, Any], fixes: list[dict[str, Any]], redactor: RedactingFilter
) -> str:
    data: dict[str, Any] = {"outcome": str(record.get("outcome", "unknown"))[:40]}
    # Keep complete JSON entries; never copy source, diffs, or model summaries.
    for key, entries in (
        ("reasons", record.get("reasons", [])),
        ("rejected_candidate_error_classes", record.get("error_classes", [])),
        (
            "rejected_patches",
            [
                {
                    "file": f.get("file"),
                    "reason": f.get("reason"),
                    "conflicting_paths": ", ".join(f.get("conflicting_paths", [])),
                }
                for f in fixes
                if not f.get("accepted")
            ],
        ),
    ):
        data[key] = []
        for entry in entries:
            safe = (
                {k: redactor.redact(str(v))[:255] for k, v in entry.items()}
                if isinstance(entry, dict)
                else redactor.redact(str(entry))[:500]
            )
            trial = {**data, key: [*data[key], safe]}
            if len(json.dumps(trial, ensure_ascii=True)) > MAX_ATTEMPT_FEEDBACK - 150:
                break
            data = trial
    if record.get("outcome") == "accepted" and not data.get("rejected_patches"):
        return ""
    return json.dumps(data, ensure_ascii=True)
