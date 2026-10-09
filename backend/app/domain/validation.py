"""Pure validation reports, deterministic sampling and the single outcome rule."""

from collections import Counter
from collections.abc import Iterable
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import PackageStatus
from app.domain.paths import validate_relative_path

Category = Literal["terraform", "reference", "naming", "structure", "lint"]
ValidationTool = Literal[
    "terraform", "builtin", "helm", "hadolint", "ansible-lint", "promtool"
]
CheckStatus = Literal["passed", "failed", "warning", "skipped"]
ValidationResult = Literal["valid", "invalid", "error"]
AbortReason = Literal["deadline", "internal_error"]


class ValidationCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    check_id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9_.-]+$")
    category: Category
    tool: ValidationTool
    status: CheckStatus
    file_path: str | None = None
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    message: str = Field(min_length=1, max_length=500)
    skip_reason: str | None = Field(
        default=None, min_length=1, max_length=100, pattern=r"^[a-z0-9_]+$"
    )

    @field_validator("file_path")
    @classmethod
    def safe_path(cls, value: str | None) -> str | None:
        return validate_relative_path(value) if value is not None else None

    @field_validator("message")
    @classmethod
    def single_line(cls, value: str) -> str:
        if any(ord(char) < 32 for char in value):
            raise ValueError("diagnostic must be a single safe line")
        return value

    @model_validator(mode="after")
    def locations_and_skip(self) -> Self:
        if (
            self.line_start is not None or self.line_end is not None
        ) and self.file_path is None:
            raise ValueError("a line requires a file")
        if self.line_end is not None and (
            self.line_start is None or self.line_end < self.line_start
        ):
            raise ValueError("invalid diagnostic line range")
        if (self.status == "skipped") != (self.skip_reason is not None):
            raise ValueError("only skipped checks require a skip reason")
        return self


def validation_result(
    checks: Iterable[ValidationCheck],
    *,
    terraform_required: bool,
    abort_reason: AbortReason | None = None,
) -> ValidationResult:
    """Failures outrank required unavailability; a whole-stage abort is an error."""
    ordered = tuple(checks)
    if abort_reason is not None:
        return "error"
    if any(check.status == "failed" for check in ordered):
        return "invalid"
    if terraform_required and not any(
        check.check_id == "terraform.validate"
        and check.tool == "terraform"
        and check.category == "terraform"
        and check.status == "passed"
        for check in ordered
    ):
        return "error"
    return "valid"


def package_validation_status(result: ValidationResult) -> PackageStatus:
    return {
        "valid": PackageStatus.VALID,
        "invalid": PackageStatus.INVALID,
        "error": PackageStatus.VALIDATION_ERROR,
    }[result]


class ValidationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    passed: int = Field(ge=0)
    failed: int = Field(ge=0)
    warnings: int = Field(ge=0)
    skipped: int = Field(ge=0)
    result: ValidationResult


def check_order(
    check: ValidationCheck,
) -> tuple[str, str, int, str, str, str, str, int, str]:
    return (
        check.category,
        check.file_path or "",
        check.line_start or 0,
        check.check_id,
        check.status,
        check.message,
        check.tool,
        check.line_end or 0,
        check.skip_reason or "",
    )


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    report_version: Literal[1] = 1
    tool_versions: dict[ValidationTool, str | None]
    terraform_required: bool = False
    checks: tuple[ValidationCheck, ...]
    summary: ValidationSummary
    failed_checks_for_remediation: tuple[ValidationCheck, ...]
    omitted_counts: dict[CheckStatus, int] = Field(default_factory=dict)
    abort_reason: AbortReason | None = None

    @field_validator("checks", "failed_checks_for_remediation", mode="before")
    @classmethod
    def json_arrays(cls, value: object) -> object:
        # JSONB returns arrays as lists; canonicalize only this representation.
        return tuple(value) if isinstance(value, list) else value

    @field_validator("tool_versions")
    @classmethod
    def bounded_versions(
        cls, versions: dict[ValidationTool, str | None]
    ) -> dict[ValidationTool, str | None]:
        if any(
            value is not None
            and (not value or len(value) > 100 or any(ord(char) < 32 for char in value))
            for value in versions.values()
        ):
            raise ValueError("invalid tool version")
        return versions

    @model_validator(mode="after")
    def consistent_report(self) -> Self:
        if tuple(sorted(self.checks, key=check_order)) != self.checks:
            raise ValueError("checks must be deterministically ordered")
        if any(
            type(count) is not int or count < 0
            for count in self.omitted_counts.values()
        ) or self.omitted_counts.get("failed", 0):
            raise ValueError("invalid omitted counts")
        expected = tuple(
            check
            for check in self.checks
            if check.status == "failed" and check.file_path is not None
        )
        if expected != self.failed_checks_for_remediation:
            raise ValueError(
                "remediation targets must retain every file-linked failure"
            )
        counts = Counter(check.status for check in self.checks)
        count_fields: tuple[tuple[CheckStatus, str], ...] = (
            ("passed", "passed"),
            ("failed", "failed"),
            ("warning", "warnings"),
            ("skipped", "skipped"),
        )
        for status, field in count_fields:
            if getattr(self.summary, field) != counts[status] + self.omitted_counts.get(
                status, 0
            ):
                raise ValueError("summary must count checks before sampling")
        if self.summary.result != validation_result(
            self.checks,
            terraform_required=self.terraform_required,
            abort_reason=self.abort_reason,
        ):
            raise ValueError("summary result must follow the centralized outcome rule")
        return self

    @classmethod
    def build(
        cls,
        checks: Iterable[ValidationCheck],
        *,
        terraform_required: bool,
        tool_versions: dict[ValidationTool, str | None] | None = None,
        max_nonfailures: int = 200,
        abort_reason: AbortReason | None = None,
    ) -> Self:
        if max_nonfailures < 0:
            raise ValueError("nonfailure limit must be nonnegative")
        ordered = sorted(checks, key=check_order)
        counts = Counter(check.status for check in ordered)
        retained: list[ValidationCheck] = []
        omitted: Counter[CheckStatus] = Counter()
        sampled = 0
        for check in ordered:
            if check.status == "failed" or (
                terraform_required and check.tool == "terraform"
            ):
                retained.append(check)
            elif sampled < max_nonfailures:
                retained.append(check)
                sampled += 1
            else:
                omitted[check.status] += 1
        return cls(
            terraform_required=terraform_required,
            tool_versions=tool_versions or {},
            checks=tuple(retained),
            summary=ValidationSummary(
                passed=counts["passed"],
                failed=counts["failed"],
                warnings=counts["warning"],
                skipped=counts["skipped"],
                result=validation_result(
                    ordered,
                    terraform_required=terraform_required,
                    abort_reason=abort_reason,
                ),
            ),
            failed_checks_for_remediation=tuple(
                check
                for check in retained
                if check.status == "failed" and check.file_path is not None
            ),
            omitted_counts=dict(omitted),
            abort_reason=abort_reason,
        )
