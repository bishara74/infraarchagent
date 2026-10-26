"""NFR-01: allow the application to check migration compatibility read-only."""

from alembic import op

revision = "0014_schema_version_read"
down_revision = "0013_lessons"
branch_labels = depends_on = None


def upgrade() -> None:
    op.execute("GRANT SELECT ON alembic_version TO infraarch_app")


def downgrade() -> None:
    op.execute("REVOKE SELECT ON alembic_version FROM infraarch_app")
