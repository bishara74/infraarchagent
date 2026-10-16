"""Generation validity checks and reusable all-type patch syntax checks."""

import time
from dataclasses import dataclass
from typing import Any, cast

from app.domain.plan import DeploymentPlan, FileType
from app.domain.validation import (
    CheckStatus,
    ValidationCheck,
    ValidationReport,
    ValidationTool,
)
from app.scanners.runner import ToolFailure, ToolName
from app.validation.documents import PackageDocuments
from app.validation.engine import ValidationEngine
from app.validation.linters import linter_targets
from app.validation.workspace import ValidationWorkspace, current_workspace


def syntax_checks(
    files: dict[str, str], touched: set[str] | None = None
) -> list[ValidationCheck]:
    documents = PackageDocuments.parse(files)
    return [
        ValidationCheck(
            check_id="document.parse",
            category="structure",
            tool="builtin",
            status="failed",
            file_path=doc.path,
            line_start=doc.error_line or 1,
            message="Document could not be parsed",
        )
        for doc in documents.documents.values()
        if doc.parse_error and (touched is None or doc.path in touched)
    ]


@dataclass
class GateResult:
    files: dict[str, str]
    report: ValidationReport
    metrics: dict[str, Any]


class GenerationGate:
    def __init__(self, engine: ValidationEngine) -> None:
        self.engine = engine

    async def extra_checks(
        self,
        files: dict[str, str],
        *,
        touched: set[str] | None = None,
        formatting: bool = False,
    ) -> tuple[dict[str, str], list[ValidationCheck], list[str]]:
        workspace = current_workspace()
        owned = workspace is None
        workspace = workspace or ValidationWorkspace()
        checks = syntax_checks(files, touched)
        formatted: list[str] = []
        documents = PackageDocuments.parse(files)
        try:
            async with workspace.check(files) as root:
                if formatting and any(
                    d.kind == FileType.TERRAFORM for d in documents.documents.values()
                ):
                    try:
                        result = await self.engine.runner.run_command(
                            "terraform",
                            [
                                "terraform",
                                "fmt",
                                "-recursive",
                                "-no-color",
                                "terraform",
                            ],
                            root,
                        )
                        if result.exit_code == 0:
                            for path in files:
                                if path.startswith("terraform/") and path.endswith(
                                    (".tf", ".tfvars")
                                ):
                                    content = (root / path).read_text()
                                    if content != files[path]:
                                        formatted.append(path)
                                        files = {**files, path: content}
                    except ToolFailure as error:
                        checks.append(
                            self.check(
                                "terraform",
                                "terraform/main.tf",
                                "skipped",
                                error.category,
                            )
                        )
                commands: list[tuple[ToolName, str, list[str]]] = []
                for target in linter_targets(documents):
                    if (
                        target.tool == "helm"
                        and target.safe_to_run
                        and (
                            touched is None
                            or any(p.startswith(target.path + "/") for p in touched)
                        )
                    ):
                        commands.append(
                            (
                                "helm",
                                target.file_path,
                                [
                                    "helm",
                                    "template",
                                    "infraarch",
                                    target.path,
                                    "--skip-schema-validation",
                                ],
                            )
                        )
                if touched is None:
                    for doc in documents.of_kind(FileType.ANSIBLE):
                        if (
                            isinstance(doc.data, list)
                            and "/roles/" not in doc.path
                            and any(
                                isinstance(p, dict) and "hosts" in p for p in doc.data
                            )
                        ):
                            # Reuse the linter's package-local input guard.
                            targets = [
                                t
                                for t in linter_targets(documents)
                                if t.tool == "ansible-lint"
                            ]
                            if targets and targets[0].safe_to_run:
                                commands.append(
                                    (
                                        "ansible-playbook",
                                        doc.path,
                                        [
                                            "ansible-playbook",
                                            "--syntax-check",
                                            "-i",
                                            "localhost,",
                                            doc.path,
                                        ],
                                    )
                                )
                for tool, path, args in commands:
                    try:
                        result = await self.engine.runner.run_command(tool, args, root)
                        passed = result.exit_code == 0
                        if tool == "helm" and passed:
                            passed = not syntax_checks(
                                {"k8s/rendered.yaml": result.stdout or "\n"}
                            )
                        checks.append(
                            self.check(tool, path, "passed" if passed else "failed")
                        )
                    except ToolFailure as error:
                        checks.append(self.check(tool, path, "skipped", error.category))
            return files, checks, formatted
        finally:
            if owned:
                workspace.close()

    @staticmethod
    def check(
        tool: ToolName, path: str, status: str, reason: str | None = None
    ) -> ValidationCheck:
        return ValidationCheck(
            check_id=f"gate.{tool.replace('-', '_')}",
            category="structure",
            tool=cast(ValidationTool, tool),
            status=cast(CheckStatus, status),
            file_path=path,
            line_start=1,
            message=f"Generation syntax check {status}",
            skip_reason=("not_installed" if reason == "not_installed" else "tool_error")
            if status == "skipped"
            else None,
        )

    async def run(self, plan: DeploymentPlan, files: dict[str, str]) -> GateResult:
        started = time.monotonic()
        workspace = current_workspace()
        before = len(workspace.terraform_metrics) if workspace else 0
        files, extra, formatted = await self.extra_checks(files, formatting=True)
        checked = await self.engine.validate(plan, files)
        report = ValidationReport.build(
            [*checked.checks, *extra],
            terraform_required=checked.terraform_required,
            tool_versions=checked.tool_versions,
            abort_reason=checked.abort_reason,
        )
        metrics = {
            "outcome": report.summary.result,
            "duration_seconds": time.monotonic() - started,
            "formatted_files": sorted(formatted),
            "failed_checks": [
                c.model_dump(mode="json") for c in report.checks if c.status == "failed"
            ],
            "skipped_checks": [
                c.model_dump(mode="json")
                for c in report.checks
                if c.status == "skipped"
            ],
            "terraform": workspace.terraform_metrics[before:] if workspace else [],
        }
        return GateResult(files, report, metrics)


class GateRepairEngine:
    def __init__(self, gate: GenerationGate) -> None:
        self.gate = gate

    async def validate(
        self, plan: DeploymentPlan, files: dict[str, str]
    ) -> ValidationReport:
        return (await self.gate.run(plan, files)).report
