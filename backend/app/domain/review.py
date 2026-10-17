"""Pure Phase 7 package presentation and ordered remediation targets."""

from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from app.domain.enums import PackageStatus, RunStatus
from app.domain.states import is_downloadable

TERMINAL_RUNS = frozenset(
    {RunStatus.SUCCESS, RunStatus.PARTIAL_SUCCESS, RunStatus.FAILED}
)
RETRY_ABORT_PREFIX = "review retry "


def security_iterations(
    report: Mapping[str, Any] | None,
) -> Iterator[Mapping[str, Any]]:
    """Canonical retained sessions take precedence over a legacy top-level alias."""
    if not report:
        return
    sessions = report.get("sessions")
    containers = sessions if isinstance(sessions, list) else [report]
    for session in containers:
        if not isinstance(session, Mapping):
            continue
        for iteration in session.get("iterations", []):
            if isinstance(iteration, Mapping):
                yield iteration


def security_final(report: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not report:
        return {}
    if isinstance(report.get("final"), dict):
        return report["final"]  # type: ignore[no-any-return]
    sessions = report.get("sessions") or []
    return sessions[-1].get("final", {}) if sessions else {}


def retry_targets(
    files: Mapping[str, str],
    security_report: Mapping[str, Any] | None,
    validation_report: Mapping[str, Any] | None,
    explicit: Sequence[str] = (),
) -> list[str]:
    groups = (
        [
            item.get("file_path")
            for item in security_final(security_report).get("remaining_blocking", [])
        ],
        [
            item.get("file_path")
            for item in (validation_report or {}).get(
                "failed_checks_for_remediation", []
            )
        ],
        explicit,
    )
    ordered: dict[str, None] = {}
    for group in groups:
        for path in sorted({p for p in group if isinstance(p, str) and p in files}):
            ordered.setdefault(path, None)
    return list(ordered)


def package_presentation(
    run_status: RunStatus,
    status: PackageStatus,
    files: Mapping[str, str],
    security_report: Mapping[str, Any] | None,
    validation_report: Mapping[str, Any] | None,
    error: str | None,
) -> dict[str, Any]:
    reasons = []
    if status == PackageStatus.PENDING_REVIEW:
        final = security_final(security_report)
        if final.get("remaining_blocking") or final.get("outcome") == "exhausted":
            reasons.append("unresolved_security_findings")
        result = (validation_report or {}).get("summary", {}).get("result")
        if result == "invalid":
            reasons.append("validation_failed")
        elif result in {None, "error"}:
            reasons.append("validation_error")
        if error and error.startswith(RETRY_ABORT_PREFIX):
            reasons.append("retry_aborted")
    downloadable = is_downloadable(status)
    return {
        "readiness_label": status.value if downloadable else None,
        "downloadable": downloadable,
        "review_available": status == PackageStatus.PENDING_REVIEW
        and run_status in TERMINAL_RUNS,
        "review_reasons": reasons,
        "retry_targets": retry_targets(files, security_report, validation_report),
    }
