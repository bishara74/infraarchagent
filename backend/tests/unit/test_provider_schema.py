"""FR-V-03: offline, exact-version schema queries and conservative selection."""

import hashlib
import json

import pytest

from app.validation.provider_schema import (
    ProviderSchemaIndex,
    compact_block,
    matches_version,
    select_version,
)

pytestmark = pytest.mark.req("FR-V-03", "NFR-01")


@pytest.fixture
def index(tmp_path):
    schema = {
        "resource_schemas": {
            "aws_widget": {
                "attributes": {
                    "name": {"type": "string", "required": True},
                    "id": {"type": "string", "computed": True},
                    "label": {"type": "string", "optional": True, "computed": True},
                },
                "block_types": {
                    "rule": {
                        "nesting_mode": "list",
                        "min_items": 1,
                        "block": {
                            "attributes": {
                                "port": {"required": True, "type": "number"}
                            },
                            "block_types": {},
                        },
                    }
                },
            }
        },
        "data_source_schemas": {"aws_widget": {"attributes": {}, "block_types": {}}},
    }
    raw = json.dumps(schema).encode()
    (tmp_path / "aws-5.100.0.json").write_bytes(raw)
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "format_version": 1,
                "providers": {
                    "aws/5.100.0": {"index_sha256": hashlib.sha256(raw).hexdigest()}
                },
            }
        )
    )
    return ProviderSchemaIndex("aws", "5.100.0", directory=tmp_path)


def test_queries_nested_required_and_names(index):
    assert index.available
    assert index.required_missing("aws_widget", {"name": "present"}) == ["rule"]
    assert index.nearest_types("aws_widgit") == ["aws_widget"]
    assert index.nearest_arguments("aws_widget", "lable") == ["label"]
    assert index.resource_schema("aws_widget", data_source=True) == {
        "attributes": {},
        "block_types": {},
    }
    assert index.resource_schema("aws_widget")["attributes"]["label"]["optional"]


def test_missing_corrupt_and_wrong_version_degrade(index, tmp_path, caplog):
    assert not ProviderSchemaIndex("aws", "6.68.0", directory=tmp_path).available
    (tmp_path / "aws-5.100.0.json").write_text("corrupt")
    broken = ProviderSchemaIndex("aws", "5.100.0", directory=tmp_path)
    assert not broken.available and broken.resource_schema("aws_widget") is None
    assert "grounding degraded" in caplog.text


@pytest.mark.parametrize(
    "constraint,expected",
    [
        ("~> 5.100", "5.100.0"),
        (">= 5, < 7", "6.68.0"),
        ("= 7.0.0", None),
        ("invalid", None),
        ("", "6.68.0"),
    ],
)
def test_version_constraints(constraint, expected):
    assert select_version("aws", constraint) == expected
    assert not matches_version("6.68.0", "~> 5.100.0")


def test_compact_drops_descriptions_recursively():
    result = compact_block(
        {
            "description": "prose",
            "attributes": {
                "x": {"description": "prose", "required": True, "type": "string"}
            },
            "block_types": {
                "rule": {
                    "nesting_mode": "list",
                    "min_items": 1,
                    "block": {"description": "prose", "attributes": {}},
                }
            },
        }
    )
    assert "prose" not in json.dumps(result)
    assert result["block_types"]["rule"]["min_items"] == 1
