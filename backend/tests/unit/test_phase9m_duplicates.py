"""FR-V-03/04: conservative duplicate repairs and retained failure semantics."""

import json

import pytest

from app.domain.validation import DeterministicRepair
from app.validation.duplicates import repair_duplicates
from app.validation.repairs import repair_declarations
from app.validation.workspace import ValidationWorkspace

pytestmark = pytest.mark.req("FR-V-03", "FR-V-04", "NFR-01")
ALB = 'resource "aws_lb" "api_alb" {\n name = "api"\n internal = false\n}\n'
LOGS = (
    'resource "aws_lb" "api_alb" {\n access_logs {\n'
    '  bucket = "logs"\n  enabled = true\n }\n}\n'
)


@pytest.mark.parametrize("separate", [False, True])
async def test_observed_alb_merge_is_idempotent_and_has_origin_and_hashes(separate):
    files = {"terraform/main.tf": ALB}
    files["terraform/extra.tf" if separate else "terraform/main.tf"] = (
        LOGS if separate else ALB + LOGS
    )
    fixed, records = await repair_declarations(files)
    joined = "\n".join(fixed.values())
    assert joined.count('resource "aws_lb" "api_alb"') == 1
    assert 'bucket = "logs"' in joined and "internal = false" in joined
    assert await repair_declarations(fixed) == (fixed, [])
    assert records
    for record in records:
        parsed = DeterministicRepair.model_validate(record)
        assert parsed.kind == "duplicate_block" and parsed.origin == "generated"
        assert parsed.before_hash != parsed.after_hash
        assert parsed.line >= 1


@pytest.mark.parametrize(
    "later",
    [
        'resource "aws_lb" "api_alb" { name = "different" }',
        'resource "aws_lb" "api_alb" { name = var.name }',
        'resource "aws_lb" "api_alb" { name = "api"\n name = "api" }',
        'resource "aws_lb" "api_alb" { dynamic "access_logs" { for_each = [] } }',
        'resource "aws_lb" "api_alb" { access_logs { enabled = false } }',
    ],
)
async def test_conflicting_or_dynamic_duplicates_leave_entire_module_unchanged(later):
    files = {"terraform/main.tf": ALB + LOGS + later + "\n"}
    assert await repair_declarations(files) == (files, [])


@pytest.mark.parametrize(
    "kind", ["aws_s3_bucket", "aws_security_group", "aws_instance"]
)
async def test_other_resource_types_and_identical_duplicates(kind):
    block = f'resource "{kind}" "example" {{\n tags = {{ Name = "same" }}\n}}\n'
    files = {"terraform/main.tf": block + block}
    fixed, records = await repair_declarations(files)
    assert fixed["terraform/main.tf"].count(f'resource "{kind}"') == 1
    assert len(records) == 1


def test_identical_nested_collections_are_not_appended_twice():
    first = ALB.replace(
        " internal = false", " access_logs { enabled = true }\n internal = false"
    )
    second = 'resource "aws_lb" "api_alb" { access_logs { enabled = true } }\n'
    fixed, _ = repair_duplicates({"terraform/main.tf": first + second})
    assert fixed["terraform/main.tf"].count("access_logs") == 1


@pytest.mark.parametrize("conflict", [False, True])
async def test_json_across_files(conflict):
    first = {"resource": {"aws_lb": {"api_alb": {"name": "api"}}}}
    second = {"resource": {"aws_lb": {"api_alb": {"access_logs": [{"enabled": True}]}}}}
    if conflict:
        second["resource"]["aws_lb"]["api_alb"]["name"] = "other"
    files = {
        "terraform/main.tf.json": json.dumps(first),
        "terraform/z.tf.json": json.dumps(second),
    }
    fixed, records = await repair_declarations(files)
    if conflict:
        assert (fixed, records) == (files, [])
    else:
        body = json.loads(fixed["terraform/main.tf.json"])["resource"]["aws_lb"][
            "api_alb"
        ]
        assert body == {"name": "api", "access_logs": [{"enabled": True}]}
        assert json.loads(fixed["terraform/z.tf.json"]) == {"resource": {"aws_lb": {}}}
        assert len(records) == 2
        assert await repair_declarations(fixed) == (fixed, [])


@pytest.mark.parametrize(
    "source",
    [
        '{"resource":{"aws_lb":{"api_alb":{},"api_alb":{}}}}',
        'resource "aws_lb" "api_alb" {',
    ],
)
def test_ambiguous_json_keys_and_malformed_hcl_are_unchanged(source):
    path = "terraform/main.tf.json" if source.startswith("{") else "terraform/main.tf"
    files = {path: source}
    assert repair_duplicates(files) == (files, [])


def test_module_scope_and_untouched_source_are_preserved():
    files = {
        "terraform/main.tf": ALB + LOGS,
        "terraform/child/main.tf": ALB,
        "README.md": "unchanged",
    }
    fixed, _ = repair_duplicates(files)
    assert fixed["terraform/child/main.tf"] == ALB
    assert fixed["README.md"] == "unchanged"


def test_conflict_aborts_other_duplicate_groups_and_mixed_formats():
    files = {
        "terraform/main.tf": ALB
        + LOGS
        + 'resource "x" "y" { a = 1 }\nresource "x" "y" { a = 2 }\n'
    }
    assert repair_duplicates(files) == (files, [])
    mixed = {
        "terraform/main.tf": ALB,
        "terraform/a.tf.json": '{"resource":{"aws_lb":{"api_alb":{}}}}',
    }
    assert repair_duplicates(mixed) == (mixed, [])


def test_data_blocks_and_later_stage_provenance():
    files = {"terraform/main.tf": 'data "aws_region" "here" {}\n' * 2}
    workspace = ValidationWorkspace()
    try:
        workspace.stage = "security_fix"
        with workspace.activate():
            fixed, records = repair_duplicates(files)
        assert fixed["terraform/main.tf"].count('data "aws_region"') == 1
        assert records[0]["origin"] == "security_fix"
    finally:
        workspace.close()
