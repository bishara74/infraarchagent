"""Reusable stateless validation with bounded tools and whole-stage cleanup."""

import asyncio
import time
from collections.abc import Awaitable
from pathlib import Path

from app.core.telemetry import execution_started, queue_wait, tool_observed
from app.domain.package_layout import (
    MAX_FILE_BYTES,
    MAX_FILES,
    MAX_PACKAGE_BYTES,
    classify_path,
)
from app.domain.plan import DeploymentPlan, FileType
from app.domain.validation import (
    AbortReason,
    ValidationCheck,
    ValidationReport,
    ValidationTool,
)
from app.scanners.runner import (
    CommandToolRunner,
    ProcessToolRunner,
    ToolName,
    ToolResult,
)
from app.validation.documents import PackageDocuments
from app.validation.linters import linter_targets, run_linter
from app.validation.naming import naming_checks
from app.validation.references import reference_checks
from app.validation.structure import structural_checks
from app.validation.terraform import validate_terraform
from app.validation.tools import DEFAULT_MIRROR, report_versions
from app.validation.workspace import ValidationWorkspace, current_workspace


class BoundedRunner:
    def __init__(self, runner: CommandToolRunner, semaphore: asyncio.Semaphore) -> None:
        self.runner = runner
        self.semaphore = semaphore

    @tool_observed
    async def run_command(
        self,
        tool: ToolName,
        args: list[str],
        workdir: Path,
        *,
        cwd: Path | None = None,
        environment_dir: Path | None = None,
        allow_provider_download: bool = False,
    ) -> ToolResult:
        started = time.monotonic()
        try:
            await self.semaphore.acquire()
        finally:
            waits = queue_wait.get()
            if waits is not None:
                waits.append(time.monotonic() - started)
        try:
            execution_started()
            return await self.runner.run_command(
                tool,
                args,
                workdir,
                cwd=cwd,
                environment_dir=environment_dir,
                allow_provider_download=allow_provider_download,
            )
        finally:
            self.semaphore.release()


class ValidationEngine:
    def __init__(
        self,
        runner: CommandToolRunner | None = None,
        *,
        tool_timeout_seconds: float = 60,
        max_parallel_tools: int = 3,
        deadline_seconds: float = 120,
        mirror: Path = DEFAULT_MIRROR,
        versions: dict[ValidationTool, str | None] | None = None,
    ) -> None:
        if (
            not 1 <= max_parallel_tools <= 3
            or deadline_seconds <= 0
            or tool_timeout_seconds <= 0
        ):
            raise ValueError("invalid validation bounds")
        self.runner = runner or ProcessToolRunner(tool_timeout_seconds)
        self.max_parallel_tools = max_parallel_tools
        self.deadline_seconds = deadline_seconds
        self.mirror = mirror
        self.versions = report_versions() if versions is None else versions

    async def validate(
        self, plan: DeploymentPlan, files: dict[str, str]
    ) -> ValidationReport:
        checks: list[ValidationCheck] = []
        required = FileType.TERRAFORM in plan.file_types
        abort: AbortReason | None = None
        started = time.monotonic()
        existing = current_workspace()
        workspace = existing or ValidationWorkspace()
        try:
            async with asyncio.timeout(self.deadline_seconds):
                if (
                    len(files) > MAX_FILES
                    or sum(len(text.encode()) for text in files.values())
                    > MAX_PACKAGE_BYTES
                    or any(
                        len(text.encode()) > MAX_FILE_BYTES for text in files.values()
                    )
                ):
                    raise ValueError("package exceeds validation bounds")
                documents = PackageDocuments.parse(files)
                if any(
                    path != "README.md" and classify_path(path) is None
                    for path in documents.files
                ):
                    raise ValueError("unsupported package path")
                checks.extend(structural_checks(documents, plan))
                checks.extend(reference_checks(documents))
                checks.extend(naming_checks(documents, plan))
                if time.monotonic() - started >= self.deadline_seconds:
                    raise TimeoutError
                async with workspace.check(documents.files) as root:
                    runner = BoundedRunner(
                        self.runner, asyncio.Semaphore(self.max_parallel_tools)
                    )

                    async def collect(job: Awaitable[list[ValidationCheck]]) -> None:
                        checks.extend(await job)

                    async with asyncio.TaskGroup() as group:
                        if required or documents.of_kind(FileType.TERRAFORM):
                            group.create_task(
                                collect(
                                    validate_terraform(
                                        root,
                                        set(documents.files),
                                        runner,
                                        self.mirror,
                                        documents,
                                    )
                                )
                            )
                        for target in linter_targets(documents):
                            group.create_task(
                                collect(
                                    run_linter(
                                        target, root, set(documents.files), runner
                                    )
                                )
                            )
        except TimeoutError:
            abort = "deadline"
        except Exception:
            abort = "internal_error"
        finally:
            if existing is None:
                workspace.close()
        if abort:
            checks.append(
                ValidationCheck(
                    check_id="validator.abort",
                    category="structure",
                    tool="builtin",
                    status="skipped",
                    skip_reason=abort,
                    message=f"Validation stage aborted: {abort}",
                )
            )
        return ValidationReport.build(
            checks,
            terraform_required=required,
            tool_versions=self.versions,
            abort_reason=abort,
        )


async def validate(plan: DeploymentPlan, files: dict[str, str]) -> ValidationReport:
    return await ValidationEngine().validate(plan, files)
