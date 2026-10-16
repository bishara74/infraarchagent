"""Private, reusable per-package Terraform state and diagnostic measurements."""

import asyncio
import hashlib
import json
import shutil
from collections import Counter
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
        self.terraform_check_initialization: dict[str, dict[str, str]] = {}
        self.measurements: list[dict[str, Any]] = []
        self.gate: dict[str, Any] | None = None
        self.original_files: dict[str, str] | None = None
        self.origins: dict[tuple[str, str, str], str] = {}
        self.last_failures: set[tuple[str, str, str]] = set()
        self.stage = "generated"
        self.declared_scopes: set[str] = set()
        self.observed = False
        self.terraform_complete = False
        self.complete_tools: set[str] = set()

    @staticmethod
    def check_key(check: ValidationCheck) -> tuple[str, str, str]:
        return (
            check.check_id,
            check.file_path or "",
            check.diagnostic_key or f"{check.message}:{check.line_start}",
        )

    def observe(
        self,
        checks: list[ValidationCheck],
        stage: str,
        files: dict[str, str],
        *,
        partial: bool = False,
    ) -> None:
        from app.validation.documents import PackageDocuments, blocks

        counts = Counter(self.check_key(c) for c in checks if c.status == "failed")
        scopes = {
            f"{Path(doc.path).parent}:{kind}.{'.'.join(labels)}"
            for doc in PackageDocuments.parse(files).documents.values()
            if not doc.parse_error
            for kind in ("resource", "data")
            for labels, body in blocks(doc.data, kind)
        }
        for check in checks:
            if check.status != "failed":
                continue
            key = self.check_key(check)
            scope = (
                f"{Path(check.file_path).parent}:{check._origin_scope}"
                if check.file_path and check._origin_scope
                else None
            )
            if key not in self.last_failures:
                certain = stage == "generated" or (
                    self.observed
                    and (
                        check.tool == "builtin"
                        or (check.tool == "terraform" and self.terraform_complete)
                        or check.tool in self.complete_tools
                        or (scope is not None and scope not in self.declared_scopes)
                    )
                )
                self.origins[key] = stage if certain and counts[key] == 1 else "unknown"
        current = set(counts)
        if partial:
            current |= {k for k in self.last_failures if k[0] != "terraform.validate"}
        self.last_failures = current
        self.declared_scopes = scopes
        self.observed = True
        self.terraform_complete = not any(
            c.tool == "terraform" and c.status in {"skipped", "failed"} for c in checks
        )
        for tool in {c.tool for c in checks}:
            self.complete_tools.discard(tool)
            if not any(
                c.tool == tool and c.status in {"skipped", "failed"} for c in checks
            ):
                self.complete_tools.add(tool)

    def annotate(
        self, checks: tuple[ValidationCheck, ...]
    ) -> tuple[ValidationCheck, ...]:
        return tuple(
            c.model_copy(
                update={"origin": self.origins.get(self.check_key(c), "unknown")}
            )
            if c.status == "failed"
            else c
            for c in checks
        )

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
