"""Reusable candidate checks; never retain unverified security changes."""

import re
import time
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from app.agents.budget import AgentBudget
from app.agents.security.verification import (
    TerraformVerifier,
    failure_count,
    terraform_files,
)
from app.domain.enums import Variant
from app.domain.validation import ValidationCheck
from app.scanners.scan import Scanner, ScanResult
from app.validation.documents import PackageDocuments, blocks, code_text
from app.validation.gate import patch_syntax_failure
from app.validation.preservation import removes_security_controls
from app.validation.references import reference_checks
from app.validation.workspace import ValidationWorkspace, current_workspace


@dataclass
class CandidateResult:
    reason: str | None
    checks: list[ValidationCheck]
    scan: ScanResult
    introduced: list[dict[str, str]]


class CandidateGuard:
    def __init__(
        self,
        verifier: TerraformVerifier,
        scanner: Scanner,
        variant: Variant,
        budget: AgentBudget,
        record: dict[str, Any],
    ):
        self.verifier, self.scanner, self.variant = verifier, scanner, variant
        self.budget, self.record = budget, record
        self.check_cache: dict[str, list[ValidationCheck]] = {}
        self.scan_cache: dict[str, ScanResult] = {}

    def time_left(self) -> None:
        if self.budget.expired():
            raise TimeoutError

    async def checks(self, files: dict[str, str]) -> list[ValidationCheck]:
        self.time_left()
        key = ValidationWorkspace.fingerprint(terraform_files(files))
        if key not in self.check_cache:
            started = time.monotonic()
            try:
                self.check_cache[key] = await self.verifier.checks(files)
            finally:
                self.record["terraform_verification_seconds"] += (
                    time.monotonic() - started
                )
        return self.check_cache[key]

    async def evaluate(
        self,
        before: dict[str, str],
        candidate: dict[str, str],
        checks: list[ValidationCheck],
        scan: ScanResult,
        *,
        force_scan: bool = False,
    ) -> CandidateResult:
        self.time_left()
        touched = {
            p
            for p in before.keys() | candidate.keys()
            if before.get(p) != candidate.get(p)
        }
        if removes_security_controls(before, candidate):
            return CandidateResult("security_control_removed", checks, scan, [])
        syntax_started = time.monotonic()
        try:
            invalid_syntax = await patch_syntax_failure(before, candidate, touched)
        finally:
            self.record["syntax_verification_seconds"] = (
                self.record.get("syntax_verification_seconds", 0.0)
                + time.monotonic()
                - syntax_started
            )
        if invalid_syntax:
            return CandidateResult("invalid_syntax", checks, scan, [])

        def broken_references(
            files: dict[str, str],
        ) -> set[tuple[str, str | None, str]]:
            return {
                (c.check_id, c.file_path, c.message)
                for c in reference_checks(PackageDocuments.parse(files))
                if c.status == "failed"
            }

        if broken_references(candidate) - broken_references(before):
            return CandidateResult("reference_regression", checks, scan, [])

        def declarations(files: dict[str, str]) -> set[tuple[str, str]]:
            return {
                (str(PurePosixPath(doc.path).parent), ".".join(labels))
                for doc in PackageDocuments.parse(files).documents.values()
                if not doc.parse_error
                for labels, _ in blocks(doc.data, "resource")
            }

        for module, removed in declarations(before) - declarations(candidate):
            if any(
                str(PurePosixPath(p).parent) == module
                and re.search(
                    r"(?<![\w.])" + re.escape(removed) + r"(?:\.|\[|\b)",
                    code_text(text, hash_comments=True, mask_strings=False),
                )
                for p, text in candidate.items()
                if p.endswith((".tf", ".tf.json"))
            ):
                return CandidateResult("reference_regression", checks, scan, [])
        after = (
            await self.checks(candidate)
            if terraform_files(before) != terraform_files(candidate)
            else checks
        )
        previous, count = failure_count(checks), failure_count(after)
        changed_terraform = terraform_files(before) != terraform_files(candidate)
        reason = (
            "terraform_regression"
            if changed_terraform
            and count is not None
            and previous is not None
            and count > previous
            else "terraform_verification_unavailable"
            if changed_terraform
            and (count is None or (previous is None and count != 0))
            else None
        )
        if self.budget.expired() and reason:
            self.record.setdefault("reasons", []).append(reason)
            self.record["error_classes"] = sorted(
                {c.message for c in after if c.status == "failed"}
            )
        self.time_left()
        if reason:
            return CandidateResult(reason, after, scan, [])
        key = ValidationWorkspace.fingerprint(candidate)
        if candidate == before and not force_scan:
            scanned = scan
        elif key in self.scan_cache:
            scanned = self.scan_cache[key]
        else:
            started = time.monotonic()
            try:
                scanned = await self.scanner.scan(candidate, self.variant)
                self.scan_cache[key] = scanned
            finally:
                self.record["security_verification_seconds"] += (
                    time.monotonic() - started
                )
        self.time_left()
        baseline = {v.fingerprint() for v in scan.violations if v.blocking}
        introduced = [
            {"rule_id": v.rule_id, "file": v.file_path, "resource": v.resource}
            for v in scanned.violations
            if v.blocking and v.fingerprint() not in baseline
        ]
        workspace = current_workspace()
        if workspace and not introduced:
            workspace.observe(
                after,
                "security_fix",
                candidate,
                partial=True,
                action=self.record.get("verification_action", "focused_fixer"),
            )
        return CandidateResult(
            "new_blocking_findings" if introduced else None, after, scanned, introduced
        )
