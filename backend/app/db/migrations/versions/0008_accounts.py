"""User accounts and session binding (NFR-01, FR-UI-07)."""

from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision = "0008_accounts"
down_revision = "0007_legacy_label_provenance"
branch_labels = depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("disabled_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("role IN ('admin','reviewer')", name="ck_user_role"),
    )
    op.create_index(
        "uq_users_username_lower", "users", [sa.text("lower(username)")], unique=True
    )
    op.add_column(
        "auth_sessions", sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"))
    )
    op.add_column(
        "pipeline_runs", sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"))
    )
    op.get_bind().execute(
        sa.text("UPDATE auth_sessions SET revoked_at=:now WHERE revoked_at IS NULL"),
        {"now": datetime.now(UTC)},
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON users TO infraarch_app")


def downgrade() -> None:
    op.drop_column("pipeline_runs", "user_id")
    op.drop_column("auth_sessions", "user_id")
    op.drop_table("users")
