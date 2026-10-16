"""Bounded scanner subprocesses with no inherited application environment."""

import asyncio
import os
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, Protocol

ToolName = Literal[
    "checkov",
    "trivy",
    "terraform",
    "helm",
    "hadolint",
    "ansible-lint",
    "ansible-playbook",
    "promtool",
]
EXECUTABLES = {
    "checkov",
    "trivy",
    "terraform",
    "helm",
    "hadolint",
    "ansible-lint",
    "ansible-playbook",
    "promtool",
}
TOOLS: tuple[ToolName, ...] = ("checkov", "trivy", "terraform")


def scanner_environment(workdir: Path, tool: str) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", os.defpath),
        "HOME": str(workdir),
        "LANG": "C.UTF-8",
        "TMPDIR": str(workdir),
        "GIT_TERMINAL_PROMPT": "0",
    }
    for key in (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
    ):
        env[key] = "http://127.0.0.1:9"
    env.update({"NO_PROXY": "", "no_proxy": ""})
    if tool == "checkov":
        env["CHECKOV_PARALLELIZATION_TYPE"] = "none"
    if tool in {"ansible-lint", "ansible-playbook"}:
        env.update(
            {
                "ANSIBLE_HOME": str(workdir / ".ansible"),
                "ANSIBLE_LOCAL_TEMP": str(workdir / ".ansible/tmp"),
                "ANSIBLE_COLLECTIONS_PATH": str(workdir / ".ansible/collections"),
                "ANSIBLE_ROLES_PATH": str(workdir / "ansible/roles"),
                "ANSIBLE_LINT_SKIP_SCHEMA_UPDATE": "1",
                "ANSIBLE_GALAXY_SERVER_LIST": "",
                "PYTHONNOUSERSITE": "1",
            }
        )
    if tool == "terraform":
        env.update(
            {
                "TF_DATA_DIR": str(workdir / ".terraform-data"),
                "CHECKPOINT_DISABLE": "1",
                "TF_IN_AUTOMATION": "1",
            }
        )
    return env


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


class CommandToolRunner(Protocol):
    async def run_command(
        self,
        tool: ToolName,
        args: list[str],
        workdir: Path,
        *,
        cwd: Path | None = None,
        environment_dir: Path | None = None,
        allow_provider_download: bool = False,
    ) -> ToolResult: ...


class ProcessToolRunner:
    def __init__(self, timeout_seconds: float = 120) -> None:
        self.timeout_seconds = timeout_seconds

    async def _terminate(self, process: asyncio.subprocess.Process) -> None:
        """Kill inherited workers as well as their parent; bound pipe cleanup."""
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            await asyncio.wait_for(process.communicate(), timeout=5)
        except TimeoutError:
            # asyncio exposes no public subprocess pipe-close API. Closing the
            # transport prevents a pipe-owning descendant from blocking exit.
            transport = getattr(process, "_transport", None)
            if transport is not None:
                transport.close()

    async def run(self, tool: ToolName, workdir: Path) -> ToolResult:
        if tool == "checkov":
            args = [
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
        elif tool == "trivy":
            args = [
                "trivy",
                "config",
                ".",
                "--format",
                "json",
                "--exit-code",
                "0",
                "--quiet",
                "--skip-check-update",
                "--skip-version-check",
                "--disable-telemetry",
                "--cache-dir",
                str(workdir / ".trivy-cache"),
            ]
        else:
            args = ["terraform", "validate", "-json", "-no-color"]
        cwd = workdir
        if tool == "terraform":
            cwd = workdir / "terraform"
            cwd.mkdir(exist_ok=True)
        return await self.run_command(tool, args, workdir, cwd=cwd)

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
        """Explicit argv without shells, inherited secrets or arbitrary executables."""
        if tool not in EXECUTABLES or not args or args[0] != tool:
            raise ToolFailure(tool, "unsafe_command")
        selected_cwd = (cwd or workdir).resolve()
        if not selected_cwd.is_relative_to(workdir.resolve()):
            raise ToolFailure(tool, "unsafe_workdir")
        env = scanner_environment(environment_dir or workdir, tool)
        if allow_provider_download:
            if tool != "terraform" or args[1:3] != ["providers", "mirror"]:
                raise ToolFailure(tool, "unsafe_network_command")
            for key in (
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "ALL_PROXY",
                "http_proxy",
                "https_proxy",
                "all_proxy",
            ):
                env.pop(key, None)
        started = time.monotonic()
        command = list(args)
        if tool == "ansible-playbook" and shutil.which(tool) is None:
            lint = shutil.which("ansible-lint")
            sibling = Path(lint).resolve().with_name(tool) if lint else None
            if sibling is not None and sibling.is_file():
                command[0] = str(sibling)
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=selected_cwd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
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
            await self._terminate(process)
            raise ToolFailure(tool, "timeout") from None
        except asyncio.CancelledError:
            await self._terminate(process)
            raise
        return ToolResult(
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            process.returncode or 0,
            time.monotonic() - started,
        )

    @staticmethod
    def probe_version(
        tool: ToolName, args: list[str] | None = None
    ) -> dict[str, str | bool | None]:
        if tool not in EXECUTABLES:
            raise ToolFailure(tool, "unsafe_command")
        executable = shutil.which(tool)
        version: str | None = None
        if executable is not None:
            with TemporaryDirectory(prefix="infraarch-version-") as directory:
                try:
                    process = subprocess.Popen(
                        [executable, *(args or ["--version"])],
                        cwd=directory,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        start_new_session=True,
                        env=scanner_environment(Path(directory), tool),
                    )
                    try:
                        stdout, _ = process.communicate(timeout=10)
                    except subprocess.TimeoutExpired:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.communicate(timeout=5)
                        stdout = ""
                    lines = stdout.strip().splitlines()
                    selected = (
                        lines[0]
                        if tool
                        in {"terraform", "helm", "hadolint", "ansible-lint", "promtool"}
                        else lines[-1]
                        if lines
                        else ""
                    )
                    version = selected.strip()[:100] or None
                except (OSError, subprocess.TimeoutExpired, IndexError):
                    pass
        return {"available": executable is not None, "version": version}


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
        return await self.run(tool, workdir)


@lru_cache
def scanner_versions() -> dict[str, dict[str, str | bool | None]]:
    """Probe once at startup through the shared runner's safe version adapter."""
    return {tool: ProcessToolRunner.probe_version(tool) for tool in TOOLS}
