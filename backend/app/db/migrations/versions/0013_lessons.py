"""Versioned human-curated lessons; append-only sets/audits (NFR-01)."""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0013_lessons"
down_revision = "0012_inspection_role"
branch_labels = depends_on = None


def upgrade() -> None:
    op.add_column("pipeline_runs", sa.Column("lessons", JSONB()))
    op.create_table(
        "lesson_revisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("previous_id", sa.Uuid(), sa.ForeignKey("lesson_revisions.id")),
        sa.Column(
            "decision_id",
            sa.Uuid(),
            sa.ForeignKey("agent_events.event_id"),
            nullable=False,
        ),
        sa.Column("proposer_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scope_role", sa.String(32), nullable=False),
        sa.Column("applies_to", JSONB(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("text", sa.String(280), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("filter_result", JSONB(), nullable=False),
        sa.Column("approval_filter_result", JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("self_approved", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("lesson_id", "revision", name="uq_lesson_revision"),
        sa.CheckConstraint(
            "status IN ('proposed','approved','retired','rejected')",
            name="ck_lesson_status",
        ),
        sa.CheckConstraint(
            "revision > 0 AND length(text) BETWEEN 1 AND 280", name="ck_lesson_bounds"
        ),
        sa.CheckConstraint(
            "scope_role IN ('architect','generator_cost',"
            "'generator_performance','generator_security','all_generators')",
            name="ck_lesson_role",
        ),
        sa.CheckConstraint(
            "category IN ('requirements_not_met','too_expensive',"
            "'organisational_policy','security_concern','operability',"
            "'too_complex','other')",
            name="ck_lesson_category",
        ),
    )
    op.create_index(
        "uq_lesson_active",
        "lesson_revisions",
        ["lesson_id"],
        unique=True,
        postgresql_where=sa.text("status = 'approved'"),
    )
    op.create_table(
        "lesson_sets",
        sa.Column("version", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("entries", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "lesson_control",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("runtime_enabled", sa.Boolean(), nullable=False),
        sa.Column("disable_generation", sa.Integer(), nullable=False),
        sa.Column(
            "set_version",
            sa.Integer(),
            sa.ForeignKey("lesson_sets.version"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "id = 1 AND disable_generation >= 0", name="ck_lesson_control"
        ),
    )
    op.create_table(
        "lesson_audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "seq",
            sa.BigInteger(),
            sa.Identity(always=True, cache=1),
            unique=True,
            nullable=False,
        ),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("revision_id", sa.Uuid(), sa.ForeignKey("lesson_revisions.id")),
        sa.Column("previous_version", sa.Uuid(), sa.ForeignKey("lesson_revisions.id")),
        sa.Column("set_version", sa.Integer(), sa.ForeignKey("lesson_sets.version")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
    )
    op.create_table(
        "lesson_confirmations",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_hash", sa.String(64), nullable=False),
        sa.Column(
            "revision_id",
            sa.Uuid(),
            sa.ForeignKey("lesson_revisions.id"),
            nullable=False,
        ),
        sa.Column("preview_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
    )
    # Content cannot be updated, including while proposed. New text means a new row.
    op.execute(
        "GRANT SELECT, INSERT ON lesson_revisions, lesson_sets, "
        "lesson_audit_events, lesson_confirmations TO infraarch_app"
    )
    op.execute(
        "GRANT UPDATE (status, approved_by, approved_at, self_approved, "
        "approval_filter_result) ON lesson_revisions TO infraarch_app"
    )
    op.execute("GRANT UPDATE (consumed_at) ON lesson_confirmations TO infraarch_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON lesson_control TO infraarch_app")
    # Approval provenance must remain fixed when a lesson is later retired.
    op.execute("""
        CREATE FUNCTION protect_lesson_approval() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF OLD.status IN ('approved','retired','rejected') AND
             (NEW.approved_by, NEW.approved_at, NEW.self_approved,
              NEW.approval_filter_result) IS DISTINCT FROM
             (OLD.approved_by, OLD.approved_at, OLD.self_approved,
              OLD.approval_filter_result) THEN
            RAISE EXCEPTION 'immutable lesson approval' USING ERRCODE = '23514';
          END IF;
          IF NOT ((OLD.status = 'proposed' AND NEW.status IN ('approved','rejected'))
                  OR (OLD.status = 'approved' AND NEW.status = 'retired')) THEN
            RAISE EXCEPTION 'invalid lesson transition' USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END $$
    """)
    op.execute(
        "CREATE TRIGGER lesson_approval_guard BEFORE UPDATE ON lesson_revisions "
        "FOR EACH ROW EXECUTE FUNCTION protect_lesson_approval()"
    )
    op.get_bind().execute(
        sa.text(
            "INSERT INTO lesson_sets (version, sha256, entries, created_at) "
            "VALUES (0, :hash, '[]'::jsonb, :now)"
        ),
        {
            "hash": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
            "now": datetime.now(UTC),
        },
    )
    op.execute("INSERT INTO lesson_control VALUES (1, false, 0, 0)")


def downgrade() -> None:
    op.drop_table("lesson_confirmations")
    op.drop_table("lesson_audit_events")
    op.drop_table("lesson_control")
    op.drop_table("lesson_sets")
    op.drop_table("lesson_revisions")
    op.execute("DROP FUNCTION protect_lesson_approval()")
    op.drop_column("pipeline_runs", "lessons")
