"""Standard-library evidence helpers. Never load dotenv or dump environments."""

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def command_version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=15, check=False
        )
        return (
            result.stdout.strip().splitlines()[0][:200]
            if result.returncode == 0 and result.stdout.strip()
            else None
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def environment(
    *,
    mode: str = "offline",
    provider: str | None = None,
    model: str | None = None,
    fixing_model: str | None = None,
    tools: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cpu = None
    ram = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                ram = int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    versions = {}
    for package in ("fastapi", "httpx", "openai", "anthropic", "pytest"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    frontend = json.loads((ROOT / "frontend/package.json").read_text())
    return {
        "recorded_at": datetime.now(UTC).isoformat(),
        "mode": mode,
        "provider": provider,
        "model": model,
        "fixing_model": fixing_model,
        "cpu_model": cpu or platform.processor() or None,
        "cpu_count": os.cpu_count(),
        "ram_bytes": ram,
        "os": platform.system(),
        "os_version": platform.version(),
        "kernel": platform.release(),
        "wsl": "microsoft" in platform.release().lower(),
        "python": platform.python_version(),
        "node": command_version(["node", "--version"]),
        "git_commit": command_version(["git", "rev-parse", "HEAD"]),
        "python_packages": versions,
        "frontend_packages": {
            **frontend["dependencies"],
            **frontend["devDependencies"],
        },
        "tools": tools
        or {
            name: command_version([name, "--version"])
            for name in (
                "checkov",
                "trivy",
                "terraform",
                "helm",
                "hadolint",
                "promtool",
                "ansible-lint",
            )
        },
    }


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    temporary.replace(path)


def evidence_directory(name: str, output: Path | None = None, **metadata: Any) -> Path:
    directory = output or ROOT / "docs/evals" / (
        f"phase9-{name}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}"
    )
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / "environment.json", environment(**metadata))
    return directory


def collection_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        INFRAARCH_TEST_BOOTSTRAP="1",
        LLM_PROVIDER="stub",
        LLM_API_KEY="",
        API_KEY="",
        LLM_MODEL="",
        SECURITY_FIX_PROVIDER="stub",
        SECURITY_FIX_MODEL="",
        LLM_BASE_URL="",
    )
    for name, role in (
        ("DATABASE_URL", "infraarch_app"),
        ("MIGRATION_DATABASE_URL", "infraarch_owner"),
        ("TEST_DATABASE_URL", "infraarch_app"),
        ("TEST_MIGRATION_DATABASE_URL", "infraarch_owner"),
    ):
        env[name] = (
            f"postgresql+asyncpg://{role}:collection-only@127.0.0.1:1/infraarch_test"
        )
    env["PYTHONPATH"] = os.pathsep.join(
        (str(BACKEND / "tests/bootstrap"), str(BACKEND))
    )
    return env


def safe_main(function: Any) -> None:
    try:
        function()
    except (OSError, ValueError, RuntimeError):
        print(
            "Phase 9 tool failed; check prerequisites and the partial summary.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
