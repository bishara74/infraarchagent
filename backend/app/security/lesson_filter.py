"""Deterministic proposal/approval screening, never an LLM safety verdict."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from app.domain.secret_patterns import ASSIGNMENT, PATTERNS


@lru_cache(maxsize=2)
def configuration(version: str = "2") -> dict[str, Any]:
    if version not in {"1", "2"}:
        raise ValueError("Unknown lesson filter version")
    return cast(
        dict[str, Any],
        json.loads(
            Path(__file__).with_name(f"lesson-filter.v{version}.json").read_text()
        ),
    )


def screen(text: str, *, version: str = "2") -> dict[str, Any]:
    config = configuration(version)
    folded = text.casefold().translate(str.maketrans(config["confusables"]))
    reasons = [
        {"id": rule["id"], "message": rule["message"]}
        for rule in config["rules"]
        if re.search(rule["pattern"], folded, re.IGNORECASE)
    ]
    if any(pattern.search(text) for _, pattern in PATTERNS) or ASSIGNMENT.search(text):
        reasons.append(
            {"id": "secret", "message": "Remove possible credentials or secrets."}
        )
    return {"version": config["version"], "passed": not reasons, "reasons": reasons}
