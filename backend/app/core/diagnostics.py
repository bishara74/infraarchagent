# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Process-lifetime native fault diagnostics."""

import faulthandler
import json
import os
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import BinaryIO

DIRECTORY = Path(__file__).resolve().parents[3] / ".cache/diagnostics"
DISTRIBUTIONS = (
    "asyncpg",
    "cryptography",
    "pydantic-core",
    "uvloop",
    "httptools",
    "orjson",
    "ujson",
)
_fault_log: BinaryIO | None = None
_fault_pid: int | None = None


def native_versions() -> dict[str, object]:
    packages: dict[str, str | None] = {}
    for name in DISTRIBUTIONS:
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    libc, libc_version = platform.libc_ver()
    return {
        "python": platform.python_version(),
        "libc": libc,
        "libc_version": libc_version,
        "extensions": packages,
    }


def fault_log_path(pid: int, directory: Path = DIRECTORY) -> Path:
    return directory / f"faulthandler-{pid}.log"


def enable_fault_diagnostics(directory: Path = DIRECTORY) -> Path:
    global _fault_log, _fault_pid
    pid = os.getpid()
    if _fault_log is not None and _fault_pid == pid:
        return Path(str(_fault_log.name))

    directory.mkdir(parents=True, exist_ok=True)
    path = fault_log_path(pid, directory)
    log = path.open("ab", buffering=0)
    try:
        faulthandler.enable(file=log, all_threads=True)
    except BaseException:
        log.close()
        raise
    if _fault_log is not None:
        _fault_log.close()
    _fault_log, _fault_pid = log, pid

    line = "Native runtime " + json.dumps(native_versions(), sort_keys=True)
    log.write((line + "\n").encode())
    print(line, file=sys.stderr, flush=True)
    print(f"Faulthandler log {path}", file=sys.stderr, flush=True)
    return path
