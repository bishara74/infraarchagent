"""FR-V-01: safe declarations without resource creation or changed defaults."""

import pytest

from app.validation.repairs import repair_terraform

pytestmark = pytest.mark.req("FR-V-01", "NFR-01")


def test_variables_and_safe_data_sources_are_module_scoped_and_idempotent():
    files = {
        "terraform/main.tf": """output "x" {
  value = [var.region, var.db_password, data.aws_region.here.name,
    data.aws_caller_identity.me.account_id, data.aws_partition.current.partition,
    data.aws_availability_zones.available.names, data.aws_ami.image.id]
}
# var.comment
output "literal" { value = "var.literal data.aws_region.fake" }
""",
        "terraform/modules/child/main.tf": 'output "x" { value = var.region }\n',
    }
    fixed, records = repair_terraform(files)
    assert len(records) == 7
    assert len([r for r in records if r["kind"] == "missing_data_source"]) == 4
    assert 'state = "available"' in fixed["terraform/variables.tf"]
    assert "default" not in fixed["terraform/variables.tf"]
    assert "sensitive = true" in fixed["terraform/variables.tf"]
    assert "aws_ami" not in fixed["terraform/variables.tf"]
    assert "literal" not in fixed["terraform/variables.tf"]
    assert "comment" not in fixed["terraform/variables.tf"]
    assert 'variable "region"' in fixed["terraform/modules/child/variables.tf"]
    assert repair_terraform(fixed) == (fixed, [])


def test_exact_duplicates_removed_but_conflicts_and_existing_data_preserved():
    declaration = 'variable "x" { type = string }'
    files = {
        "terraform/main.tf": declaration + '\ndata "aws_region" "here" {}\n',
        "terraform/variables.tf": declaration + '\nvariable "x" { default = "a" }\n',
    }
    fixed, records = repair_terraform(files)
    assert records == [
        {"file": "terraform/variables.tf", "kind": "duplicate_variable", "name": "x"}
    ]
    assert 'default = "a"' in fixed["terraform/variables.tf"]
    assert fixed["terraform/main.tf"] == files["terraform/main.tf"]
    assert repair_terraform(fixed) == (fixed, [])


@pytest.mark.parametrize("source", ['variable "x" {}\n', 'output "x" { value = }'])
def test_clean_and_unparsable_modules_are_unchanged(source):
    files = {"terraform/main.tf": source}
    assert repair_terraform(files) == (files, [])


def test_json_declarations_prevent_duplicate_hcl_inputs():
    files = {
        "terraform/main.tf": 'output "x" { value = var.region }',
        "terraform/inputs.tf.json": '{"variable":{"region":{"type":"string"}}}',
    }
    assert repair_terraform(files) == (files, [])
