"""FR-V-01/03: documented equivalents preserve values and unrelated source."""

import json

import pytest

from app.validation.equivalents import repair_equivalents

pytestmark = pytest.mark.req("FR-V-01", "FR-V-03", "NFR-01")


def test_name_route_and_listener_maps_preserve_expressions_and_comments():
    source = """# retain this comment
resource "aws_db_instance" "db" {
  name = var.database_name # keep expression
  multi_az = true
}
resource "aws_route_table" "rt" {
  route {
    cidr_blocks = [var.destination]
    gateway_id = aws_internet_gateway.main.id
  }
}
resource "aws_lb_listener_rule" "route" {
  condition {
    path_pattern = { values = ["/api/*"] }
  }
}
"""
    files = {"terraform/main.tf": source}
    result, records = repair_equivalents(files)
    assert (
        "db_name = var.database_name # keep expression" in result["terraform/main.tf"]
    )
    assert "cidr_block = var.destination" in result["terraform/main.tf"]
    assert 'path_pattern { values = ["/api/*"] }' in result["terraform/main.tf"]
    assert "multi_az = true" in result["terraform/main.tf"]
    assert len(records) == 3
    assert repair_equivalents(result) == (result, [])
    assert files["terraform/main.tf"] == source


@pytest.mark.parametrize(
    "body",
    [
        "name = var.a\n db_name = var.b",
        "multi_az = true",
        "drop_invalid_header_fields = true",
    ],
)
def test_conflicting_and_non_equivalent_arguments_are_untouched(body):
    files = {
        "terraform/main.tf": 'resource "aws_db_instance" "db" {\n' + body + "\n}\n"
    }
    assert repair_equivalents(files) == (files, [])


def test_json_rename_preserves_unrelated_bytes():
    source = (
        '{"resource":{"aws_db_instance":{"db":{"name": "${v'
        'ar.db}", "multi_az": true}}}}'
    )
    result, records = repair_equivalents({"terraform/main.tf.json": source})
    assert result["terraform/main.tf.json"] == source.replace('"name"', '"db_name"')
    assert json.loads(result["terraform/main.tf.json"])
    assert len(records) == 1


def test_cidr_collection_with_multiple_destinations_is_not_collapsed():
    files = {
        "terraform/main.tf": (
            'resource "aws_route_table" "rt" {\n route {\n cidr_b'
            'locks = ["a", "b"]\n }\n}\n'
        )
    }
    assert repair_equivalents(files) == (files, [])


def test_competing_json_legacy_route_fields_are_untouched():
    files = {
        "terraform/main.tf.json": json.dumps(
            {
                "resource": {
                    "aws_route_table": {
                        "rt": {
                            "route": [
                                {
                                    "cidr_ipv4": "10.0.0.0/8",
                                    "cidr_blocks": ["0.0.0.0/0"],
                                }
                            ]
                        }
                    }
                }
            }
        )
    }
    assert repair_equivalents(files) == (files, [])


def test_optional_names_types_and_nested_shapes_fit_generation_cap():
    from app.validation.schema_context import generator_schema_guidance

    guidance = generator_schema_guidance(
        4500, resource_types=("aws_db_instance", "aws_lb_listener", "aws_ecs_service")
    )
    raw = guidance.text
    entries = json.loads(raw)
    assert len(raw) <= 4500
    db = next(e for e in entries if e["type"] == "aws_db_instance")
    assert db["schema"]["optional"]["db_name"] == "string"
    service = next(e for e in entries if e["type"] == "aws_ecs_service")
    assert "aws_ecs_service" in guidance.omitted_conditional
    assert service["schema"]["blocks"] == {}
    single = generator_schema_guidance(4500, resource_types=("aws_ecs_service",))
    service = json.loads(single.text)[0]
    assert "network_configuration" in service["schema"]["blocks"]
    assert (
        service["schema"]["blocks"]["network_configuration"]["optional"][
            "assign_public_ip"
        ]
        == "bool"
    )
