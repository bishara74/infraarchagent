"""Private, reusable per-package Terraform state and diagnostic measurements."""

import asyncio
import hashlib
import json
import shutil
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from app.domain.paths import validate_file_map
from app.domain.validation import ValidationCheck

_current: ContextVar["ValidationWorkspace | None"] = ContextVar(
    "validation_workspace", default=None
)


def current_workspace() -> "ValidationWorkspace | None":
    return _current.get()


class ValidationWorkspace:
    def __init__(self) -> None:
        self._temporary = TemporaryDirectory(prefix="infraarch-package-")
        self.root = Path(self._temporary.name)
        self.lock = asyncio.Lock()
        self.paths: set[str] = set()
        self.initialized: dict[str, str] = {}
        self.resolved: dict[str, dict[str, str]] = {}
        self.terraform_metrics: list[dict[str, Any]] = []
        self.terraform_checks: dict[str, list[ValidationCheck]] = {}
        self.measurements: list[dict[str, Any]] = []
        self.gate: dict[str, Any] | None = None
        self.original_files: dict[str, str] | None = None
        self.origins: dict[tuple[str, str, str], str] = {}
        self.last_failures: set[tuple[str, str, str]] = set()
        self.stage = "generated"

    @contextmanager
    def activate(self) -> Iterator["ValidationWorkspace"]:
        token = _current.set(self)
        try:
            yield self
        finally:
            _current.reset(token)

    def sync(self, files: dict[str, str]) -> None:
        safe = validate_file_map(files)
        for path in self.paths - safe.keys():
            (self.root / path).unlink(missing_ok=True)
        for path, content in safe.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_text() != content:
                target.write_text(content)
        self.paths = set(safe)

    @asynccontextmanager
    async def check(self, files: dict[str, str]) -> AsyncIterator[Path]:
        async with self.lock:
            self.sync(files)
            with self.activate():
                yield self.root

    def environment(self, module: str) -> Path:
        key = hashlib.sha256(module.encode()).hexdigest()[:16]
        environment = self.root / ".tool-environments" / key
        environment.mkdir(parents=True, exist_ok=True)
        return environment

    def reset_initialization(self, module: str) -> None:
        self.initialized.pop(module, None)
        self.resolved.pop(module, None)
        shutil.rmtree(self.environment(module) / ".terraform-data", ignore_errors=True)
        (self.root / module / ".terraform.lock.hcl").unlink(missing_ok=True)

    @staticmethod
    def fingerprint(value: object) -> str:
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, default=str).encode()
        ).hexdigest()

    def close(self) -> None:
        self._temporary.cleanup()
