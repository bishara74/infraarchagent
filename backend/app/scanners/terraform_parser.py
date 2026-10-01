"""Filter validate diagnostics to demonstrated HCL/configuration-loading errors.

No init is performed. Missing providers/modules, references, defaults and schema
validation are deliberately outside this syntax gate (Phase 6 owns validation).
"""

import json
from pathlib import Path

from app.domain.enums import Severity
from app.domain.models import Violation
from app.scanners.paths import scanner_path

SYNTAX_SUMMARIES = frozenset(
    {
        "Invalid block definition",
        "Invalid single-argument block definition",
        "Unclosed configuration block",
        "Argument or block definition required",
        "Missing newline after argument",
        "Invalid expression",
        "Missing expression",
        "Unsupported block type",
        "Duplicate argument",
        "Attribute redefined",
        "Duplicate attribute definition",
        "Invalid character",
        "Unterminated template string",
        "Invalid multi-line string",
    }
)
SYNTAX_PREFIXES = ("Extraneous label for ", "Missing name for ")
CORE_CONTEXTS = (
    "variable ",
    "output ",
    "locals",
    "terraform",
    "module ",
    "provider ",
    "check ",
    "import ",
    "moved ",
    "removed ",
)


def parse_terraform(output: str, root: Path, files: set[str]) -> list[Violation]:
    try:
        data = json.loads(output)
        if not isinstance(data, dict) or not isinstance(data.get("diagnostics"), list):
            raise ValueError
        violations = []
        for diagnostic in data["diagnostics"]:
            if not isinstance(diagnostic, dict):
                raise ValueError
            summary = diagnostic.get("summary", "")
            if not isinstance(summary, str):
                raise ValueError
            if diagnostic.get("severity") != "error" or not (
                summary in SYNTAX_SUMMARIES or summary.startswith(SYNTAX_PREFIXES)
            ):
                continue
            if summary == "Unsupported block type":
                snippet = diagnostic.get("snippet") or {}
                context = snippet.get("context")
                # This summary is also used by resource/provider schema checks.
                # Only a top-level or known Terraform-language context is syntax.
                if "context" not in snippet or (
                    context is not None and not str(context).startswith(CORE_CONTEXTS)
                ):
                    continue
                if context is not None and str(context).startswith("provider "):
                    continue
            location = diagnostic.get("range")
            if not location:
                continue
            raw_path = location["filename"]
            candidate = Path(raw_path)
            if not candidate.is_absolute():
                raw_path = "terraform/" + raw_path.removeprefix("./")
            path = scanner_path(raw_path, root, files)
            violations.append(
                Violation(
                    tool="terraform",
                    rule_id="TERRAFORM_SYNTAX",
                    severity=Severity.CRITICAL,
                    file_path=path,
                    resource="",
                    message="Terraform configuration cannot be parsed or loaded: "
                    + summary,
                    title=summary[:200],
                    line_start=location["start"]["line"],
                    line_end=location["end"]["line"],
                )
            )
        return violations
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise ValueError("invalid Terraform JSON") from error
