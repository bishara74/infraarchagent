"""Safe validator version probes and project-local mirror discovery."""

from functools import lru_cache
from pathlib import Path

from app.domain.validation import ValidationTool
from app.scanners.runner import ProcessToolRunner, ToolName

DEFAULT_MIRROR = Path(__file__).resolve().parents[3] / ".cache/terraform-providers"


@lru_cache
def validator_versions() -> dict[str, dict[str, str | bool | None]]:
    commands: tuple[tuple[ToolName, list[str]], ...] = (
        ("terraform", ["version"]),
        ("helm", ["version", "--short"]),
        ("hadolint", ["--version"]),
        ("ansible-lint", ["--version"]),
        ("promtool", ["--version"]),
    )
    return {
        tool: ProcessToolRunner.probe_version(tool, args) for tool, args in commands
    }


def mirror_present(mirror: Path = DEFAULT_MIRROR) -> bool:
    return mirror.is_dir() and any(mirror.rglob("*_linux_amd64.zip"))


def report_versions() -> dict[ValidationTool, str | None]:
    result: dict[ValidationTool, str | None] = {}
    for tool in ("terraform", "helm", "hadolint", "ansible-lint", "promtool"):
        value = validator_versions()[tool]["version"]
        result[tool] = value if isinstance(value, str) else None
    return result
