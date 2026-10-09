"""Offline Terraform initialization and full provider-schema diagnostics."""

import json
import re
from pathlib import Path

import hcl2
from hcl2.utils import SerializationOptions
from lark.exceptions import LarkError

from app.domain.paths import validate_relative_path
from app.domain.validation import ValidationCheck
from app.scanners.runner import CommandToolRunner, ToolFailure
from app.validation.documents import PackageDocuments, walk
from app.validation.tools import DEFAULT_MIRROR, mirror_present

SAFE_TITLES = {
    "Invalid resource type",
    "Unsupported argument",
    "Invalid expression",
    "Missing required argument",
    "Unsupported block type",
    "Unsupported attribute",
    "Invalid reference",
    "Invalid index",
    "Invalid value for variable",
    "Reference to undeclared resource",
    "Reference to undeclared local value",
    "Reference to undeclared input variable",
    "Reference to undeclared module",
    "Module not installed",
    "Missing required provider",
    "Unclosed configuration block",
    "Invalid multi-line string",
    "Invalid single-argument block definition",
    "Invalid provider configuration",
    "Duplicate required providers configuration",
    "Missing newline after argument",
    "Inconsistent conditional result types",
    "Duplicate resource",
    "Duplicate variable declaration",
    "Duplicate output definition",
}


def terraform_skip(reason: str) -> ValidationCheck:
    return ValidationCheck(
        check_id="terraform.validate",
        category="terraform",
        tool="terraform",
        status="skipped",
        message=f"Terraform validation unavailable: {reason}",
        skip_reason=reason,
    )


def terraform_diagnostics(
    raw: str, root: Path, files: set[str]
) -> list[ValidationCheck]:
    """Never expose source snippets, raw output, absolute paths or diagnostic detail."""
    data = json.loads(raw)
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("diagnostics"), list)
        or type(data.get("valid")) is not bool
    ):
        raise ValueError("invalid Terraform output")
    checks: list[ValidationCheck] = []
    for diagnostic in data["diagnostics"]:
        if not isinstance(diagnostic, dict) or diagnostic.get("severity") not in {
            "error",
            "warning",
        }:
            raise ValueError("invalid Terraform diagnostic")
        location = diagnostic.get("range") or {}
        filename = location.get("filename") if isinstance(location, dict) else None
        path = None
        if isinstance(filename, str):
            candidate = Path(filename)
            if candidate.is_absolute():
                try:
                    candidate = candidate.resolve().relative_to(root.resolve())
                except ValueError:
                    raise ValueError("unsafe Terraform diagnostic location") from None
            else:
                candidate = Path("terraform") / candidate
            path = validate_relative_path(candidate.as_posix())
            if path not in files:
                raise ValueError("unknown Terraform diagnostic file")
        start = location.get("start", {}).get("line") if path else None
        end = location.get("end", {}).get("line") if path else None
        # Summaries are diagnostic titles, without the offending source expression.
        title = diagnostic.get("summary")
        if not isinstance(title, str) or title not in SAFE_TITLES:
            title = "Terraform configuration diagnostic"
        checks.append(
            ValidationCheck(
                check_id="terraform.validate",
                category="terraform",
                tool="terraform",
                status="failed" if diagnostic["severity"] == "error" else "warning",
                file_path=path,
                line_start=start,
                line_end=end,
                message=title,
            )
        )
    if data["valid"]:
        checks.append(
            ValidationCheck(
                check_id="terraform.validate",
                category="terraform",
                tool="terraform",
                status="passed",
                message="Terraform provider-schema validation passed",
            )
        )
    elif not any(check.status == "failed" for check in checks):
        raise ValueError("invalid Terraform result without errors")
    return checks


def module_preflight(
    root: Path, files: set[str], documents: PackageDocuments | None = None
) -> tuple[str | None, bool]:
    """Inspect every reachable local module; never fetch remote module sources."""
    queue = [root / "terraform"]
    visited: set[Path] = set()
    local = False
    while queue:
        directory = queue.pop().resolve()
        if directory in visited:
            continue
        visited.add(directory)
        for path in sorted(directory.glob("*.tf*")):
            if path.suffix != ".tf" and not path.name.endswith(".tf.json"):
                continue
            try:
                indexed = (
                    documents.documents.get(path.relative_to(root).as_posix())
                    if documents is not None
                    else None
                )
                if documents is not None:
                    if (
                        indexed is None
                        or indexed.parse_error
                        or not isinstance(indexed.data, dict)
                    ):
                        continue
                    data = indexed.data
                else:
                    data = (
                        json.loads(path.read_text())
                        if path.name.endswith(".tf.json")
                        else hcl2.loads(
                            path.read_text(),
                            serialization_options=SerializationOptions(
                                strip_string_quotes=True,
                                with_comments=False,
                                explicit_blocks=False,
                            ),
                        )
                    )
            except (ValueError, TypeError, LarkError):
                # Syntax remains the real Terraform executable's responsibility.
                continue
            modules = data.get("module", [])
            entries = modules if isinstance(modules, list) else [modules]
            for entry in entries:
                for module in entry.values():
                    source = module.get("source")
                    if not isinstance(source, str) or not source.startswith(
                        ("./", "../")
                    ):
                        return "remote_module_not_available_offline", local
                    target = (directory / source).resolve()
                    if not target.is_relative_to(root.resolve()):
                        return "unsafe_local_module", local
                    if not target.is_dir() or not any(target.glob("*.tf*")):
                        return "local_module_missing", local
                    local = True
                    queue.append(target)
    return None, local


