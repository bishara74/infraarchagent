"""Shared Retry/automatic patch merging and verification primitives."""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from app.agents.security.fix import FixProposal
from app.core.logging import RedactingFilter
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.package_layout import package_structure_errors
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationReport
from app.scanners.scan import Scanner, ScanResult


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
        if accepted:
            candidate = dict(current)
            assert proposal.content is not None
            candidate[proposal.path] = proposal.content
            if any(path in candidate for path in proposal.new_files):
                accepted, reason = False, "new_file_conflict"
            else:
                candidate.update(proposal.new_files)
                if package_structure_errors(candidate, plan.file_types):
                    accepted, reason = False, "invalid_merged_structure"
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
                "input_tokens": proposal.input_tokens,
                "output_tokens": proposal.output_tokens,
                "cached_input_tokens": proposal.cached_input_tokens,
                "schema_context_chars": proposal.schema_context_chars,
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
