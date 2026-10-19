"""Freeze all five agent selections and credential reference (FR-P-04)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0010_agent_selections"
down_revision = "0009_credentials"
branch_labels = depends_on = None


def upgrade() -> None:
    op.add_column("pipeline_runs", sa.Column("agent_models", JSONB()))
    op.add_column(
        "pipeline_runs",
        sa.Column("credential_id", sa.Uuid(), sa.ForeignKey("provider_credentials.id")),
    )


def downgrade() -> None:
    op.drop_column("pipeline_runs", "credential_id")
    op.drop_column("pipeline_runs", "agent_models")
