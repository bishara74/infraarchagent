"""Deterministic labelled IaC ZIPs (FR-UI-06, FR-S-10, PR-04)."""

from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from app.domain.enums import PackageStatus, Variant
from app.domain.paths import validate_file_map, validate_relative_path
from app.domain.review import security_final
from app.domain.states import is_downloadable


def readiness_document(
    *,
    run_id: UUID,
    variant: Variant,
    status: PackageStatus,
    model: str | None,
    labelled_at: datetime | None,
    review_action: str | None,
    feedback: str | None,
    security_report: dict[str, Any] | None,
    validation_report: dict[str, Any] | None,
    retried: bool = False,
    decision: dict[str, Any] | None = None,
) -> str:
    if not is_downloadable(status):
        raise ValueError("package is not downloadable")
    label = status.value.replace("_", " ").upper()
    origin = (
        "engineer decision"
        if review_action in {"approve", "reject"}
        else "automatic after an engineer-requested retry "
        "(clean scan and valid validation)"
        if labelled_at and retried
        else "automatic (clean scan and valid validation)"
        if labelled_at
        else "unavailable (transition event not recorded)"
    )
    timestamp = (
        labelled_at.isoformat()
        if labelled_at
        else "unavailable (transition event not recorded)"
    )
    security = security_final(security_report)
    blocking_count = len(security.get("remaining_blocking", []))
    summary = (validation_report or {}).get("summary", {})
    return "\n".join(
        [
            f"# {label}",
            "",
            f"Run ID: {run_id}",
            f"Variant: {variant.value}",
            f"Model: {model or 'unavailable'}",
            f"Labelled at: {timestamp}",
            f"Label origin: {origin}",
            "",
            "## Engineer decision",
            f"Decision: {(decision or {}).get('action', 'none')}",
            f"Reviewer: {(decision or {}).get('reviewer_name') or 'unavailable'} — "
            f"{(decision or {}).get('identity_basis', 'unavailable')}",
            f"Decision time: {(decision or {}).get('decided_at') or 'unavailable'}",
            f"Reason: {(decision or {}).get('reason') or 'unavailable'}",
            "",
            "## Review feedback",
            feedback or "None",
            "",
            "## Security summary",
            f"Scan outcome: {security.get('outcome', 'unavailable')}",
            f"Remaining blocking findings: {blocking_count}",
            "",
            "## Validation summary",
            f"Result: {summary.get('result', 'unavailable')}",
            f"Passed: {summary.get('passed', 0)}; failed: {summary.get('failed', 0)}; "
            f"warnings: {summary.get('warnings', 0)}; "
            f"skipped: {summary.get('skipped', 0)}",
            "",
            "## Remaining findings and failed checks",
            *[
                f"- {f.get('rule_id', 'unavailable')} — "
                f"{f.get('resource', 'unavailable')} "
                f"({f.get('file_path', 'unavailable')})"
                for f in security.get("remaining_blocking", [])
            ],
            *[
                f"- {c.get('check_id', 'unavailable')}: "
                f"{c.get('message', 'unavailable')}"
                for c in (validation_report or {}).get("checks", [])
                if c.get("status") == "failed"
            ],
            "No label implies a successful cloud deployment. "
            "These are static checks only.",
            "",
        ]
    )


def package_zip(files: dict[str, str], readiness: str) -> bytes:
    safe = validate_file_map(files)
    occupied = {path.casefold() for path in safe}
    readiness_path = "INFRAARCHAGENT_READINESS.md"
    if readiness_path.casefold() in occupied:
        readiness_path = "_infraarchagent/READINESS.md"
        number = 2
        while readiness_path.casefold() in occupied:
            readiness_path = f"_infraarchagent/READINESS-{number}.md"
            number += 1
    entries = {**safe, readiness_path: readiness}
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(entries):
            validate_relative_path(path)
            info = ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                entries[path].encode("utf-8"),
                compress_type=ZIP_DEFLATED,
                compresslevel=6,
            )
    return buffer.getvalue()
