"""One path contract for generator prompts and structural completeness checks."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.domain.paths import UnsafePathError, validate_file_map, validate_relative_path
from app.domain.plan import FileType

MAX_FILES = 80
MAX_FILE_BYTES = 200_000
MAX_PACKAGE_BYTES = 2_000_000


@dataclass(frozen=True)
class LayoutRule:
    required: tuple[str, ...]
    allowed: tuple[str, ...]


LAYOUT: dict[FileType, LayoutRule] = {
    FileType.TERRAFORM: LayoutRule(
        ("terraform/**/*.tf",),
        ("terraform/**/*.tf", "terraform/**/*.tfvars", "terraform/**/*.tf.json"),
    ),
    FileType.KUBERNETES: LayoutRule(
        ("k8s/**/*.yaml", "k8s/**/*.yml"),
        ("k8s/**/*.yaml", "k8s/**/*.yml"),
    ),
    FileType.HELM: LayoutRule(("helm/<chart>/Chart.yaml",), ("helm/<chart>/**",)),
    FileType.DOCKERFILE: LayoutRule(
        ("docker/**/Dockerfile",), ("docker/**/Dockerfile",)
    ),
    FileType.JENKINS: LayoutRule(("jenkins/Jenkinsfile",), ("jenkins/Jenkinsfile",)),
    FileType.NGINX: LayoutRule(("nginx/**/*.conf",), ("nginx/**/*.conf",)),
    FileType.ANSIBLE: LayoutRule(
        ("ansible/**/*.yml", "ansible/**/*.yaml"),
        ("ansible/**/*.yml", "ansible/**/*.yaml"),
    ),
    FileType.PROMETHEUS: LayoutRule(
        ("monitoring/prometheus/**/*.yml", "monitoring/prometheus/**/*.yaml"),
        ("monitoring/prometheus/**/*.yml", "monitoring/prometheus/**/*.yaml"),
    ),
    FileType.GRAFANA: LayoutRule(
        ("monitoring/grafana/**/*.json",),
        ("monitoring/grafana/**/*.json",),
    ),
}


def _regex(pattern: str) -> re.Pattern[str]:
    """Treat **/ as zero or more directory levels, and * as one segment."""
    escaped = re.escape(pattern)
    escaped = escaped.replace(r"\*\*/", r"(?:[^/]+/)*")
    escaped = escaped.replace(r"\*\*", r".+")
    escaped = escaped.replace(r"\*", r"[^/]*")
    escaped = escaped.replace(r"<chart>", r"[^/]+")
    return re.compile(rf"{escaped}\Z")


_REQUIRED = {
    kind: tuple(_regex(pattern) for pattern in rule.required)
    for kind, rule in LAYOUT.items()
}
_ALLOWED = {
    kind: tuple(_regex(pattern) for pattern in rule.allowed)
    for kind, rule in LAYOUT.items()
}


def layout_guidance() -> str:
    """Render the same path rules that validation uses for the LLM prompt."""
    lines = ["Required path for each requested file type (one matching file minimum):"]
    for kind, rule in LAYOUT.items():
        lines.append(f"- {kind.value}: {' or '.join(rule.required)}")
        extras = tuple(path for path in rule.allowed if path not in rule.required)
        if extras:
            lines.append(f"  Also allowed: {', '.join(extras)}")
    lines.append("An optional top-level README.md is allowed.")
    return "\n".join(lines)


def classify_path(path: str) -> FileType | None:
    try:
        validate_relative_path(path)
    except UnsafePathError:
        return None
    for kind, patterns in _ALLOWED.items():
        if any(pattern.fullmatch(path) for pattern in patterns):
            return kind
    return None


def _safe_path(path: str) -> bool:
    try:
        validate_relative_path(path)
    except UnsafePathError:
        return False
    return True


def required_types_missing(
    files: Mapping[str, str], required: Sequence[FileType]
) -> list[FileType]:
    return [
        kind
        for kind in dict.fromkeys(required)
        if not any(
            _safe_path(path)
            and any(pattern.fullmatch(path) for pattern in _REQUIRED[kind])
            for path in files
        )
    ]


def package_structure_errors(
    files: Mapping[str, str], required: Sequence[FileType]
) -> list[str]:
    """Collect independent structure defects without inspecting file syntax."""
    errors: list[str] = []
    required_set = set(required)
    if len(files) > MAX_FILES:
        errors.append(f"too many files: {len(files)}; maximum is {MAX_FILES}")
    try:
        validate_file_map(files)
    except (UnsafePathError, ValueError) as error:
        errors.append(f"file map: {error}")
    total_bytes = 0
    for index, (path, content) in enumerate(files.items(), start=1):
        try:
            validate_relative_path(path)
        except UnsafePathError:
            errors.append(f"file path #{index} is unsafe; use a relative POSIX path")
            continue
        if path != "README.md":
            kind = classify_path(path)
            if kind is None:
                errors.append(f"{path}: outside the allowed package layout")
            elif kind not in required_set:
                errors.append(f"{path}: {kind.value} is not in plan.file_types")
        if not content:
            errors.append(f"{path}: file is empty")
        file_bytes = len(content.encode("utf-8"))
        total_bytes += file_bytes
        if file_bytes > MAX_FILE_BYTES:
            errors.append(
                f"{path}: {file_bytes} bytes exceeds {MAX_FILE_BYTES}-byte file limit"
            )
    if total_bytes > MAX_PACKAGE_BYTES:
        errors.append(
            f"package: {total_bytes} bytes exceeds {MAX_PACKAGE_BYTES}-byte limit"
        )
    for kind in required_types_missing(files, required):
        patterns = " or ".join(LAYOUT[kind].required)
        errors.append(f"missing {kind.value} files: expected at least one {patterns}")
    return errors
