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


def open_plan_conflicts(
    security_report: Mapping[str, Any] | None,
    validation_report: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Project recorded guard rejections only onto still-open exact findings."""
    assessment = (validation_report or {}).get("plan_conformance")
    if isinstance(assessment, Mapping):
        return [
            dict(row)
            for row in [*assessment.get("conflicts", []), *assessment.get("notes", [])]
        ]
    final = security_final(security_report)
    conflicts = list(final.get("plan_conflicts", []))
    for iteration in security_iterations(security_report):
        conflicts.extend(
            (iteration.get("verification") or {}).get("plan_conformance", [])
        )
    for round_ in ((validation_report or {}).get("remediation") or {}).get(
        "rounds", []
    ):
        conflicts.extend(round_.get("plan_conformance", []))
    result: dict[tuple[str, ...], dict[str, Any]] = {}
    for finding in final.get("remaining_blocking", []):
        for conflict in conflicts:
            if not isinstance(conflict, dict):
                continue
            resource = conflict.get("resource", "")
            related = conflict.get("related_resources", [])
            targeted = conflict.get("targeted_findings")
            if targeted and not any(
                all(
                    t.get(k) == finding.get(k)
                    for k in ("rule_id", "resource", "file_path")
                )
                for t in targeted
            ):
                continue
            if (
                finding.get("rule_id")
                not in conflict.get("rule_ids", [conflict.get("rule_id")])
                or (
                    not targeted
                    and conflict.get("file_path")
                    not in {None, finding.get("file_path")}
                )
                or (
                    resource != "unresolved"
                    and str(finding.get("resource", "")).split("[", 1)[0]
                    not in [resource, *related]
                )
                or conflict.get("expected") not in {"public", "private"}
                or conflict.get("assessment") not in {"regression", "unknown"}
            ):
                continue
            row = {
                k: str(conflict.get(k, ""))
                for k in ("service", "property", "expected", "assessment")
            }
            row.update(
                rule_id=finding["rule_id"],
                resource=finding["resource"],
                file_path=finding.get("file_path"),
            )
            result[tuple(str(row[k]) for k in row)] = row
    return list(result.values())


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
    conflicts = open_plan_conflicts(security_report, validation_report)
    if status in {
        PackageStatus.PENDING_REVIEW,
        PackageStatus.ENGINEER_APPROVED,
        PackageStatus.REJECTED,
    }:
        final = security_final(security_report)
        if any(c.get("assessment") == "regression" for c in conflicts):
            reasons.append("plan_conformance_conflict")
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
        "readiness_label": status.value
        if downloadable or status == PackageStatus.PENDING_REVIEW
        else None,
        "downloadable": downloadable,
        "review_available": status == PackageStatus.PENDING_REVIEW
        and run_status in TERMINAL_RUNS,
        "review_actions": (
            ["approve", "retry", "reject"]
            if status == PackageStatus.PENDING_REVIEW
            else ["reject"]
            if status == PackageStatus.CHECKS_PASSED
            else []
        )
        if run_status in TERMINAL_RUNS
        else [],
        "review_reasons": reasons,
        "plan_conflicts": conflicts,
        "retry_targets": retry_targets(files, security_report, validation_report),
    }
