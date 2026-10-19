"""Hashed browser sessions (NFR-01)."""

import sqlalchemy as sa
from alembic import op

revision = "0005_auth_sessions"
down_revision = "0004_honest_labels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("absolute_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON auth_sessions TO infraarch_app")


def downgrade() -> None:
    op.drop_table("auth_sessions")
