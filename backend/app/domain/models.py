"""Typed values shared by later pipeline stages."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.enums import Severity, Variant
from app.domain.paths import validate_file_map
from app.domain.plan import DeploymentPlan

__all__ = ["DeploymentPlan", "IaCPackage", "Violation"]


class Violation(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: Severity = Severity.UNKNOWN
    file_path: str
    resource: str
    message: str
    tool: Literal[
        "checkov", "trivy", "terraform", "tfsec"
    ]  # tfsec: historical reports only
    line_start: int | None = None
    line_end: int | None = None
    title: str = ""
    guide_url: str | None = None
    blocking: bool = False
    advisory_reason: str | None = None

    def fingerprint(self) -> tuple[str, str, str]:
        return self.rule_id, self.file_path, self.resource


class IaCPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    variant: Variant
    files: dict[str, str]
    security_report: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None

    @field_validator("files")
    @classmethod
    def safe_files(cls, files: dict[str, str]) -> dict[str, str]:
        return validate_file_map(files)
