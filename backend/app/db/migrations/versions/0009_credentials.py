"""Encrypted provider credentials and non-secret LLM settings (NFR-01)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0009_credentials"
down_revision = "0008_accounts"
branch_labels = depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_credentials",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("credential_type", sa.String(32), nullable=False),
        sa.Column("api_protocol", sa.String(32), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("nonce", sa.LargeBinary(), nullable=False),
        sa.Column("key_version", sa.Integer(), nullable=False),
        sa.Column("last4", sa.String(4), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "llm_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "default_credential_id", sa.Uuid(), sa.ForeignKey("provider_credentials.id")
        ),
        sa.Column("agent_defaults", JSONB(), nullable=False),
        sa.Column("static_models", JSONB(), nullable=False),
    )
    op.execute("INSERT INTO llm_settings VALUES (1, NULL, '{}'::jsonb, '[]'::jsonb)")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON provider_credentials, llm_settings "
        "TO infraarch_app"
    )


def downgrade() -> None:
    op.drop_table("llm_settings")
    op.drop_table("provider_credentials")
