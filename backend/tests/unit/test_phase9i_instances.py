"""FR-S-04/NFR-01: bounded instances never infer unknown deployment values."""

import pytest

from app.security.addressing import repair_addressing
from app.security.instances import Instances, Ref, Unresolved

pytestmark = pytest.mark.req("FR-S-04", "FR-S-09", "NFR-01")


def files(extra="", count="2"):
    return {
        "terraform/main.tf": """locals { names = ["a", "b"] }
resource "aws_vpc" "v" {}
resource "aws_subnet" "public" {
 count = """
        + count
        + """
 vpc_id = aws_vpc.v.id
 map_public_ip_on_launch = true
}
"""
        + extra
    }


def test_literal_local_count_index_and_splat():
    value = files(count="length(local.names)")
    graph = Instances(value)
    assert len(graph.all("terraform", {"aws_subnet"})) == 2
    assert graph.value("${aws_subnet.public[0].id}", "terraform") == Ref(
        "terraform", "aws_subnet.public[0]"
    )
    assert len(graph.value("${aws_subnet.public[*].id}", "terraform")) == 2
    assert len(graph.value("${[for s in aws_subnet.public : s.id]}", "terraform")) == 2
    changed, records = repair_addressing(value)
    assert records and "map_public_ip_on_launch = false" in changed["terraform/main.tf"]
    assert repair_addressing(changed) == (changed, [])


@pytest.mark.parametrize(
    "count", ["65", "var.count", "length(var.subnets)", "local.loop"]
)
def test_unbounded_variable_and_cycles_remain_unknown(count):
    value = files("locals { loop = local.loop }\n", count)
    assert repair_addressing(value) == (value, [])


@pytest.mark.parametrize(
    "override,changed",
    [
        ("", False),
        ("associate_public_ip_address = true", True),
        ("associate_public_ip_address = false", True),
        ("associate_public_ip_address = var.public", False),
    ],
)
def test_instance_inheritance_and_explicit_overrides(override, changed):
    value = files(
        'resource "aws_instance" "nginx" {\n subnet_id = aws_subnet.public[0].id\n'
        + override
        + "\n}\n"
    )
    result, _ = repair_addressing(value)
    assert (result != value) is changed


def test_foreach_literal_local_and_values():
    value = files().copy()
    value["terraform/main.tf"] = """locals { names = { a = "x", b = "y" } }
resource "aws_subnet" "public" {
 for_each = local.names
 map_public_ip_on_launch = true
}
"""
    graph = Instances(value)
    assert graph.find("terraform", 'aws_subnet.public["a"]')
    assert len(graph.value("${values(aws_subnet.public)}", "terraform")) == 2
    with pytest.raises(Unresolved):
        graph.value("${var.names}", "terraform")


def test_unknown_consumer_and_external_module_prevent_repair():
    for extra in (
        'resource "aws_emr_cluster" "other" {\n ec2_attributes { subnet_id = aws_subnet.public[0].id }\n}\n',
        'module "external" { source = "./external" }\n',
    ):
        value = files(extra)
        assert repair_addressing(value) == (value, [])


def test_total_instance_limit_and_local_depth_are_enforced():
    value = {
        "terraform/main.tf": "\n".join(
            f'resource "aws_subnet" "s{i}" {{\n count = 64\n}}' for i in range(17)
        )
    }
    assert Instances(value).all("terraform") == []
    value = files(
        "locals {\n"
        + "\n".join(f"x{i} = local.x{i + 1}" for i in range(18))
        + "\nx18 = 2\n}\n",
        "local.x0",
    )
    assert not Instances(value).all("terraform", {"aws_subnet"})
