"""SELECT-only inspection grants; role is provisioned by cluster bootstrap."""

import sqlalchemy as sa
from alembic import op

revision = "0012_inspection_role"
down_revision = "0011_user_preferences"
branch_labels = depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    if not connection.scalar(
        sa.text(
            "SELECT EXISTS(SELECT FROM pg_roles WHERE rolname='infraarch_readonly')"
        )
    ):
        raise RuntimeError(
            "Provision the inspection role with make prepare-db-tools before migrating."
        )
    op.execute("GRANT USAGE ON SCHEMA public TO infraarch_readonly")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO infraarch_readonly")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT ON TABLES TO infraarch_readonly"
    )
    name = connection.scalar(sa.text("SELECT current_database()"))
    connection.execute(
        sa.text(
            "GRANT CONNECT ON DATABASE "
            + connection.dialect.identifier_preparer.quote(name)
            + " TO infraarch_readonly"
        )
    )


def downgrade() -> None:
    op.execute("REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM infraarch_readonly")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE SELECT ON TABLES FROM infraarch_readonly"
    )
    op.execute("REVOKE USAGE ON SCHEMA public FROM infraarch_readonly")
