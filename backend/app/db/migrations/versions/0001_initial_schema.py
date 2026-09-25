"""Initial schema and least-privilege app grants.

Revision ID: 0001_initial_schema
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

# Deliberately literal: the parity test catches drift from domain enums.
RUN_STATUS_VALUES = (
    "created",
    "running",
    "success",
    "partial_success",
    "failed",
)
PACKAGE_STATUS_VALUES = (
    "generating",
    "generated",
    "failed",
    "scanning",
    "remediating",
    "scan_clean",
    "scan_exhausted",
    "scan_error",
    "validating",
    "valid",
    "invalid",
    "validation_error",
    "pending_review",
    "production_ready",
    "not_production_ready",
)
VARIANT_VALUES = ("cost", "performance", "security")
LLM_PROVIDER_VALUES = ("anthropic", "openai", "stub")
AGENT_NAME_VALUES = (
    "orchestrator",
    "architect",
    "generator_cost",
    "generator_performance",
    "generator_security",
    "security",
    "validator",
)


def enum_check(column: str, values: tuple[str, ...]) -> str:
    literals = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({literals})"


def upgrade() -> None:
    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", sa.Uuid(), primary_key=True),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("llm_provider", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128)),
        sa.Column("max_iterations", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.CheckConstraint(
            enum_check("status", RUN_STATUS_VALUES), name="ck_run_status"
        ),
        sa.CheckConstraint(
            enum_check("llm_provider", LLM_PROVIDER_VALUES), name="ck_run_provider"
        ),
        sa.CheckConstraint("max_iterations >= 1", name="ck_run_max_iterations"),
    )
    op.create_index("ix_pipeline_runs_start_time", "pipeline_runs", ["start_time"])

    op.create_table(
        "generated_packages",
        sa.Column("package_id", sa.Uuid(), primary_key=True),
        sa.Column(
            "run_id",
            sa.Uuid(),
            sa.ForeignKey("pipeline_runs.run_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("variant", sa.String(16), nullable=False),
        sa.Column(
            "files", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("security_report", JSONB()),
        sa.Column("validation_report", JSONB()),
        sa.Column("remediation_diff", sa.Text()),
        sa.Column("iteration_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("review_feedback", sa.Text()),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "variant", name="uq_package_run_variant"),
        sa.CheckConstraint(
            enum_check("variant", VARIANT_VALUES), name="ck_package_variant"
        ),
        sa.CheckConstraint("jsonb_typeof(files) = 'object'", name="ck_package_files"),
        sa.CheckConstraint("iteration_count >= 0", name="ck_package_iterations"),
        sa.CheckConstraint(
            enum_check("status", PACKAGE_STATUS_VALUES), name="ck_package_status"
        ),
    )
    op.create_index(
        "ix_generated_packages_created_at", "generated_packages", ["created_at"]
    )

    op.create_table(
        "agent_events",
        sa.Column("event_id", sa.Uuid(), primary_key=True),
        # CACHE 1 prevents different sessions from preallocating sequence ranges.
        sa.Column(
            "seq", sa.BigInteger(), sa.Identity(always=True, cache=1), nullable=False
        ),
        sa.Column(
            "run_id",
            sa.Uuid(),
            sa.ForeignKey("pipeline_runs.run_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(32), nullable=False),
        sa.Column("previous_state", sa.String(32)),
        sa.Column("new_state", sa.String(32), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column(
            "payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.UniqueConstraint("seq", name="uq_agent_events_seq"),
        sa.CheckConstraint(
            enum_check("agent_name", AGENT_NAME_VALUES), name="ck_event_agent"
        ),
        sa.CheckConstraint("jsonb_typeof(payload) = 'object'", name="ck_event_payload"),
    )
    op.create_index("ix_agent_events_run_seq", "agent_events", ["run_id", "seq"])

    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA public TO infraarch_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON pipeline_runs TO infraarch_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON generated_packages TO infraarch_app"
    )
    op.execute("GRANT SELECT, INSERT ON agent_events TO infraarch_app")


def downgrade() -> None:
    op.drop_table("agent_events")
    op.drop_table("generated_packages")
    op.drop_table("pipeline_runs")
