"""Reusable candidate checks; never retain unverified security changes."""

import time
from dataclasses import dataclass
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
from app.validation.gate import patch_syntax_failure
from app.validation.preservation import removes_security_controls
from app.validation.workspace import ValidationWorkspace


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
        self.time_left()
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
        if await patch_syntax_failure(before, candidate, touched):
            return CandidateResult("invalid_syntax", checks, scan, [])
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
        return CandidateResult(
            "new_blocking_findings" if introduced else None, after, scanned, introduced
        )
