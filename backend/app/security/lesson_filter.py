"""Deterministic proposal/approval screening, never an LLM safety verdict."""

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.secret_patterns import ASSIGNMENT, PATTERNS


@lru_cache(maxsize=1)
def configuration() -> dict[str, Any]:
    return json.loads(Path(__file__).with_name("lesson-filter.v1.json").read_text())  # type: ignore[no-any-return]


def screen(text: str) -> dict[str, Any]:
    config = configuration()
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
