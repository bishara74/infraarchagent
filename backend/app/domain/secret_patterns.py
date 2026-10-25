"""Shared offline credential heuristics; findings never contain matched values."""

import re

PATTERNS = (
    ("openrouter", re.compile(r"\bsk-or-[A-Za-z0-9_-]{16,}")),
    ("anthropic", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}")),
    ("openai", re.compile(r"\bsk-(?!or-|ant-)[A-Za-z0-9_-]{16,}")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    (
        "private_key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"
        ),
    ),
)
ASSIGNMENT = re.compile(
    r"""\b(?:[A-Z][A-Z0-9_]*_)?API_KEY[ \t]*=[ \t]*"""
    r"""(?:"([^"\r\n]*)"|'([^'\r\n]*)'|([^\s#'";]+))"""
)
TOKEN = re.compile(r"[A-Za-z0-9_+/=-]{16,}")
