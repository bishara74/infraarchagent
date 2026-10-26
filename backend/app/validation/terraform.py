"""Offline Terraform initialization and full provider-schema diagnostics."""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

import hcl2
from hcl2.utils import SerializationOptions
from lark.exceptions import LarkError

from app.core.telemetry import execution_started, invocation, span, timed
from app.domain.paths import validate_relative_path
from app.domain.validation import ValidationCheck
from app.scanners.runner import CommandToolRunner, ToolFailure
from app.validation.documents import PackageDocuments, blocks, walk
from app.validation.provider_schema import provider_requirements
from app.validation.tools import DEFAULT_MIRROR, mirror_present
from app.validation.workspace import ValidationWorkspace, current_workspace

SAFE_TITLES = {
    "Cycle",
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
    raw: str, root: Path, files: set[str], module: str = "terraform"
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
                candidate = Path(module) / candidate
            path = validate_relative_path(candidate.as_posix())
            if path not in files:
                raise ValueError("unknown Terraform diagnostic file")
        if path is not None:
            start = location.get("start", {}).get("line")
            end = location.get("end", {}).get("line")
        else:
            # Global diagnostics (e.g. dependency cycles) still need retry targets.
            candidates = sorted(
                path
                for path in files
                if path.startswith("terraform/") and path.endswith(".tf")
            )
            roots = [
                path for path in candidates if Path(path).parent == Path("terraform")
            ]
            path = (
                "terraform/main.tf"
                if "terraform/main.tf" in files
                else next(iter(roots or candidates), None)
            )
            if path is None:
                path = next(
                    (
                        path
                        for path in sorted(files)
                        if path.startswith("terraform/") and path.endswith(".tf.json")
                    ),
                    None,
                )
            start = 1 if path else None
            end = None
        # Summaries are diagnostic titles, without the offending source expression.
        title = diagnostic.get("summary")
        if isinstance(title, str) and title.startswith("Cycle:"):
            # The remainder is a graph listing, not a stable diagnostic title.
            title = "Cycle"
        if not isinstance(title, str) or title not in SAFE_TITLES:
            title = "Terraform configuration diagnostic"
        check = ValidationCheck(
            check_id="terraform.validate",
            category="terraform",
            tool="terraform",
            status="failed" if diagnostic["severity"] == "error" else "warning",
            file_path=path,
            line_start=start,
            line_end=end,
            message=title,
        )
        scope_match = re.match(
            r'(resource|data) "([\w-]+)" "([\w-]+)"',
            str((diagnostic.get("snippet") or {}).get("context", "")),
        )
        if scope_match:
            scope = ".".join(scope_match.groups())
            argument = re.search(
                r'(?:argument|attribute|block(?:s)? of type)(?: named)? "([\w-]+)"',
                str(diagnostic.get("detail", "")),
                re.IGNORECASE,
            )
            key = (
                title,
                path,
                scope,
                argument[1]
                if argument
                else (start, (location.get("start") or {}).get("column")),
            )
            check = check.model_copy(
                update={
                    "diagnostic_key": hashlib.sha256(
                        json.dumps(key).encode()
                    ).hexdigest()
                }
            )
            check._origin_scope = scope
        checks.append(check)
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
    root: Path,
    files: set[str],
    documents: PackageDocuments | None = None,
    module: str = "terraform",
) -> tuple[str | None, bool]:
    """Inspect every reachable local module; never fetch remote module sources."""
    queue = [root / module]
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
                for module_body in entry.values():
                    source = module_body.get("source")
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


def file_input_guard(
    root: Path, documents: PackageDocuments, *, evaluation_cwd: Path | None = None
) -> list[ValidationCheck]:
    """Terraform file functions must never inspect files outside the copied package."""
    cwd = evaluation_cwd or (
        root / "terraform" if (root / "terraform").is_dir() else root
    )
    for doc in documents.documents.values():
        if not doc.path.endswith((".tf", ".tf.json", ".tfvars")) or doc.parse_error:
            continue
        for _, value in walk(doc.data):
            if not isinstance(value, str) or not re.search(r"(?<!\$)\$\{", value):
                continue
            for function in re.finditer(
                r"\b(file|filebase64|templatefile|fileset|fileexists|filemd5|filesha1|"
                r"filesha256|filesha512|filebase64sha256|filebase64sha512)\s*\(\s*",
                value,
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
                    .replace("${path.root}", str(cwd))
                )
                if "${" in filename or filename.startswith("~"):
                    return [terraform_skip("uninspectable_file_input")]
                target = (cwd / filename).resolve()
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


