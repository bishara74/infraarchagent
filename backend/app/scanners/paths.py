"""Constrain scanner-supplied locations to the exact package file map."""

from pathlib import Path

from app.domain.paths import validate_relative_path


def scanner_path(
    raw: object, root: Path, files: set[str], *, allow_report_relative: bool = False
) -> str:
    if not isinstance(raw, str):
        raise ValueError("missing scanner path")
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            path = candidate.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            if not allow_report_relative:
                raise ValueError("scanner path outside package") from None
            path = raw.lstrip("/")
    else:
        path = raw.removeprefix("./")
    validate_relative_path(path)
    if path not in files:
        raise ValueError("scanner path not in package")
    return path
