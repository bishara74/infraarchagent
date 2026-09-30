"""Strict JSON shape returned by one full-package LLM response."""

from pydantic import BaseModel, ConfigDict, Field


class GeneratorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: dict[str, str] = Field(min_length=1)
    notes: str = Field(default="", max_length=1000)
