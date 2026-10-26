"""Deterministic labelled IaC ZIPs (FR-UI-06, FR-S-10, PR-04)."""

import hashlib
import json
from datetime import datetime
from io import BytesIO
from typing import Any
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from app.domain.enums import PackageStatus, Variant
from app.domain.paths import validate_file_map, validate_relative_path
from app.domain.review import security_final
from app.domain.states import is_downloadable


def runtime_defaults_notes(
    files: dict[str, str],
    *reports: dict[str, Any] | None,
) -> list[str]:
    """Only retained, still-current catalogue evidence belongs in an archive."""
    rows: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, dict):
            if (
                value.get("kind") == "kubernetes_pod_defaults"
                and (
                    value.get("outcome") == "accepted"
                    or value.get("status") == "retained"
                )
                and value.get("runtime_compatibility") == "unverified"
                and isinstance(value.get("file"), str)
                and value["file"] in files
                and value.get("after_hash")
                == hashlib.sha256(files[value["file"]].encode()).hexdigest()
            ):

                def clean(key: str) -> str:
                    return (
                        str(value.get(key) or "unavailable")
                        .replace("`", "")
                        .replace("\n", " ")[:256]
                    )

                rows.add(
                    f"- {clean('workload')} / {clean('container')} "
                    f"({clean('file')}): runtime compatibility unverified. "
                    f"Configuration: {clean('override_location')}."
                )
            for item in value.values():
                visit(item)

    for report in reports:
        visit(report)
    return sorted(rows)


