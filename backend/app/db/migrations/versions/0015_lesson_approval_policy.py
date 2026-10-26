"""Add direct-admin provenance and approval categories (NFR-01, FR-UI-07)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0015_lesson_approval_policy"
down_revision = "0014_schema_version_read"
branch_labels = depends_on = None


def upgrade() -> None:
    op.add_column("lesson_revisions", sa.Column("approval", sa.String(32)))
    op.add_column("lesson_revisions", sa.Column("approval_actor", JSONB()))
    # Existing immutable sets/events stay byte-identical. Historical identity
    # snapshots remain unknown rather than reconstructed from today's username.
    op.execute("DROP TRIGGER lesson_approval_guard ON lesson_revisions")
    op.execute(
        "UPDATE lesson_revisions SET approval = CASE WHEN self_approved "
        "THEN 'self_approved' ELSE 'admin_reviewed' END "
        "WHERE approved_by IS NOT NULL"
    )
    op.execute("""
        CREATE OR REPLACE FUNCTION protect_lesson_approval() 
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF OLD.status IN ('approved','retired','rejected') AND
             (NEW.approved_by, NEW.approved_at, NEW.self_approved,
              NEW.approval_filter_result, NEW.approval, NEW.approval_actor)
             IS DISTINCT FROM
             (OLD.approved_by, OLD.approved_at, OLD.self_approved,
              OLD.approval_filter_result, OLD.approval, OLD.approval_actor) THEN
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
    op.execute(
        "GRANT UPDATE (approval, approval_actor) ON lesson_revisions TO infraarch_app"
    )
    op.create_check_constraint(
        "ck_lesson_approval",
        "lesson_revisions",
        "approval IS NULL OR approval IN "
        "('admin_direct','admin_reviewed','self_approved')",
    )
    op.drop_constraint("ck_lesson_category", "lesson_revisions", type_="check")
    op.create_check_constraint(
        "ck_lesson_category",
        "lesson_revisions",
        "category IN ('requirements_not_met','too_expensive',"
        "'organisational_policy','security_concern','operability','too_complex',"
        "'other','meets_requirements','accepted_risk','approved_with_follow_ups',"
        "'organisational_exception')",
    )


def downgrade() -> None:
    raise RuntimeError("Approval provenance is retained; restore a pre-upgrade backup.")
