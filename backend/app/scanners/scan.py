"""Temporary package materialisation and concurrent scanner orchestration."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.paths import validate_file_map
from app.scanners.checkov_parser import parse_checkov
from app.scanners.runner import ToolFailure, ToolName, ToolRunner
from app.scanners.tfsec_parser import parse_tfsec
from app.security.policy import classify


@dataclass(frozen=True)
class ScanResult:
    violations: list[Violation]
    tool_status: dict[str, str]


class Scanner:
    def __init__(self, runner: ToolRunner) -> None:
        self.runner = runner

    async def scan(self, files: dict[str, str], variant: Variant) -> ScanResult:
        safe_files = validate_file_map(files)
        last_error: ToolFailure | None = None
        for _ in range(2):
            try:
                return await self._once(safe_files, variant)
            except ToolFailure as error:
                last_error = error
        assert last_error is not None
        raise last_error

    async def _once(self, files: dict[str, str], variant: Variant) -> ScanResult:
        with TemporaryDirectory(prefix="infraarch-scan-") as directory:
            root = Path(directory)
            for path, content in files.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8", newline="")
            names: tuple[ToolName, ToolName] = ("checkov", "tfsec")
            outputs = await asyncio.gather(
                *(self.runner.run(name, root) for name in names),
                return_exceptions=True,
            )
            violations: list[Violation] = []
            for name, output in zip(names, outputs, strict=True):
                if isinstance(output, ToolFailure):
                    raise output
                if isinstance(output, BaseException):
                    raise ToolFailure(name, "crash") from None
                try:
                    parsed = (
                        parse_checkov(output.stdout, root, set(files))
                        if name == "checkov"
                        else parse_tfsec(output.stdout, root, set(files))
                    )
                except ValueError:
                    raise ToolFailure(name, "invalid_json") from None
                if output.exit_code not in (0, 1):
                    raise ToolFailure(name, "crash")
                violations.extend(parsed)
            return ScanResult(
                classify(violations, variant, files), {name: "ok" for name in names}
            )
