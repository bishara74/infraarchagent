"""Record the selected secondary assessment profile (FR-S-04)."""

import sqlalchemy as sa
from alembic import op

revision = "0006_policy_profile"
down_revision = "0005_auth_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "pipeline_runs",
        sa.Column(
            "policy_profile", sa.String(32), nullable=False, server_default="strict"
        ),
    )
    op.create_check_constraint(
        "ck_run_policy_profile",
        "pipeline_runs",
        "policy_profile IN ('strict','contextual-v1')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_run_policy_profile", "pipeline_runs", type_="check")
    op.drop_column("pipeline_runs", "policy_profile")
