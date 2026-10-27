"""Trusted assembly of the Fixer's nonce-delimited network/advisory context."""

import json
import re
from typing import Any


def fixer_context(network: dict[str, Any], marker: str) -> str:
    return (
        f'<fixer_advisory id="{marker}">\n'
        + json.dumps({"network": network}, ensure_ascii=True, sort_keys=True)
        + f'\n</fixer_advisory id="{marker}">'
    )


def with_fixer_lessons(prompt: str, block: str) -> str:
    """Insert only at the trusted final delimiter, never at a source substring.

    Production markers are 128-bit nonces, constructed after all untrusted text.
    Fixed output-repair diagnostics may follow the context on corrective attempts.
    Missing/malformed assembly fails closed before lesson authorization/dispatch.
    """
    matches = list(re.finditer(r'\n</fixer_advisory id="([a-f0-9]{32})">', prompt))
    if not matches:
        raise ValueError("Fixer advisory context unavailable")
    match = matches[-1]
    marker = match[1]
    if prompt.count(f'<fixer_advisory id="{marker}">') != 1:
        raise ValueError("Fixer advisory context ambiguous")
    return prompt[: match.start()] + "\n" + block + prompt[match.start() :]
