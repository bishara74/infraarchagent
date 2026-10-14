"""Strict JSON shape returned by one full-package LLM response."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GeneratorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: dict[str, str] = Field(min_length=1)
    notes: str = Field(default="", max_length=1000)


class GeneratorFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    content: str


def generator_wire_schema() -> dict[str, Any]:
    """Adapt the existing package fields to closed strict-output objects."""
    schema = GeneratorOutput.model_json_schema()
    schema["properties"]["files"] = {
        "type": "array",
        "minItems": 1,
        "items": GeneratorFile.model_json_schema(),
    }
    schema["properties"]["notes"].pop("default", None)
    schema["required"] = ["files", "notes"]
    return schema


def validate_generator_output(
    data: dict[str, Any], *, wire_files: bool
) -> dict[str, Any]:
    if wire_files:
        if not isinstance(data.get("files"), list) or "notes" not in data:
            raise ValueError("invalid wire shape")
        files: dict[str, str] = {}
        for entry in data["files"]:
            file = GeneratorFile.model_validate(entry)
            if file.path in files:
                raise ValueError("duplicate file path")
            files[file.path] = file.content
        data = {**data, "files": files}
    return GeneratorOutput.model_validate(data).model_dump()
