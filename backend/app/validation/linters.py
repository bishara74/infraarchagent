"""Pluggable optional linters using recorded, narrowly supported output formats."""

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath

from app.domain.plan import FileType
from app.domain.validation import CheckStatus, ValidationCheck, ValidationTool
from app.scanners.paths import scanner_path
from app.scanners.runner import CommandToolRunner, ToolFailure, ToolResult
from app.validation.documents import PackageDocuments, mapping, walk
from app.validation.references import safe_reference


@dataclass(frozen=True)
class LinterTarget:
    tool: ValidationTool
    path: str
    file_path: str
    args: tuple[str, ...]
    safe_to_run: bool = True


def safe_inputs(package: PackageDocuments, target: LinterTarget) -> bool:
    """Refuse file-reading inputs outside the copy and dynamic Ansible lookups."""
    docs = (
        package.of_kind(FileType.ANSIBLE)
        if target.tool == "ansible-lint"
        else [package.documents[target.file_path]]
    )
    if target.tool not in {"ansible-lint", "promtool"}:
        return True
    for doc in docs:
        for path, value in walk(doc.data):
            if (
                isinstance(value, str)
                and target.tool == "ansible-lint"
                and re.search(r"\b(?:lookup|query)\s*\(", value)
            ):
                return False
            key = str(path[-1])
            file_key = (
                key in {"vars_files", "include_tasks", "import_tasks", "include_vars"}
                if target.tool == "ansible-lint"
                else key.endswith("_file")
                or key == "rule_files"
                or (key == "files" and "file_sd_configs" in path)
            )
            if not file_key:
                continue
            values = value if isinstance(value, list) else [value]
            for candidate in values:
                if isinstance(candidate, dict):
                    candidate = candidate.get("file", candidate.get("dir"))
                if not isinstance(candidate, str) or "{{" in candidate:
                    return False
                normalized = safe_reference(
                    str(PurePosixPath(doc.path).parent), candidate
                )
                if normalized is None or any(
                    part.startswith(".env") for part in PurePosixPath(normalized).parts
                ):
                    return False
    return True


def linter_targets(package: PackageDocuments) -> list[LinterTarget]:
    targets = []
    for doc in package.documents.values():
        if doc.kind == FileType.HELM and PurePosixPath(doc.path).name == "Chart.yaml":
            chart = str(PurePosixPath(doc.path).parent)
            targets.append(
                LinterTarget(
                    "helm",
                    chart,
                    doc.path,
                    ("helm", "lint", chart, "--skip-schema-validation"),
                )
            )
        elif doc.kind == FileType.DOCKERFILE:
            targets.append(
                LinterTarget(
                    "hadolint",
                    doc.path,
                    doc.path,
                    ("hadolint", "--format", "json", doc.path),
                )
            )
        elif doc.kind == FileType.PROMETHEUS and isinstance(doc.data, dict):
            rules = "groups" in doc.data and "scrape_configs" not in doc.data
            mode = "rules" if rules else "config"
            targets.append(
                LinterTarget(
                    "promtool",
                    doc.path,
                    doc.path,
                    ("promtool", "check", mode, doc.path),
                )
            )
    ansible = [
        doc
        for doc in package.of_kind(FileType.ANSIBLE)
        if isinstance(doc.data, list)
        and "/roles/" not in doc.path
        and any(isinstance(play, dict) and "hosts" in play for play in doc.data)
    ]
    if ansible:
        paths = tuple(doc.path for doc in ansible)
        targets.append(
            LinterTarget(
                "ansible-lint",
                "ansible",
                paths[0],
                (
                    "ansible-lint",
                    "--offline",
                    "--nocolor",
                    "-f",
                    "json",
                    "--project-dir",
                    "ansible",
                    *paths,
                ),
            )
        )
    return [
        replace(target, safe_to_run=safe_inputs(package, target)) for target in targets
    ]


def lint_check(
    target: LinterTarget,
    status: CheckStatus,
    *,
    file_path: str | None = None,
    line: int = 1,
    reason: str | None = None,
    code: str | None = None,
) -> ValidationCheck:
    label = f"{target.tool} optional lint {status}"
    if code:
        label += f" ({code})"
    return ValidationCheck(
        check_id=f"{target.tool}.lint",
        category="lint",
        tool=target.tool,
        status=status,
        file_path=file_path or target.file_path,
        line_start=line,
        message=label,
        skip_reason=reason,
    )


def lint_location(
    raw: object, root: Path, files: set[str], target: LinterTarget
) -> str:
    if raw is None:
        return target.file_path
    if not isinstance(raw, str):
        raise ValueError("invalid linter path")
    try:
        return scanner_path(raw, root, files)
    except ValueError:
        if Path(raw).is_absolute() or ".." in PurePosixPath(raw).parts or "\\" in raw:
            raise ValueError("unsafe linter path") from None
        base = (
            target.path
            if target.tool in {"helm", "ansible-lint"}
            else str(PurePosixPath(target.file_path).parent)
        )
        return scanner_path(base + "/" + raw, root, files)


def lint_line(raw: object) -> int:
    if raw is None:
        return 1
    if type(raw) is not int or raw < 1:
        raise ValueError("invalid linter line")
    return raw


