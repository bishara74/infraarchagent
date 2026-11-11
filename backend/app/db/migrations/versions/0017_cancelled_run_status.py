# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Allow the cancelled terminal run status (FR-P-01, FR-P-04)."""

from alembic import op

revision = "0017_cancelled_run_status"
down_revision = "0016_fixer_lesson_scope"
branch_labels = depends_on = None

RUN_STATUS_VALUES = (
    "created",
    "running",
    "success",
    "partial_success",
    "failed",
    "cancelled",
)


def upgrade() -> None:
    op.drop_constraint("ck_run_status", "pipeline_runs", type_="check")
    allowed = ",".join(f"'{value}'" for value in RUN_STATUS_VALUES)
    op.create_check_constraint(
        "ck_run_status", "pipeline_runs", f"status IN ({allowed})"
    )


def downgrade() -> None:
    # PostgreSQL rejects this constraint if any cancelled runs are retained.
    op.drop_constraint("ck_run_status", "pipeline_runs", type_="check")
    allowed = ",".join(
        f"'{value}'" for value in RUN_STATUS_VALUES if value != "cancelled"
    )
    op.create_check_constraint(
        "ck_run_status", "pipeline_runs", f"status IN ({allowed})"
    )
