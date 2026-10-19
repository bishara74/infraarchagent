"""Server-authoritative preferences and per-user recent runs (FR-UI-01)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0011_user_preferences"
down_revision = "0010_agent_selections"
branch_labels = depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("data", JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_recent_runs",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column(
            "run_id", sa.Uuid(), sa.ForeignKey("pipeline_runs.run_id"), primary_key=True
        ),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seq", sa.BigInteger(), nullable=False),
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON user_preferences, user_recent_runs "
        "TO infraarch_app"
    )


def downgrade() -> None:
    op.drop_table("user_recent_runs")
    op.drop_table("user_preferences")
