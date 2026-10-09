"""Identify interrupted review retries independently of event publication.

Revision ID: 0003_review_retry_started_at
Revises: 0002_original_files
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_review_retry_started_at"
down_revision = "0002_original_files"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generated_packages",
        sa.Column("review_retry_started_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_packages", "review_retry_started_at")
