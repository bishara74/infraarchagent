"""Temporary package materialisation and concurrent scanner orchestration."""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.telemetry import execution_started, invocation, scope, tags, timed
from app.domain.enums import Severity, Variant
from app.domain.models import Violation
from app.domain.paths import validate_file_map
from app.scanners.checkov_parser import CheckovPathError, parse_checkov
from app.scanners.external_modules import external_module_findings
from app.scanners.runner import TOOLS, ToolFailure, ToolName, ToolResult, ToolRunner
from app.scanners.terraform_parser import parse_terraform
from app.scanners.trivy_parser import parse_trivy
from app.security.policy import classify


@dataclass(frozen=True)
class ScanResult:
    violations: list[Violation]
    tool_status: dict[str, str]
    syntax_limited: bool = False


@dataclass(frozen=True)
class ScanObservation:
    iteration: int
    attempt: int
    tool: ToolName
    duration: float
    category: str


class Scanner:
    def __init__(
        self,
        runner: ToolRunner,
        observer: Callable[[ScanObservation], None] | None = None,
    ) -> None:
        self.runner = runner
        self.observer = observer

    async def run_tool(
        self, tool: ToolName, root: Path, *, iteration: int = 0, attempt: int = 1
    ) -> ToolResult:
        started = time.monotonic()
        category = "ok"
        try:
            with (
                scope(
                    attempt=attempt,
                    iteration=(tags.get() or {}).get("iteration", iteration),
                ),
                invocation("terraform.validate" if tool == "terraform" else tool),
            ):
                execution_started()
                return await self.runner.run(tool, root)
        except ToolFailure as error:
            category = error.category
            raise
        except asyncio.CancelledError:
            category = "cancelled"
            raise
        except Exception:
            category = "crash"
            raise
        finally:
            if self.observer is not None:
                self.observer(
                    ScanObservation(
                        iteration, attempt, tool, time.monotonic() - started, category
                    )
                )

    @timed("scan")
    async def scan(
        self, files: dict[str, str], variant: Variant, *, iteration: int = 0
    ) -> ScanResult:
        safe_files = validate_file_map(files)
        last_error: ToolFailure | None = None
        for attempt in range(1, 3):
            try:
                return await self._once(safe_files, variant, iteration, attempt)
            except ToolFailure as error:
                last_error = error
        assert last_error is not None
        raise last_error

    async def _once(
        self, files: dict[str, str], variant: Variant, iteration: int, attempt: int
    ) -> ScanResult:
        with TemporaryDirectory(prefix="infraarch-scan-") as directory:
            root = Path(directory)
            for path, content in files.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8", newline="")
            names = TOOLS
            outputs = await asyncio.gather(
                *(
                    self.run_tool(name, root, iteration=iteration, attempt=attempt)
                    for name in names
                ),
                return_exceptions=True,
            )
            violations: list[Violation] = []
            syntax_limited = False
            file_input_blocked = False
            for name, output in zip(names, outputs, strict=True):
                if (
                    isinstance(output, ToolFailure)
                    and name == "terraform"
                    and output.category == "unsafe_file_input"
                ):
                    from app.validation.documents import PackageDocuments
                    from app.validation.terraform import file_input_guard

                    refused = file_input_guard(root, PackageDocuments.parse(files))
                    if not refused:
                        raise output
                    file_input_blocked = True
                    for check in refused:
                        path = check.file_path or next(
                            p
                            for p in sorted(files)
                            if p.endswith((".tf", ".tf.json", ".tfvars"))
                        )
                        violations.append(
                            Violation(
                                tool="terraform",
                                rule_id="TERRAFORM_FILE_INPUT",
                                severity=Severity.CRITICAL,
                                file_path=path,
                                resource="",
                                line_start=check.line_start,
                                title="Terraform file input blocked",
                                message=(
                                    "Terraform evaluation was refused because a file "
                                    "input cannot be proved to remain "
                                    "inside the package."
                                ),
                            )
                        )
                    continue
                if isinstance(output, ToolFailure):
                    raise output
                if isinstance(output, BaseException):
                    raise ToolFailure(name, "crash") from None
                try:
                    parsed = (
                        parse_checkov(output.stdout, root, set(files))
                        if name == "checkov"
                        else parse_trivy(output.stdout, root, set(files))
                        if name == "trivy"
                        else parse_terraform(output.stdout, root, set(files))
                    )
                except CheckovPathError:
                    raise ToolFailure(name, "path_mapping") from None
                except ValueError:
                    raise ToolFailure(name, "invalid_json") from None
                if output.exit_code not in (0, 1):
                    raise ToolFailure(name, "crash")
                if name == "terraform" and any(
                    item.rule_id == "TERRAFORM_SYNTAX" for item in parsed
                ):
                    syntax_limited = True
                violations.extend(parsed)
            violations.extend(external_module_findings(files))
            return ScanResult(
                classify(violations, variant, files),
                {
                    "checkov": "ok",
                    "trivy": "ok",
                    "terraform": "file_input_blocked"
                    if file_input_blocked
                    else "syntax_limited"
                    if syntax_limited
                    else "ok",
                },
                syntax_limited=syntax_limited,
            )
