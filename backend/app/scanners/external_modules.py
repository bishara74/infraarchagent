"""Expose the coverage gap for literal remote Terraform module sources."""

import json
import re
from collections.abc import Mapping

from app.domain.enums import Severity
from app.domain.models import Violation

# Preserve quoted strings as one token, discard comments and heredoc bodies.
TOKENS = re.compile(
    r'(?P<comment>\#[^\n]*|//[^\n]*|/\*.*?\*/)|(?P<heredoc><<-?(\w+)[^\n]*\n.*?^\s*\3\s*$)|(?P<string>"(?:\\.|[^"\\])*")|(?P<word>[\w-]+)|(?P<punct>[{}=])',
    re.S | re.M,
)


def external_module_findings(files: Mapping[str, str]) -> list[Violation]:
    findings = []
    for path, content in files.items():
        if not path.startswith("terraform/") or not path.endswith(".tf"):
            continue
        tokens = [
            m
            for m in TOKENS.finditer(content)
            if m.lastgroup not in {"comment", "heredoc"}
        ]
        depth = 0
        index = 0
        while index < len(tokens):
            token = tokens[index]
            value = token.group()
            if (
                depth == 0
                and value == "module"
                and index + 2 < len(tokens)
                and tokens[index + 1].lastgroup == "string"
                and tokens[index + 2].group() == "{"
            ):
                try:
                    name = json.loads(tokens[index + 1].group())
                except ValueError:
                    index += 1
                    continue
                cursor, module_depth = index + 3, 1
                while cursor < len(tokens) and module_depth:
                    current = tokens[cursor]
                    text = current.group()
                    if (
                        module_depth == 1
                        and text == "source"
                        and cursor + 2 < len(tokens)
                        and tokens[cursor + 1].group() == "="
                        and tokens[cursor + 2].lastgroup == "string"
                    ):
                        try:
                            source = json.loads(tokens[cursor + 2].group())
                        except ValueError:
                            source = None
                        if isinstance(source, str) and not source.startswith(
                            ("./", "../", "/")
                        ):
                            findings.append(
                                Violation(
                                    tool="trivy",
                                    rule_id="EXTERNAL_MODULE_NOT_SCANNED",
                                    severity=Severity.LOW,
                                    file_path=path,
                                    resource="module." + name,
                                    line_start=content.count("\n", 0, current.start())
                                    + 1,
                                    line_end=content.count("\n", 0, current.start())
                                    + 1,
                                    title="External module not scanned",
                                    message=(
                                        "Remote Terraform module contents are "
                                        "unavailable to the offline scanner."
                                    ),
                                )
                            )
                    module_depth += (text == "{") - (text == "}")
                    cursor += 1
                index = cursor
                continue
            depth += (value == "{") - (value == "}")
            index += 1
    return findings
