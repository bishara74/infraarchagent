"""Explicit optional Fixer lesson scope (FR-S-02, NFR-01)."""

from alembic import op

revision = "0016_fixer_lesson_scope"
down_revision = "0015_lesson_approval_policy"
branch_labels = depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_lesson_role", "lesson_revisions", type_="check")
    op.create_check_constraint(
        "ck_lesson_role",
        "lesson_revisions",
        "scope_role IN ('architect','generator_cost','generator_performance',"
        "'generator_security','all_generators','fixer')",
    )


def downgrade() -> None:
    raise RuntimeError(
        "Fixer lesson history is retained; restore a pre-upgrade backup."
    )
