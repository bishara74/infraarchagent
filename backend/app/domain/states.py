"""Pure transition rules for runs, packages, and review readiness."""

from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.enums import PackageStatus, RunStatus, Variant


class IllegalTransition(ValueError):
    def __init__(
        self, current: RunStatus | PackageStatus, target: RunStatus | PackageStatus
    ) -> None:
        self.current = current
        self.target = target
        super().__init__(f"illegal transition: {current} -> {target}")


RUN_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.CREATED: frozenset({RunStatus.RUNNING}),
    RunStatus.RUNNING: frozenset(
        {RunStatus.SUCCESS, RunStatus.PARTIAL_SUCCESS, RunStatus.FAILED}
    ),
    RunStatus.SUCCESS: frozenset(),
    RunStatus.PARTIAL_SUCCESS: frozenset(),
    RunStatus.FAILED: frozenset(),
}

PACKAGE_TRANSITIONS: dict[PackageStatus, frozenset[PackageStatus]] = {
    PackageStatus.GENERATING: frozenset(
        {PackageStatus.GENERATED, PackageStatus.FAILED}
    ),
    PackageStatus.GENERATED: frozenset({PackageStatus.SCANNING}),
    PackageStatus.FAILED: frozenset(),
    PackageStatus.SCANNING: frozenset(
        {
            PackageStatus.REMEDIATING,
            PackageStatus.SCAN_CLEAN,
            PackageStatus.SCAN_ERROR,
        }
    ),
    PackageStatus.REMEDIATING: frozenset(
        {PackageStatus.SCANNING, PackageStatus.SCAN_EXHAUSTED}
    ),
    PackageStatus.SCAN_CLEAN: frozenset({PackageStatus.VALIDATING}),
    PackageStatus.SCAN_EXHAUSTED: frozenset({PackageStatus.VALIDATING}),
    PackageStatus.SCAN_ERROR: frozenset(),
    PackageStatus.VALIDATING: frozenset(
        {
            PackageStatus.VALID,
            PackageStatus.INVALID,
            PackageStatus.VALIDATION_ERROR,
        }
    ),
    PackageStatus.VALID: frozenset(
        {PackageStatus.PRODUCTION_READY, PackageStatus.PENDING_REVIEW}
    ),
    PackageStatus.INVALID: frozenset({PackageStatus.PENDING_REVIEW}),
    PackageStatus.VALIDATION_ERROR: frozenset({PackageStatus.PENDING_REVIEW}),
    PackageStatus.PENDING_REVIEW: frozenset(
        {
            PackageStatus.PRODUCTION_READY,
            PackageStatus.NOT_PRODUCTION_READY,
            PackageStatus.REMEDIATING,
        }
    ),
    PackageStatus.PRODUCTION_READY: frozenset(),
    PackageStatus.NOT_PRODUCTION_READY: frozenset(),
}

PACKAGE_TERMINAL = frozenset(
    {
        PackageStatus.FAILED,
        PackageStatus.SCAN_ERROR,
        PackageStatus.PRODUCTION_READY,
        PackageStatus.NOT_PRODUCTION_READY,
    }
)


def assert_run_transition(current: RunStatus, target: RunStatus) -> None:
    if target not in RUN_TRANSITIONS[current]:
        raise IllegalTransition(current, target)


def assert_package_transition(current: PackageStatus, target: PackageStatus) -> None:
    if target not in PACKAGE_TRANSITIONS[current]:
        raise IllegalTransition(current, target)


def assert_transition(
    current: RunStatus | PackageStatus, target: RunStatus | PackageStatus
) -> None:
    if isinstance(current, RunStatus) and isinstance(target, RunStatus):
        assert_run_transition(current, target)
    elif isinstance(current, PackageStatus) and isinstance(target, PackageStatus):
        assert_package_transition(current, target)
    else:
        raise IllegalTransition(current, target)


@dataclass(frozen=True)
class RemediationDecision:
    apply_fix: bool
    target: PackageStatus
    next_iteration_count: int


def remediation_budget_decision(
    iteration_count: int, max_iterations: int
) -> RemediationDecision:
    """Decide in remediating; count only a completed fix pass (CL-01)."""
    if max_iterations < 1 or not 0 <= iteration_count <= max_iterations:
        raise ValueError("invalid remediation iteration budget")
    if iteration_count == max_iterations:
        return RemediationDecision(False, PackageStatus.SCAN_EXHAUSTED, iteration_count)
    return RemediationDecision(True, PackageStatus.SCANNING, iteration_count + 1)


def readiness_after_validation(
    scan_outcome: PackageStatus, validation_outcome: PackageStatus
) -> PackageStatus:
    if scan_outcome not in {
        PackageStatus.SCAN_CLEAN,
        PackageStatus.SCAN_EXHAUSTED,
    } or validation_outcome not in {
        PackageStatus.VALID,
        PackageStatus.INVALID,
        PackageStatus.VALIDATION_ERROR,
    }:
        raise ValueError("invalid scan or validation outcome")
    if (
        scan_outcome == PackageStatus.SCAN_CLEAN
        and validation_outcome == PackageStatus.VALID
    ):
        return PackageStatus.PRODUCTION_READY
    return PackageStatus.PENDING_REVIEW


def review_reasons(
    scan_outcome: PackageStatus, validation_outcome: PackageStatus
) -> list[str]:
    readiness_after_validation(scan_outcome, validation_outcome)
    reasons: list[str] = []
    if scan_outcome == PackageStatus.SCAN_EXHAUSTED:
        reasons.append("unresolved_violations")
    if validation_outcome == PackageStatus.INVALID:
        reasons.append("validation_failed")
    if validation_outcome == PackageStatus.VALIDATION_ERROR:
        reasons.append("validation_unavailable")
    return reasons


def is_settled(status: PackageStatus) -> bool:
    return status in PACKAGE_TERMINAL or status == PackageStatus.PENDING_REVIEW


def is_downloadable(status: PackageStatus) -> bool:
    return status in {
        PackageStatus.PRODUCTION_READY,
        PackageStatus.NOT_PRODUCTION_READY,
    }


def classify_run(
    architect_succeeded: bool, packages: Mapping[Variant, PackageStatus | None]
) -> RunStatus:
    outcomes = [packages.get(variant) for variant in Variant]
    if any(status is not None and not is_settled(status) for status in outcomes):
        raise ValueError("run has an unsettled package")
    if not architect_succeeded:
        return RunStatus.FAILED
    available = [
        status
        for status in outcomes
        if status is not None
        and status not in {PackageStatus.FAILED, PackageStatus.SCAN_ERROR}
    ]
    if not available:
        return RunStatus.FAILED
    if all(status == PackageStatus.PRODUCTION_READY for status in outcomes):
        return RunStatus.SUCCESS
    return RunStatus.PARTIAL_SUCCESS
