"""Offline, budget-owned Helm render evidence for D-56 pod proposals."""

import re
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any

import yaml  # type: ignore[import-untyped]

from app.domain.paths import validate_file_map
from app.scanners.runner import CommandToolRunner, ProcessToolRunner, ToolFailure
from app.security.kubernetes import repair_pods
from app.security.kubernetes_images import repair_image_values


async def render_charts(
    files: dict[str, str],
    runner: CommandToolRunner | None = None,
) -> dict[str, list[dict[str, Any]]]:
    runner = runner or ProcessToolRunner()
    files = validate_file_map(files)
    rendered: dict[str, list[dict[str, Any]]] = {}
    with TemporaryDirectory(prefix="infraarch-pod-render-") as directory:
        root = Path(directory)
        for path, source in files.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
        for path in sorted(files):
            if not path.startswith("helm/") or PurePosixPath(path).name != "Chart.yaml":
                continue
            chart = str(PurePosixPath(path).parent)
            try:
                output = await runner.run_command(
                    "helm",
                    [
                        "helm",
                        "template",
                        "infraarch",
                        chart,
                        "--skip-schema-validation",
                    ],
                    root,
                )
                if output.exit_code:
                    continue
                for text in re.split(r"(?m)^---\s*$", output.stdout):
                    match = re.search(
                        r"(?m)^# Source: [^\n]+?(/templates/[^\n]+)$", text
                    )
                    if match is None:
                        continue
                    source_path = chart + match[1]
                    if source_path not in files:
                        continue
                    data = yaml.safe_load(text)
                    if isinstance(data, dict):
                        rendered.setdefault(source_path, []).append(data)
            except (ToolFailure, yaml.YAMLError):
                continue
    return rendered


async def repair_kubernetes(
    files: dict[str, str],
    runner: CommandToolRunner | None = None,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    candidate, records = repair_pods(files, await render_charts(files, runner))
    candidate, image_records = repair_image_values(
        candidate, await render_charts(candidate, runner)
    )
    records.extend(image_records)
    # An atomic candidate may change the same file through several entries.
    from app.security.kubernetes import _hash

    for record in records:
        record["before_hash"] = _hash(files.get(record["file"], ""))
        record["after_hash"] = _hash(candidate[record["file"]])
    return candidate, records


async def repair_formats_and_pods(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    from app.validation.formats import repair_formats

    candidate, records = repair_formats(files)
    candidate, pod_records = await repair_kubernetes(candidate)
    records.extend(pod_records)
    from app.security.kubernetes import _hash

    for record in records:
        record["after_hash"] = _hash(candidate[record["file"]])
    return candidate, records
