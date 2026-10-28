"""FR-S-07: final retained-package evidence, independent of scanner findings."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PlanConflict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    service: str
    resource: str
    property: str
    expected: Literal["public", "private"]
    assessment: Literal["regression", "unknown"]
    rule_id: str | None = None
    file_path: str | None = None
    message: str | None = None


class PlanConformanceAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    conflicts: list[PlanConflict] = Field(default_factory=list)
    notes: list[PlanConflict] = Field(default_factory=list)