def file_input_guard(root: Path, documents: PackageDocuments) -> list[ValidationCheck]:
    """Terraform file functions must never inspect files outside the copied package."""
    for doc in documents.documents.values():
        if not doc.path.startswith("terraform/") or doc.parse_error:
            continue
        for _, value in walk(doc.data):
            if not isinstance(value, str) or not re.search(r"(?<!\$)\$\{", value):
                continue
            for function in re.finditer(
                r"\b(file|filebase64|templatefile|fileset|fileexists)\s*\(\s*", value
            ):
                tail = value[function.end() :]
                literal = re.match(r'"([^"\n]*)"', tail)
                if literal is None:
                    return [
                        ValidationCheck(
                            check_id="terraform.validate",
                            category="terraform",
                            tool="terraform",
                            status="skipped",
                            file_path=doc.path,
                            line_start=doc.line(function.group(1)),
                            message="Dynamic file input cannot be verified offline",
                            skip_reason="uninspectable_file_input",
                        )
                    ]
                filename = (
                    literal.group(1)
                    .replace("${path.module}", str(root / Path(doc.path).parent))
                    .replace("${path.root}", str(root / "terraform"))
                )
                if "${" in filename or filename.startswith("~"):
                    return [terraform_skip("uninspectable_file_input")]
                target = (root / Path(doc.path).parent / filename).resolve()
                if not target.is_relative_to(root.resolve()) or any(
                    part.startswith(".env") for part in target.parts
                ):
                    return [
                        ValidationCheck(
                            check_id="terraform.file_input",
                            category="reference",
                            tool="builtin",
                            status="failed",
                            file_path=doc.path,
                            line_start=doc.line(function.group(1)),
                            message="File input must remain inside the package",
                        )
                    ]
    return []


async def validate_terraform(
    root: Path,
    files: set[str],
    runner: CommandToolRunner,
    mirror: Path = DEFAULT_MIRROR,
    documents: PackageDocuments | None = None,
) -> list[ValidationCheck]:
    tf = root / "terraform"
    if not tf.is_dir() or not any(tf.glob("*.tf*")):
        return [
            ValidationCheck(
                check_id="terraform.validate",
                category="terraform",
                tool="terraform",
                status="failed",
                file_path=next(
                    (path for path in sorted(files) if path.startswith("terraform/")),
                    None,
                ),
                message="Terraform configuration is missing",
            )
        ]
    indexed = documents or PackageDocuments.parse(
        {path: (root / path).read_text() for path in files}
    )
    guarded = file_input_guard(root, indexed)
    if guarded:
        return guarded
    reason, local = module_preflight(root, files, indexed)
    if reason in {"unsafe_local_module", "local_module_missing"}:
        path = next(
            (
                path
                for path in sorted(files)
                if path.startswith("terraform/") and path.endswith((".tf", ".tf.json"))
            ),
            None,
        )
        return [
            ValidationCheck(
                check_id="terraform.local_module",
                category="reference",
                tool="builtin",
                status="failed",
                file_path=path,
                line_start=1 if path else None,
                message=f"Local module unavailable: {reason}",
            )
        ]
    if not mirror_present(mirror):
        return [terraform_skip("mirror_missing")]
    try:
        if reason is None:
            init = await runner.run_command(
                "terraform",
                [
                    "terraform",
                    "init",
                    "-backend=false",
                    "-input=false",
                    f"-plugin-dir={mirror}",
                    f"-get={'true' if local else 'false'}",
                    "-no-color",
                ],
                root,
                cwd=tf,
            )
        else:
            init = None
        validation = await runner.run_command(
            "terraform", ["terraform", "validate", "-json", "-no-color"], root, cwd=tf
        )
        if validation.exit_code < 0 or (init is not None and init.exit_code < 0):
            return [terraform_skip("tool_error")]
        checks = terraform_diagnostics(validation.stdout, root, files)
        if reason:
            # A real syntax failure must survive even when a module is remote.
            failures = [
                check
                for check in checks
                if check.status == "failed"
                and check.message
                not in {"Module not installed", "Missing required provider"}
            ]
            return failures + [terraform_skip(reason)]
        if init is not None and init.exit_code != 0:
            failures = [
                check
                for check in checks
                if check.status == "failed"
                and check.message
                not in {"Module not installed", "Missing required provider"}
            ]
            if failures:
                return failures
            output = init.stdout + init.stderr
            unavailable = (
                "provider_version_not_in_mirror"
                if any(
                    word in output
                    for word in (
                        "provider packages",
                        "provider registry",
                        "available releases",
                        "Failed to query",
                    )
                )
                else "tool_error"
            )
            return [terraform_skip(unavailable)]
        return checks
    except ToolFailure as error:
        return [
            terraform_skip(
                "not_installed" if error.category == "not_installed" else "tool_error"
            )
        ]
    except (ValueError, TypeError, KeyError, AttributeError):
        return [terraform_skip("tool_error")]
