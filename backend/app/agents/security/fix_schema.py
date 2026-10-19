"""Closed wire representation of the existing fixer patch contract."""

from typing import Any


def wire_schema() -> dict[str, Any]:
    # Import lazily: FixAgent uses this helper after its patch models exist.
    from app.agents.security.fix import FixFile, FixOutput, FixSummary

    schema = FixOutput.model_json_schema()
    for name in ("new_files", "edits"):
        schema["properties"][name] = {
            "type": "array",
            "items": FixFile.model_json_schema(),
        }
    schema["properties"]["fixes"] = {
        "type": "array",
        "items": FixSummary.model_json_schema(),
    }
    schema["required"] = list(schema["properties"])
    return schema


def validate_output(data: dict[str, Any], *, wire_files: bool) -> dict[str, Any]:
    from app.agents.security.fix import FixFile, FixOutput, FixSummary

    if wire_files:
        if any(name not in data for name in ("file", "edits", "new_files", "fixes")):
            raise ValueError("missing strict patch field")
        data = dict(data)
        for name in ("edits", "new_files"):
            entries = data[name]
            if not isinstance(entries, list):
                raise ValueError("invalid patch files")
            files = {}
            for entry in entries:
                file = FixFile.model_validate(entry)
                if file.path in files:
                    raise ValueError("duplicate patch path")
                files[file.path] = file.content
            data[name] = files
        if not isinstance(data["fixes"], list):
            raise ValueError("invalid fix summaries")
        data["fixes"] = [
            FixSummary.model_validate(value).model_dump() for value in data["fixes"]
        ]
    return FixOutput.model_validate(data).model_dump()
