"""Shared Retry/automatic patch merging and verification primitives."""

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any, Protocol

from app.agents.security.fix import FixProposal, content_hash
from app.core.logging import RedactingFilter
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.package_layout import package_structure_errors
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationReport
from app.scanners.scan import Scanner, ScanResult
from app.validation.gate import syntax_checks


class ValidationService(Protocol):
    async def validate(
        self, plan: DeploymentPlan, files: dict[str, str]
    ) -> ValidationReport: ...


def apply_proposals(
    files: dict[str, str],
    proposals: Sequence[FixProposal],
    targets: Mapping[str, Sequence[Violation]],
    plan: DeploymentPlan,
    redactor: RedactingFilter,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Keep Retry's per-proposal acceptance; callers choose round acceptance."""
    current = dict(files)
    results = []
    for proposal in sorted(proposals, key=lambda item: item.path):
        accepted, reason = proposal.accepted, proposal.reason
        if accepted and any(
            name not in current or content_hash(current[name]) != expected
            for name, expected in proposal.edit_bases.items()
        ):
            accepted, reason = False, "stale_edit_base"
        if accepted and any(name not in proposal.edit_bases for name in proposal.edits):
            accepted, reason = False, "edit_base_missing"
        if accepted:
            candidate = dict(current)
            assert proposal.content is not None
            candidate[proposal.path] = proposal.content
            candidate.update(proposal.edits)
            if any(path in candidate for path in proposal.new_files):
                accepted, reason = False, "new_file_conflict"
            else:
                candidate.update(proposal.new_files)
                if package_structure_errors(candidate, plan.file_types):
                    accepted, reason = False, "invalid_merged_structure"
                elif syntax_checks(
                    candidate, {proposal.path, *proposal.edits, *proposal.new_files}
                ):
                    accepted, reason = False, "invalid_merged_syntax"
                else:
                    current = candidate
        results.append(
            {
                "file": proposal.path,
                "rule_ids": sorted({item.rule_id for item in targets[proposal.path]}),
                "accepted": accepted,
                "reason": reason,
                "summaries": [redactor.redact(text) for text in proposal.summaries],
                "new_files": sorted(proposal.new_files) if accepted else [],
                "edits": sorted(proposal.edits) if accepted else [],
                "normalized_existing_paths": list(proposal.normalized_existing_paths),
                "conflicting_paths": list(proposal.conflicting_paths),
                "input_tokens": proposal.input_tokens,
                "output_tokens": proposal.output_tokens,
                "cached_input_tokens": proposal.cached_input_tokens,
                "schema_context_chars": proposal.schema_context_chars,
                "schema_context_reason": proposal.schema_context_reason,
                "failure_category": proposal.failure_category,
                "call_kind": proposal.call_kind,
                "attempt_details": [asdict(a) for a in proposal.attempt_details],
            }
        )
    return current, results


async def validate_files(
    engine: ValidationService, plan: DeploymentPlan, files: dict[str, str]
) -> ValidationReport:
    return await engine.validate(plan, files)


async def scan_files(
    scanner: Scanner, files: dict[str, str], variant: Variant, *, iteration: int = 0
) -> ScanResult:
    return await scanner.scan(files, variant, iteration=iteration)
