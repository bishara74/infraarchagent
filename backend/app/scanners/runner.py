"""Bounded scanner subprocesses with no inherited application environment."""

import asyncio
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

ToolName = Literal["checkov", "tfsec"]


@dataclass(frozen=True)
class ToolResult:
    stdout: str
    stderr: str
    exit_code: int
    duration: float


class ToolFailure(Exception):
    def __init__(self, tool: ToolName, category: str) -> None:
        self.tool = tool
        self.category = category
        super().__init__(f"{tool}: {category}")


class ToolRunner(Protocol):
    async def run(self, tool: ToolName, workdir: Path) -> ToolResult: ...


class ProcessToolRunner:
    def __init__(self, timeout_seconds: float = 120) -> None:
        self.timeout_seconds = timeout_seconds

    async def run(self, tool: ToolName, workdir: Path) -> ToolResult:
        args = (
            [
                "checkov",
                "-d",
                ".",
                "-o",
                "json",
                "--quiet",
                "--compact",
                "--skip-download",
                "--skip-results-upload",
                "--framework",
                "terraform,kubernetes,helm,dockerfile",
            ]
            if tool == "checkov"
            else [
                "tfsec",
                ".",
                "--format",
                "json",
                "--no-color",
                "--soft-fail",
                "--no-module-downloads",
            ]
        )
        # Scanner input is untrusted; never inherit DB, LLM, cloud, proxy, or
        # Checkov/TFSEC configuration variables from the application process.
        env = {
            "PATH": os.defpath if not os.environ.get("PATH") else os.environ["PATH"],
            "HOME": str(workdir),
            "LANG": "C.UTF-8",
            "TMPDIR": str(workdir),
        }
        started = time.monotonic()
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                cwd=workdir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            raise ToolFailure(tool, "not_installed") from None
        except OSError:
            raise ToolFailure(tool, "launch_error") from None
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout_seconds
            )
        except TimeoutError:
            process.kill()
            await process.communicate()
            raise ToolFailure(tool, "timeout") from None
        return ToolResult(
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            process.returncode or 0,
            time.monotonic() - started,
        )


class RecordedToolRunner:
    """Scripted scanner outputs for offline tests, with call history."""

    def __init__(
        self,
        results: dict[ToolName, list[ToolResult | ToolFailure]],
        *,
        recorded_root: Path | None = None,
    ) -> None:
        self.results = {tool: list(script) for tool, script in results.items()}
        self.calls: list[ToolName] = []
        self.recorded_root = recorded_root

    async def run(self, tool: ToolName, workdir: Path) -> ToolResult:
        self.calls.append(tool)
        if not self.results.get(tool):
            raise ToolFailure(tool, "recording_exhausted")
        result = self.results[tool].pop(0)
        if isinstance(result, ToolFailure):
            raise result
        if self.recorded_root is not None:
            return ToolResult(
                result.stdout.replace(str(self.recorded_root), str(workdir)),
                result.stderr,
                result.exit_code,
                result.duration,
            )
        return result


def scanner_versions() -> dict[str, dict[str, str | bool | None]]:
    """Probe once at startup; version commands receive the same safe environment."""
    import subprocess

    versions: dict[str, dict[str, str | bool | None]] = {}
    for tool in ("checkov", "tfsec"):
        executable = shutil.which(tool)
        version: str | None = None
        if executable:
            try:
                completed = subprocess.run(
                    [executable, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                    env={
                        "PATH": os.environ.get("PATH", os.defpath),
                        "HOME": "/tmp",
                        "LANG": "C.UTF-8",
                    },
                )
                lines = completed.stdout.strip().splitlines()
                version = lines[-1].strip()[:100] if lines else None
            except (OSError, subprocess.TimeoutExpired):
                pass
        versions[tool] = {"available": executable is not None, "version": version}
    return versions
