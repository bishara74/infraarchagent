import pytest

from app.domain.enums import PackageStatus as P
from app.domain.enums import RunStatus as R
from app.domain.enums import Variant
from app.domain.states import (
    PACKAGE_TRANSITIONS,
    RUN_TRANSITIONS,
    IllegalTransition,
    assert_package_transition,
    assert_run_transition,
    assert_transition,
    classify_run,
    is_downloadable,
    is_settled,
    readiness_after_validation,
    remediation_budget_decision,
    review_reasons,
)


def test_all_run_edges_and_terminal_freeze() -> None:
    assert set(RUN_TRANSITIONS) == set(R)
    for current, targets in RUN_TRANSITIONS.items():
        for target in targets:
            assert_run_transition(current, target)
    for terminal in (R.SUCCESS, R.PARTIAL_SUCCESS, R.FAILED):
        assert not RUN_TRANSITIONS[terminal]
        for target in R:
            with pytest.raises(IllegalTransition) as caught:
                assert_run_transition(terminal, target)
            assert caught.value.current == terminal
            assert caught.value.target == target
    with pytest.raises(IllegalTransition):
        assert_run_transition(R.CREATED, R.SUCCESS)


@pytest.mark.req("FR-S-07", "FR-S-09")
def test_package_edges_and_full_retry_path() -> None:
    assert set(PACKAGE_TRANSITIONS) == set(P)
    for current, targets in PACKAGE_TRANSITIONS.items():
        for target in targets:
            assert_package_transition(current, target)
    path = [
        P.SCANNING,
        P.REMEDIATING,
        P.SCANNING,
        P.REMEDIATING,
        P.SCAN_EXHAUSTED,
        P.VALIDATING,
        P.VALID,
        P.PENDING_REVIEW,
        P.REMEDIATING,
        P.SCANNING,
        P.SCAN_CLEAN,
        P.VALIDATING,
        P.VALID,
        P.PRODUCTION_READY,
    ]
    for current, target in zip(path, path[1:], strict=False):
        assert_transition(current, target)
    failure = [
        P.SCAN_CLEAN,
        P.VALIDATING,
        P.INVALID,
        P.PENDING_REVIEW,
        P.NOT_PRODUCTION_READY,
    ]
    for current, target in zip(failure, failure[1:], strict=False):
        assert_package_transition(current, target)
    for current, target in (
        (P.VALIDATION_ERROR, P.PRODUCTION_READY),
        (P.SCANNING, P.SCAN_EXHAUSTED),
        (P.FAILED, P.GENERATING),
    ):
        with pytest.raises(IllegalTransition):
            assert_package_transition(current, target)
    for terminal in (
        P.FAILED,
        P.SCAN_ERROR,
        P.PRODUCTION_READY,
        P.NOT_PRODUCTION_READY,
    ):
        assert not PACKAGE_TRANSITIONS[terminal]


@pytest.mark.req("FR-S-03", "FR-S-05")
def test_remediation_budget_is_checked_in_remediating() -> None:
    first = remediation_budget_decision(0, 1)
    assert first.apply_fix and first.target == P.SCANNING
    assert first.next_iteration_count == 1
    exhausted = remediation_budget_decision(first.next_iteration_count, 1)
    assert not exhausted.apply_fix and exhausted.target == P.SCAN_EXHAUSTED
    assert exhausted.next_iteration_count == 1
    for maximum in (1, 2, 3):
        count = 0
        while True:
            decision = remediation_budget_decision(count, maximum)
            assert decision.next_iteration_count <= maximum
            count = decision.next_iteration_count
            if not decision.apply_fix:
                break
        assert count == maximum
    for count, maximum in ((-1, 3), (4, 3), (0, 0)):
        with pytest.raises(ValueError):
            remediation_budget_decision(count, maximum)


@pytest.mark.req("FR-UI-06", "FR-V-05", "FR-S-07")
@pytest.mark.parametrize("scan", [P.SCAN_CLEAN, P.SCAN_EXHAUSTED])
@pytest.mark.parametrize("validation", [P.VALID, P.INVALID, P.VALIDATION_ERROR])
def test_readiness_and_reasons(scan: P, validation: P) -> None:
    result = readiness_after_validation(scan, validation)
    reasons = review_reasons(scan, validation)
    if scan == P.SCAN_CLEAN and validation == P.VALID:
        assert result == P.PRODUCTION_READY
        assert reasons == []
    else:
        assert result == P.PENDING_REVIEW
    assert ("unresolved_violations" in reasons) == (scan == P.SCAN_EXHAUSTED)
    assert ("validation_failed" in reasons) == (validation == P.INVALID)
    assert ("validation_unavailable" in reasons) == (validation == P.VALIDATION_ERROR)


def test_readiness_input_and_downloadability() -> None:
    with pytest.raises(ValueError):
        readiness_after_validation(P.SCANNING, P.VALID)
    with pytest.raises(ValueError):
        review_reasons(P.SCAN_CLEAN, P.SCANNING)
    for status in (P.PENDING_REVIEW, P.INVALID, P.VALIDATION_ERROR):
        assert not is_downloadable(status)
    for status in (P.INVALID, P.VALIDATION_ERROR):
        assert not is_settled(status)
    assert is_settled(P.PENDING_REVIEW)
    assert is_downloadable(P.PRODUCTION_READY)
    assert is_downloadable(P.NOT_PRODUCTION_READY)


def test_classify_run_all_rules() -> None:
    ready = {variant: P.PRODUCTION_READY for variant in Variant}
    assert classify_run(False, {}) == R.FAILED
    assert classify_run(True, {}) == R.FAILED
    assert classify_run(True, {v: P.SCAN_ERROR for v in Variant}) == R.FAILED
    assert classify_run(True, ready) == R.SUCCESS
    assert classify_run(True, {**ready, Variant.COST: P.FAILED}) == R.PARTIAL_SUCCESS
    assert (
        classify_run(True, {**ready, Variant.COST: P.PENDING_REVIEW})
        == R.PARTIAL_SUCCESS
    )
    with pytest.raises(ValueError):
        classify_run(True, {Variant.COST: P.SCANNING})