def readiness_document(
    *,
    run_id: UUID,
    variant: Variant,
    status: PackageStatus,
    model: str | None,
    agent_models: dict[str, Any] | None = None,
    labelled_at: datetime | None,
    review_action: str | None,
    feedback: str | None,
    security_report: dict[str, Any] | None,
    validation_report: dict[str, Any] | None,
    retried: bool = False,
    decision: dict[str, Any] | None = None,
    policy_profile: str = "strict",
    assessments: dict[str, Any] | None = None,
    files: dict[str, str] | None = None,
    lessons: dict[str, Any] | None = None,
) -> str:
    if not is_downloadable(status):
        raise ValueError("package is not downloadable")
    label = status.value.replace("_", " ").upper()
    origin = (
        "synthetic benchmark fixture (no engineer decision or executed checks)"
        if (decision or {}).get("identity_basis") == "synthetic benchmark fixture"
        else "engineer decision"
        if status in {PackageStatus.ENGINEER_APPROVED, PackageStatus.REJECTED}
        or review_action in {"approve", "reject"}
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
    blocking_count = (
        len(security["remaining_blocking"])
        if "remaining_blocking" in security
        else "unavailable"
    )
    summary = (validation_report or {}).get("summary", {})
    return "\n".join(
        [
            f"# {label}",
            "",
            f"Run ID: {run_id}",
            f"Variant: {variant.value}",
            f"Model: {model or 'unavailable'}",
            *(
                [
                    f"Lessons used: set v{lessons['set_version']} "
                    f"({lessons['used_count']} lessons)"
                    if lessons.get("used_count")
                    else "Lessons used: none",
                    f"Lesson set SHA-256: {lessons['set_hash']}",
                    *[
                        f"Lesson approval: {entry.get('approval')}; "
                        f"actor: {entry.get('approval_actor')}"
                        for entry in lessons.get("entries", [])
                        if entry.get("id") in lessons.get("used_lesson_ids", [])
                        and entry.get("approval")
                    ],
                    "Self-approved lessons used: "
                    + (
                        "yes — four-eyes review was off"
                        if lessons.get("self_approved")
                        else "no"
                    ),
                ]
                if lessons
                else []
            ),
            "Agent models and thinking modes:",
            *[
                f"- {role}: {selection}"
                for role, selection in (agent_models or {}).items()
            ],
            f"Labelled at: {timestamp}",
            f"Label origin: {origin}",
            "",
            f"Selected secondary profile: {policy_profile}",
            "Strict alone controls the official label and template acceptance.",
            "## Profile assessments",
            *[
                f"{name}: checks passed={view.get('checks_passed')}; "
                f"remaining blocking={view.get('remaining_blocking')}"
                for name, view in (assessments or {}).items()
            ],
            "Contextual results are experimental; supervisor approval is required.",
            *[
                f"- excepted: {f.get('rule_id')} / {f.get('resource')} "
                f"[{f.get('entry_id')}] — {f.get('justification')}"
                for view in (assessments or {}).values()
                for f in view.get("excepted", [])
            ],
            "",
            "## Engineer decision",
            f"Decision: {(decision or {}).get('action', 'none')}",
            f"Reviewer: {(decision or {}).get('reviewer_name') or 'unavailable'} — "
            f"{(decision or {}).get('identity_basis', 'unavailable')}",
            f"Decision time: {(decision or {}).get('decided_at') or 'unavailable'}",
            *(
                [f"Category: {decision.get('category') or 'not recorded'}"]
                if decision
                else []
            ),
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
            f"Passed: {summary.get('passed', 'unavailable')}; "
            f"failed: {summary.get('failed', 'unavailable')}; "
            f"warnings: {summary.get('warnings', 'unavailable')}; "
            f"skipped: {summary.get('skipped', 'unavailable')}",
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
            "## Kubernetes catalogue defaults",
            *(
                runtime_defaults_notes(files or {}, security_report, validation_report)
                or ["No retained, current catalogue records available."]
            ),
            "",
        ]
    )


def package_zip(
    files: dict[str, str], readiness: str, lessons: dict[str, Any] | None = None
) -> bytes:
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
    if lessons is not None:
        lesson_path = "_infraarchagent/LESSONS.json"
        number = 2
        while lesson_path.casefold() in {path.casefold() for path in entries}:
            lesson_path = f"_infraarchagent/LESSONS-{number}.json"
            number += 1
        entries[lesson_path] = (
            json.dumps(lessons, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        )
    return _zip_entries(
        {path: content.encode("utf-8") for path, content in entries.items()}
    )


def _zip_entries(entries: dict[str, bytes]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(entries):
            validate_relative_path(path)
            info = ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                entries[path],
                compress_type=ZIP_DEFLATED,
                compresslevel=6,
            )
    return buffer.getvalue()


def bundle_zip(
    run_id: UUID,
    packages: dict[Variant, tuple[bytes, str, str]],
    *,
    lessons: dict[str, Any] | None = None,
) -> bytes:
    """Flatten the unchanged individual ZIP payloads, retaining verifiable hashes."""
    entries: dict[str, bytes] = {}
    variants = {}
    table = []
    for variant in Variant:
        data, filename, label = packages[variant]
        digest = hashlib.sha256(data).hexdigest()
        variants[variant.value] = {
            "readiness_label": label,
            "single_variant_zip": {"filename": filename, "sha256": digest},
        }
        with ZipFile(BytesIO(data)) as archive:
            for name in archive.namelist():
                validate_relative_path(name)
                entries[f"{variant.value}/{name}"] = archive.read(name)
        table.append(f"| {variant.value} | {label} | {filename} | {digest} |")
    entries["README.md"] = (
        f"# InfraArchAgent — all three variants\n\nRun ID: {run_id}\n\n"
        "| Variant | Readiness label | Individual ZIP | SHA-256 |\n"
        "|---|---|---|---|\n" + "\n".join(table) + "\n\n"
        "Each variant folder contains exactly its individual download's payload, "
        "including its readiness document. Labels describe static checks and "
        "engineer decisions, not a deployment.\n\n"
        "manifest.json lists the SHA-256 of every included file except itself, "
        "including this README. Compare individual ZIP hashes only for the same "
        "run and unchanged readiness snapshot. No manifest can hash itself.\n"
    ).encode("utf-8")
    manifest = {
        "schema_version": 1,
        "run_id": str(run_id),
        "variants": variants,
        **({"lessons": lessons} if lessons is not None else {}),
        "files": {
            path: hashlib.sha256(data).hexdigest()
            for path, data in sorted(entries.items())
        },
    }
    entries["manifest.json"] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return _zip_entries(entries)
