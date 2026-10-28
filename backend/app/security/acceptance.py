"""Reusable candidate checks; never retain unverified security changes."""

import asyncio
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
from app.core.telemetry import span, timed
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationCheck
from app.scanners.scan import Scanner, ScanResult
from app.security.verification_scope import same_unavailability
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
        *,
        plan: DeploymentPlan | None = None,
        targeted: list[Violation] | None = None,
    ):
        self.verifier, self.scanner, self.variant = verifier, scanner, variant
        self.budget, self.record = budget, record
        self.plan, self.targeted = plan, targeted or []
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
        else:
            with span("cache", operation="terraform.validate"):
                pass
        return self.check_cache[key]

    @timed("verification")
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

        old_references = broken_references(before)
        await asyncio.sleep(0)
        self.time_left()
        if broken_references(candidate) - old_references:
            return CandidateResult("reference_regression", checks, scan, [])

        def declarations(files: dict[str, str]) -> set[tuple[str, str]]:
            def build() -> set[tuple[str, str]]:
                return {
                    (str(PurePosixPath(doc.path).parent), ".".join(labels))
                    for doc in PackageDocuments.parse(files).documents.values()
                    if not doc.parse_error
                    for labels, _ in blocks(doc.data, "resource")
                }

            workspace = current_workspace()
            return (
                workspace.cache_index("resources", files, build)
                if workspace
                else build()
            )

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
        observed_before = sum(
            c.check_id == "terraform.validate" and c.status == "failed" for c in checks
        )
        observed_after = sum(
            c.check_id == "terraform.validate" and c.status == "failed" for c in after
        )
        unchanged_unavailability = (
            changed_terraform
            and previous is None
            and count is None
            and same_unavailability(before, candidate, checks, after)
        )
        if unchanged_unavailability:
            self.record["unchanged_terraform_unavailability"] = sorted(
                {c.skip_reason for c in after if c.skip_reason}
            )
        reason = (
            "terraform_regression"
            if changed_terraform and observed_after > observed_before
            else "terraform_verification_unavailable"
            if changed_terraform
            and (count is None or (previous is None and count != 0))
            and not unchanged_unavailability
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
            with span("cache", action="baseline_scan"):
                pass
        elif key in self.scan_cache:
            scanned = self.scan_cache[key]
            with span("cache", action="candidate_scan"):
                pass
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
        self.time_left()
        return CandidateResult(
            "new_blocking_findings" if introduced else None, after, scanned, introduced
        )
