"""SQLAlchemy mapping of the Phase 0 schema."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    run_id: Mapped[UUID] = mapped_column(primary_key=True)
    policy_profile: Mapped[str] = mapped_column(
        String(32), default="strict", server_default="strict"
    )
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    agent_models: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    lessons: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    credential_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("provider_credentials.id")
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    llm_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(128))
    max_iterations: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class GeneratedPackage(Base):
    __tablename__ = "generated_packages"

    package_id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipeline_runs.run_id", ondelete="RESTRICT"), nullable=False
    )
    variant: Mapped[str] = mapped_column(String(16), nullable=False)
    files: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    original_files: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    security_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    validation_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    remediation_diff: Mapped[str | None] = mapped_column(Text)
    iteration_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    review_decision: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    review_feedback: Mapped[str | None] = mapped_column(Text)
    review_retry_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class AgentEvent(Base):
    __tablename__ = "agent_events"

    event_id: Mapped[UUID] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True, cache=1),
        unique=True,
        nullable=False,
    )
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipeline_runs.run_id", ondelete="RESTRICT"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(32))
    new_state: Mapped[str] = mapped_column(String(32), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderCredential(Base):
    __tablename__ = "provider_credentials"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32))
    label: Mapped[str] = mapped_column(String(120))
    base_url: Mapped[str] = mapped_column(Text)
    credential_type: Mapped[str] = mapped_column(String(32))
    api_protocol: Mapped[str] = mapped_column(String(32))
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary)
    nonce: Mapped[bytes] = mapped_column(LargeBinary)
    key_version: Mapped[int] = mapped_column(Integer)
    last4: Mapped[str] = mapped_column(String(4))
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LLMSettings(Base):
    __tablename__ = "llm_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    default_credential_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("provider_credentials.id")
    )
    agent_defaults: Mapped[dict[str, Any]] = mapped_column(JSONB)
    static_models: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    revision: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class UserRecentRun(Base):
    __tablename__ = "user_recent_runs"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("pipeline_runs.run_id"), primary_key=True
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seq: Mapped[int] = mapped_column(BigInteger)


class LessonRevision(Base):
    __tablename__ = "lesson_revisions"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    lesson_id: Mapped[UUID]
    revision: Mapped[int] = mapped_column(Integer)
    previous_id: Mapped[UUID | None] = mapped_column(ForeignKey("lesson_revisions.id"))
    decision_id: Mapped[UUID] = mapped_column(ForeignKey("agent_events.event_id"))
    proposer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    scope_role: Mapped[str] = mapped_column(String(32))
    applies_to: Mapped[list[str]] = mapped_column(JSONB)
    category: Mapped[str] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(String(280))
    status: Mapped[str] = mapped_column(String(16))
    filter_result: Mapped[dict[str, Any]] = mapped_column(JSONB)
    approval_filter_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    self_approved: Mapped[bool] = mapped_column(Boolean, default=False)


class LessonSet(Base):
    __tablename__ = "lesson_sets"
    version: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    sha256: Mapped[str] = mapped_column(String(64))
    entries: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LessonControl(Base):
    __tablename__ = "lesson_control"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    runtime_enabled: Mapped[bool] = mapped_column(Boolean)
    disable_generation: Mapped[int] = mapped_column(Integer)
    set_version: Mapped[int] = mapped_column(ForeignKey("lesson_sets.version"))


class LessonAuditEvent(Base):
    __tablename__ = "lesson_audit_events"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(BigInteger, Identity(always=True, cache=1))
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(32))
    revision_id: Mapped[UUID | None] = mapped_column(ForeignKey("lesson_revisions.id"))
    previous_version: Mapped[UUID | None] = mapped_column(
        ForeignKey("lesson_revisions.id")
    )
    set_version: Mapped[int | None] = mapped_column(ForeignKey("lesson_sets.version"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)


class LessonConfirmation(Base):
    __tablename__ = "lesson_confirmations"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    session_hash: Mapped[str] = mapped_column(String(64))
    revision_id: Mapped[UUID] = mapped_column(ForeignKey("lesson_revisions.id"))
    preview_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
