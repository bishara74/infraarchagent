"""Preserve legacy labels and review provenance (FR-S-08/10).

Revision ID: 0004_honest_labels
Revises: 0003_review_retry_started_at
"""

import json
import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0004_honest_labels"
down_revision = "0003_review_retry_started_at"
branch_labels = None
depends_on = None
PACKAGE_STATUS_VALUES = (
    "generating",
    "generated",
    "failed",
    "scanning",
    "remediating",
    "scan_clean",
    "scan_exhausted",
    "scan_error",
    "validating",
    "valid",
    "invalid",
    "validation_error",
    "pending_review",
    "checks_passed",
    "engineer_approved",
    "rejected",
)


def upgrade() -> None:
    op.add_column(
        "generated_packages", sa.Column("review_decision", JSONB(), nullable=True)
    )
    op.drop_constraint("ck_package_status", "generated_packages", type_="check")
    connection = op.get_bind()
    rows = (
        connection.execute(
            sa.text("""
        SELECT p.package_id, p.status, p.security_report, p.validation_report,
               p.review_feedback, e.timestamp, e.payload, e.seq
        FROM generated_packages p
        LEFT JOIN LATERAL (
            SELECT timestamp, payload, seq FROM agent_events
            WHERE run_id = p.run_id AND payload->>'variant' = p.variant
              AND payload->>'kind' = 'package_status' AND new_state = p.status
            ORDER BY seq DESC LIMIT 1
        ) e ON true
        WHERE p.status IN ('production_ready', 'not_production_ready')
    """)
        )
        .mappings()
        .all()
    )
    counts = {
        "checks_passed": 0,
        "engineer_approved": 0,
        "rejected": 0,
        "pending_review": 0,
    }
    for row in rows:
        payload = row["payload"] or {}
        manual = payload.get("review_action") in {"approve", "reject"}
        final = (row["security_report"] or {}).get("final", {})
        valid = (row["validation_report"] or {}).get("summary", {}).get(
            "result"
        ) == "valid"
        target = (
            "rejected"
            if row["status"] == "not_production_ready"
            else "engineer_approved"
            if payload.get("review_action") == "approve"
            else "checks_passed"
            if final.get("outcome") == "clean"
            and not final.get("remaining_blocking")
            and valid
            else "pending_review"
        )
        decision = None
        if manual or target == "rejected":
            decision = {
                "action": payload.get("review_action") or "reject",
                "reviewer_name": None,
                "reason": row["review_feedback"],
                "decided_at": row["timestamp"].isoformat()
                if row["timestamp"]
                else None,
                "identity_basis": "unavailable (legacy record)",
                "legacy_event_seq": row["seq"],
                "original_event_payload": payload,
            }
        connection.execute(
            sa.text(
                "UPDATE generated_packages SET status=:status, "
                "review_decision=CAST(:decision AS jsonb) WHERE package_id=:id"
            ),
            {
                "id": row["package_id"],
                "status": target,
                "decision": json.dumps(decision) if decision else None,
            },
        )
        counts[target] += 1
    literals = ", ".join(repr(v) for v in PACKAGE_STATUS_VALUES)
    op.create_check_constraint(
        "ck_package_status", "generated_packages", f"status IN ({literals})"
    )
    logging.getLogger("alembic.runtime.migration").info(
        "Phase 9g label migration counts: %s", counts
    )


def downgrade() -> None:
    op.drop_constraint("ck_package_status", "generated_packages", type_="check")
    op.execute(
        "UPDATE generated_packages SET status = CASE "
        "WHEN status IN ('checks_passed','engineer_approved') "
        "THEN 'production_ready' WHEN status='rejected' "
        "THEN 'not_production_ready' ELSE status END"
    )
    old = tuple(
        v
        for v in PACKAGE_STATUS_VALUES
        if v not in {"checks_passed", "engineer_approved", "rejected"}
    ) + ("production_ready", "not_production_ready")
    op.create_check_constraint(
        "ck_package_status",
        "generated_packages",
        "status IN (" + ", ".join(repr(v) for v in old) + ")",
    )
    op.drop_column("generated_packages", "review_decision")
