"""Fail closed for legacy success without an automatic transition (FR-S-08/10).

Revision ID: 0007_legacy_label_provenance
Revises: 0006_policy_profile
"""

import logging

import sqlalchemy as sa
from alembic import op

revision = "0007_legacy_label_provenance"
down_revision = "0006_policy_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    rows = (
        connection.execute(
            sa.text("""
        SELECT p.package_id, e.new_state, e.previous_state, e.payload
        FROM generated_packages p
        LEFT JOIN LATERAL (
            SELECT new_state, previous_state, payload FROM agent_events
            WHERE run_id = p.run_id AND payload->>'variant' = p.variant
              AND payload->>'kind' = 'package_status'
            ORDER BY seq DESC LIMIT 1
        ) e ON true
        WHERE p.status = 'checks_passed'
    """)
        )
        .mappings()
        .all()
    )
    counts = {"confirmed_checks_passed": 0, "ambiguous_to_pending_review": 0}
    for row in rows:
        # Current automatic events remain authoritative. Historical rows also
        # need an automatic valid -> production_ready event; report contents
        # alone cannot distinguish an approval whose publication was lost.
        proven = row["new_state"] == "checks_passed" or (
            row["new_state"] == "production_ready"
            and row["previous_state"] == "valid"
            and not (row["payload"] or {}).get("review_action")
        )
        if proven:
            counts["confirmed_checks_passed"] += 1
        else:
            connection.execute(
                sa.text(
                    "UPDATE generated_packages SET status='pending_review' "
                    "WHERE package_id=:id"
                ),
                {"id": row["package_id"]},
            )
            counts["ambiguous_to_pending_review"] += 1
    logging.getLogger("alembic.runtime.migration").info(
        "Phase 9g legacy provenance reconciliation counts: %s", counts
    )


def downgrade() -> None:
    # Restoring an unverifiable success claim would invent provenance.
    pass