def parse_lint(
    target: LinterTarget, result: ToolResult, root: Path, files: set[str]
) -> list[ValidationCheck]:
    if result.exit_code < 0:
        raise ValueError("linter crashed")
    checks = []
    if target.tool in {"hadolint", "ansible-lint"}:
        data = json.loads(result.stdout)
        if not isinstance(data, list):
            raise ValueError("invalid linter JSON shape")
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("invalid linter issue")
            if target.tool == "hadolint":
                severity = item.get("level")
                raw_path = item.get("file")
                raw_line = item.get("line")
                code = item.get("code")
                code = (
                    code
                    if isinstance(code, str) and re.fullmatch(r"(?:DL|SC)\d{4}", code)
                    else None
                )
                if severity not in {"error", "warning", "info", "style"}:
                    raise ValueError("unknown hadolint severity")
                status: CheckStatus = "failed" if severity == "error" else "warning"
            else:
                severity = item.get("severity")
                if severity not in {
                    "blocker",
                    "critical",
                    "major",
                    "minor",
                    "info",
                    "error",
                    "warning",
                    "note",
                }:
                    raise ValueError("unknown ansible severity")
                status = (
                    "failed"
                    if severity in {"blocker", "critical", "major", "error"}
                    else "warning"
                )
                location = mapping(item.get("location"))
                raw_path = location.get("path")
                raw_line = mapping(mapping(location.get("positions")).get("begin")).get(
                    "line", mapping(location.get("lines")).get("begin")
                )
                code = None
            checks.append(
                lint_check(
                    target,
                    status,
                    file_path=lint_location(raw_path, root, files, target),
                    line=lint_line(raw_line),
                    code=code,
                )
            )
        if result.exit_code != 0 and not checks:
            raise ValueError("nonzero linter without diagnostics")
    elif target.tool == "helm":
        output = result.stdout + "\n" + result.stderr
        helper = re.search(r'no template "([a-zA-Z0-9_.-]{1,128})" associated', output)
        template_location = None
        for candidate in sorted(files):
            if not candidate.startswith(target.path + "/templates/"):
                continue
            match = re.search(
                re.escape(candidate.removeprefix("helm/")) + r":(\d+)(?::\d+)?", output
            )
            if match:
                template_location = (candidate, int(match[1]))
                break
        for line in output.splitlines():
            match = re.search(r"\[(ERROR|WARNING|INFO)\]\s*(.*)", line)
            if not match:
                continue
            severity, text = match.groups()
            helm_location = re.match(r"([^:]+\.(?:ya?ml|tpl|json))(?::(\d+))?:", text)
            raw_path = helm_location.group(1) if helm_location else None
            raw_line = (
                int(helm_location.group(2))
                if helm_location and helm_location.group(2)
                else None
            )
            check = lint_check(
                target,
                "failed" if severity == "ERROR" else "warning",
                file_path=template_location[0]
                if severity == "ERROR" and template_location
                else lint_location(raw_path, root, files, target),
                line=template_location[1]
                if severity == "ERROR" and template_location
                else lint_line(raw_line),
                code="undefined_named_template"
                if severity == "ERROR" and helper
                else None,
            )
            if severity == "ERROR" and helper:
                check = check.model_copy(update={"template_name": helper[1]})
            checks.append(check)
        if result.exit_code != 0 and not any(
            check.status == "failed" for check in checks
        ):
            raise ValueError("unusable Helm output")
        if result.exit_code == 0 and "chart(s) linted" not in result.stdout:
            raise ValueError("unusable Helm output")
    elif target.tool == "promtool":
        output = result.stdout + "\n" + result.stderr
        if result.exit_code == 0:
            if "SUCCESS" not in output:
                raise ValueError("unusable promtool output")
        else:
            if not re.search(r"FAILED|(?:Error|error):", output):
                raise ValueError("unusable promtool output")
            reported = re.search(
                r"(?:parsing (?:YAML )?file|Checking)\s+([^\s]+?\.ya?ml)\b", output
            )
            if reported is not None:
                lint_location(reported.group(1), root, files, target)
            line_match = re.search(r"\bline (\d+)\b", output)
            path = next(
                (
                    path
                    for path in sorted(files, key=len, reverse=True)
                    if path in output
                ),
                target.file_path,
            )
            checks.append(
                lint_check(
                    target,
                    "failed",
                    file_path=path,
                    line=int(line_match.group(1)) if line_match else 1,
                )
            )
    if not checks:
        checks.append(lint_check(target, "passed"))
    return checks


async def run_linter(
    target: LinterTarget, root: Path, files: set[str], runner: CommandToolRunner
) -> list[ValidationCheck]:
    if not target.safe_to_run:
        return [lint_check(target, "skipped", reason="tool_error")]
    try:
        # Builtin never has an external target; this narrows the runner literal.
        if target.tool not in {"helm", "hadolint", "ansible-lint", "promtool"}:
            raise ValueError("unsupported linter")
        result = await runner.run_command(target.tool, list(target.args), root)
        return parse_lint(target, result, root, files)
    except ToolFailure as error:
        return [
            lint_check(
                target,
                "skipped",
                reason="not_installed"
                if error.category == "not_installed"
                else "tool_error",
            )
        ]
    except (ValueError, TypeError, KeyError, AttributeError):
        return [lint_check(target, "skipped", reason="tool_error")]
