"""Shared domain vocabulary persisted as string values."""

from enum import StrEnum


class RunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class PackageStatus(StrEnum):
    GENERATING = "generating"
    GENERATED = "generated"
    FAILED = "failed"
    SCANNING = "scanning"
    REMEDIATING = "remediating"
    SCAN_CLEAN = "scan_clean"
    SCAN_EXHAUSTED = "scan_exhausted"
    SCAN_ERROR = "scan_error"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    VALIDATION_ERROR = "validation_error"
    PENDING_REVIEW = "pending_review"
    PRODUCTION_READY = "production_ready"
    NOT_PRODUCTION_READY = "not_production_ready"


class Variant(StrEnum):
    COST = "cost"
    PERFORMANCE = "performance"
    SECURITY = "security"


class LLMProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    STUB = "stub"


class AgentName(StrEnum):
    ORCHESTRATOR = "orchestrator"
    ARCHITECT = "architect"
    GENERATOR_COST = "generator_cost"
    GENERATOR_PERFORMANCE = "generator_performance"
    GENERATOR_SECURITY = "generator_security"
    SECURITY = "security"
    VALIDATOR = "validator"


class AgentState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewAction(StrEnum):
    APPROVE = "approve"
    RETRY = "retry"
    REJECT = "reject"