@timed("verification")
async def _validate_module(
    root: Path,
    files: set[str],
    runner: CommandToolRunner,
    mirror: Path = DEFAULT_MIRROR,
    documents: PackageDocuments | None = None,
    module: str = "terraform",
) -> list[ValidationCheck]:
    tf = root / module
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
    guarded = file_input_guard(root, indexed, evaluation_cwd=tf)
    if guarded:
        return guarded
    reason, local = module_preflight(root, files, indexed, module)
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
    workspace = current_workspace()
    environment = workspace.environment(module) if workspace else root
    # Resource bodies do not require initialization. Only provider type names do.
    dependencies: dict[str, dict[str, Any]] = {}
    for doc in indexed.documents.values():
        if not doc.path.endswith((".tf", ".tf.json")) or not isinstance(doc.data, dict):
            continue
        kinds = {
            labels[0].split("_")[0]
            for kind in ("resource", "data")
            for labels, _ in blocks(doc.data, kind)
        }
        if not kinds and not any(k in doc.data for k in ("module", "terraform")):
            continue
        group = dependencies.setdefault(
            str(Path(doc.path).parent), {"module": [], "terraform": [], "types": []}
        )
        for key in ("module", "terraform"):
            value = doc.data.get(key, [])
            group[key].extend(value if isinstance(value, list) else [value])
        group["types"] = sorted(set(group["types"]) | kinds)
    fingerprint = ValidationWorkspace.fingerprint(
        {"mirror": str(mirror.resolve()), "dependencies": dependencies}
    )
    reused = bool(workspace and workspace.initialized.get(module) == fingerprint)
    if reused:
        with span("cache", operation="terraform.init"):
            pass
    metrics = {
        "module": module,
        "init_reused": reused,
        "init_seconds": 0.0,
        "validate_seconds": 0.0,
        "init_outcome": "reused" if reused else "not_started",
        "reinitialization_reason": "dependencies_changed"
        if workspace and module in workspace.initialized and not reused
        else "none"
        if reused
        else "first_or_failed_initialization",
    }
    started = time.monotonic()
    try:
        if reason is None and not reused:
            if workspace:
                workspace.reset_initialization(module)
            (environment / ".terraformrc").write_text(
                "provider_installation { filesystem_mirror { path = "
                + json.dumps(str(mirror.resolve()))
                + " } }\n"
            )
            init_started = time.monotonic()
            try:
                with invocation("terraform.init"):
                    execution_started()
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
                        environment_dir=environment,
                    )
            finally:
                metrics["init_seconds"] = time.monotonic() - init_started
            metrics["init_outcome"] = (
                "initialized"
                if init.exit_code == 0
                else init_failure_category(init.stdout + init.stderr, indexed, module)
            )
            if workspace and init.exit_code == 0:
                workspace.initialized[module] = fingerprint
                lock = tf / ".terraform.lock.hcl"
                workspace.resolved[module] = (
                    dict(
                        re.findall(
                            r'provider "registry.terraform.io/hashicorp/([\w-]+)" '
                            r'\{\s*version\s*=\s*"([0-9.]+)"',
                            lock.read_text(),
                        )
                    )
                    if lock.exists()
                    else {}
                )
        else:
            init = None
        validate_started = time.monotonic()
        try:
            with invocation("terraform.validate"):
                execution_started()
                validation = await runner.run_command(
                    "terraform",
                    ["terraform", "validate", "-json", "-no-color"],
                    root,
                    cwd=tf,
                    environment_dir=environment,
                )
        finally:
            metrics["validate_seconds"] = time.monotonic() - validate_started
        if validation.exit_code < 0 or (init is not None and init.exit_code < 0):
            return [terraform_skip("tool_error")]
        checks = terraform_diagnostics(validation.stdout, root, files, module)
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
    finally:
        metrics["seconds"] = time.monotonic() - started
        if workspace:
            workspace.terraform_metrics.append(metrics)


def init_failure_category(output: str, documents: PackageDocuments, module: str) -> str:
    if any(
        d.parse_error
        for d in documents.documents.values()
        if str(Path(d.path).parent) == module
    ) or any(
        word in output
        for word in (
            "Invalid character",
            "Invalid single-argument",
            "Invalid multi-line",
            "Unclosed",
            "Missing newline",
            "Invalid expression",
            "Argument or block definition required",
        )
    ):
        return "syntax"
    if ("required_providers" in output or "provider source" in output.lower()) and any(
        word in output.lower() for word in ("invalid", "duplicate", "incorrect")
    ):
        return "invalid_required_providers"
    if not provider_requirements(documents, module):
        return "missing_required_providers"
    if any(
        word in output
        for word in (
            "provider packages",
            "available releases",
            "Failed to query",
            "provider registry",
        )
    ):
        return "mirror_constraint_unavailable"
    return "unknown"


async def validate_terraform(
    root: Path,
    files: set[str],
    runner: CommandToolRunner,
    mirror: Path = DEFAULT_MIRROR,
    documents: PackageDocuments | None = None,
) -> list[ValidationCheck]:
    documents = documents or PackageDocuments.parse(
        {p: (root / p).read_text() for p in files}
    )
    workspace = current_workspace()
    key = ValidationWorkspace.fingerprint(
        {"files": documents.files, "mirror": str(mirror.resolve())}
    )
    if (
        workspace is not None
        and key in workspace.terraform_checks
        and workspace.terraform_check_initialization.get(key) == workspace.initialized
    ):
        with span("cache", operation="terraform.validate"):
            pass
        workspace.terraform_metrics.append(
            {
                "module": "terraform",
                "init_reused": True,
                "init_seconds": 0.0,
                "validate_seconds": 0.0,
                "seconds": 0.0,
                "init_outcome": "validation_cached",
            }
        )
        return list(workspace.terraform_checks[key])
    modules = sorted(
        {
            str(Path(p).parent)
            for p in files
            if p.startswith("terraform/") and p.endswith((".tf", ".tf.json"))
        }
    ) or ["terraform"]
    checks = []
    for module in modules:
        checks.extend(
            await _validate_module(root, files, runner, mirror, documents, module)
        )
    if (
        workspace is not None
        and checks
        and not any(c.status == "skipped" for c in checks)
        and all(module in workspace.initialized for module in modules)
    ):
        workspace.terraform_checks[key] = list(checks)
        workspace.terraform_check_initialization[key] = dict(workspace.initialized)
    return checks
