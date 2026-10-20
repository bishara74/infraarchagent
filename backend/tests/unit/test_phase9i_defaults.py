"""FR-S-02/09: recovery defaults preserve longer retention and live rules."""

import json

import pytest

from app.security.defaults import repair_defaults

pytestmark = pytest.mark.req("FR-S-02", "FR-S-09", "NFR-01")


@pytest.mark.parametrize(
    "retention,changed",
    [
        (None, True),
        (0, True),
        (1, True),
        (6, True),
        (7, False),
        (30, False),
        ("${var.days}", False),
        (True, False),
    ],
)
def test_backup_days(retention, changed):
    body = {} if retention is None else {"backup_retention_period": retention}
    files = {
        "terraform/main.tf.json": json.dumps(
            {"resource": {"aws_db_instance": {"db": body}}}
        )
    }
    result, records = repair_defaults(files)
    assert (result != files) is changed
    if changed:
        assert records and repair_defaults(result) == (result, [])


def test_unused_default_group_is_managed_idempotently():
    files = {"terraform/main.tf": 'resource "aws_vpc" "v" {}\n'}
    result, records = repair_defaults(files)
    assert (
        records
        and "aws_default_security_group" in result["terraform/security_support.tf"]
    )
    assert "ingress = []" in result["terraform/security_support.tf"]
    assert repair_defaults(result) == (result, [])


@pytest.mark.parametrize(
    "groups",
    [
        "",
        "vpc_security_group_ids = [aws_default_security_group.default.id]",
        "vpc_security_group_ids = var.groups",
    ],
)
def test_inherited_explicit_and_unknown_default_consumers_keep_rules(groups):
    source = (
        """resource "aws_vpc" "v" {}
resource "aws_default_security_group" "default" {
 vpc_id = aws_vpc.v.id
 ingress { from_port = 443
 to_port = 443
 protocol = "tcp"
 cidr_blocks = ["10.0.0.0/8"]
 }
}
resource "aws_instance" "app" {
"""
        + groups
        + "\n}\n"
    )
    files = {"terraform/main.tf": source}
    assert repair_defaults(files) == (files, [])
