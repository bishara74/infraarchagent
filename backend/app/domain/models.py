"""Typed values shared by later pipeline stages."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import Variant
from app.domain.paths import validate_file_map


class Violation(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: str
    file_path: str
    resource: str
    message: str
    tool: Literal["checkov", "tfsec"]

    def fingerprint(self) -> tuple[str, str, str]:
        return self.rule_id, self.file_path, self.resource


class DeploymentPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    services: list[str] = Field(default_factory=list)
    dependencies: Any = Field(default_factory=dict)
    network: Any = Field(default_factory=dict)
    storage: Any = Field(default_factory=dict)
    file_types: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


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
