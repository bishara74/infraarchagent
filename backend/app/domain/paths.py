"""Safe relative paths for generated file maps."""

import re
from collections.abc import Mapping

ALLOWED = re.compile(r"[A-Za-z0-9._/-]+\Z", re.ASCII)
DRIVE = re.compile(r"^[A-Za-z]:")


class UnsafePathError(ValueError):
    pass


def validate_relative_path(path: str) -> str:
    if (
        not isinstance(path, str)
        or not path
        or len(path) > 255
        or path.startswith("/")
        or DRIVE.match(path)
        or "\\" in path
        or "\x00" in path
        or not ALLOWED.fullmatch(path)
    ):
        raise UnsafePathError("unsafe relative path")
    segments = path.split("/")
    if len(segments) > 8 or any(segment in {"", ".", ".."} for segment in segments):
        raise UnsafePathError("unsafe relative path")
    return path


def validate_file_map(files: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    seen: set[str] = set()
    for path, content in files.items():
        safe = validate_relative_path(path)
        folded = safe.casefold()
        if folded in seen:
            raise UnsafePathError("case-insensitive duplicate path")
        if not isinstance(content, str):
            raise ValueError("file content must be text")
        seen.add(folded)
        result[safe] = content
    return result
