"""Retain the generated package as the cumulative remediation diff baseline.

Revision ID: 0002_original_files
Revises: 0001_initial_schema
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002_original_files"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generated_packages", sa.Column("original_files", JSONB(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("generated_packages", "original_files")
