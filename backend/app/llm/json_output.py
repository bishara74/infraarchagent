"""JSON boundaries and schema-validated salvage, without retaining response text."""

import json
import re
from collections.abc import Callable
from typing import Any

from app.llm.errors import LLMResponseFormatError

FENCE = re.compile(r"```(?:json)?[ \t]*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
Validator = Callable[[dict[str, Any]], dict[str, Any]]


def boundaries(text: str) -> tuple[list[tuple[int, int]], int]:
    """Find root objects and fence delimiters outside JSON string values."""
    objects: list[tuple[int, int]] = []
    stack: list[str] = []
    quoted = escaped = False
    start = fences = index = 0
    while index < len(text):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"' and stack:
            quoted = True
        elif text.startswith("```", index):
            fences += 1
            index += 2
        elif char in "{[":
            if not stack:
                start = index
            stack.append(char)
        elif char in "}]" and stack:
            opening = stack.pop()
            if (opening, char) not in {("{", "}"), ("[", "]")}:
                raise LLMResponseFormatError("invalid_json")
            if not stack and opening == "{":
                objects.append((start, index + 1))
        index += 1
    return objects, fences


def extract_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if not candidate:
        raise LLMResponseFormatError("empty")
    # Parse before inspecting markdown: backticks in file contents are data.
    try:
        whole = json.loads(candidate)
    except json.JSONDecodeError:
        pass
    else:
        if not isinstance(whole, dict):
            raise LLMResponseFormatError("not_object")
        return whole
    _, fences = boundaries(candidate)
    if fences >= 4:
        raise LLMResponseFormatError("multiple_blocks")
    fenced = FENCE.fullmatch(candidate)
    if fenced:
        candidate = fenced.group(1).strip()
    elif candidate.startswith("```"):
        raise LLMResponseFormatError("truncated" if fences == 1 else "prose_after")
    elif fences:
        raise LLMResponseFormatError("prose_before")
    if not candidate:
        raise LLMResponseFormatError("empty")
    if not candidate.startswith("{") and "{" in candidate:
        raise LLMResponseFormatError("prose_before")
    failure: LLMResponseFormatError | None = None
    try:
        parsed, end = json.JSONDecoder().raw_decode(candidate)
    except json.JSONDecodeError as error:
        incomplete = error.pos >= len(candidate) - 1 and any(
            part in error.msg
            for part in (
                "Unterminated",
                "Expecting value",
                "Expecting ',' delimiter",
                "Expecting property name",
            )
        )
        failure = LLMResponseFormatError(
            "truncated" if incomplete else f"syntax_error@{error.pos}"
        )
        failure.diagnostics(None, type(error).__name__)
    if failure is not None:
        raise failure from None
    if not isinstance(parsed, dict):
        raise LLMResponseFormatError("not_object")
    if candidate[end:].strip():
        raise LLMResponseFormatError("prose_after")
    return parsed


def validated_json(text: str, validate: Validator) -> tuple[dict[str, Any], str | None]:
    """Validate whole objects first; salvage only one unambiguous valid object."""
    try:
        data = extract_json_object(text)
    except LLMResponseFormatError as original:
        objects, fences = boundaries(text.strip())
        if len(objects) > 1 or fences >= 4:
            raise LLMResponseFormatError("multiple_blocks") from None
        if len(objects) != 1:
            raise original from None
        start, end = objects[0]
        data = extract_json_object(text.strip()[start:end])
        reason: str | None = "salvaged"
    else:
        reason = "salvaged" if text.strip().startswith("```") else None
    failed = False
    try:
        normalized = validate(data)
    except (ValueError, TypeError):
        failed = True
    if failed:
        raise LLMResponseFormatError("schema_invalid") from None
    return normalized, reason
