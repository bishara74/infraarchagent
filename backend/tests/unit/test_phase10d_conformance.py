"""FR-S-07: NAT egress is separate from an instance's public addressing."""

import json
from copy import deepcopy

import pytest

from app.security.plan_conformance import plan_regressions
from tests.unit.test_phase10b_conformance import plan

pytestmark = pytest.mark.req("FR-S-02", "FR-S-07", "FR-V-03", "NFR-01")


def resources():
    return {
        "aws_instance": {
            "edge": {
                "subnet_id": "${aws_subnet.private.id}",
                "security_groups": ["${aws_security_group.app.id}"],
            }
        },
        "aws_eip": {"nat": {"vpc": True}},
        "aws_vpc": {"main": {}},
        "aws_subnet": {
            "private": {
                "vpc_id": "${aws_vpc.main.id}",
                "map_public_ip_on_launch": False,
            },
            "public": {"vpc_id": "${aws_vpc.main.id}", "map_public_ip_on_launch": True},
        },
        "aws_nat_gateway": {
            "nat": {
                "subnet_id": "${aws_subnet.public.id}",
                "allocation_id": "${aws_eip.nat.id}",
            }
        },
        "aws_route_table": {"private": {"vpc_id": "${aws_vpc.main.id}"}},
        "aws_route_table_association": {
            "private": {
                "subnet_id": "${aws_subnet.private.id}",
                "route_table_id": "${aws_route_table.private.id}",
            }
        },
        "aws_route": {
            "nat": {
                "route_table_id": "${aws_route_table.private.id}",
                "destination_cidr_block": "0.0.0.0/0",
                "nat_gateway_id": "${aws_nat_gateway.nat.id}",
            }
        },
        "aws_security_group": {
            "app": {
                "ingress": [
                    {
                        "from_port": 22,
                        "to_port": 22,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"],
                    }
                ]
            }
        },
    }


def package(data):
    return {"terraform/main.tf.json": json.dumps({"resource": data})}


@pytest.mark.parametrize("explicit", [False, True])
def test_nat_eip_migration_is_not_an_ec2_exposure_or_ingress_change(explicit):
    before = resources()
    if explicit:
        before["aws_instance"]["edge"]["associate_public_ip_address"] = False
    after = deepcopy(before)
    after["aws_eip"]["nat"] = {"domain": "vpc"}
    assert not plan_regressions(plan(False, "ec2"), package(before), package(after))


def test_nat_public_subnet_addressing_is_not_private_instance_addressing():
    before = resources()
    after = deepcopy(before)
    after["aws_subnet"]["public"]["map_public_ip_on_launch"] = False
    assert not plan_regressions(plan(False, "ec2"), package(before), package(after))


@pytest.mark.parametrize("attachment", ["instance", "network_interface"])
def test_configured_unknown_eip_attachment_is_still_guarded(attachment):
    before = resources()
    before["aws_eip"]["nat"][attachment] = "${var.attachment}"
    after = deepcopy(before)
    after["aws_eip"]["nat"][attachment] = "${var.other_attachment}"
    assert plan_regressions(plan(False, "ec2"), package(before), package(after))


def test_attaching_an_eip_to_private_instance_still_rejects():
    before = resources()
    after = deepcopy(before)
    after["aws_eip"]["nat"]["instance"] = "${aws_instance.edge.id}"
    assert plan_regressions(plan(False, "ec2"), package(before), package(after))


@pytest.mark.parametrize("change", ["addressing", "subnet", "route", "ingress"])
def test_actual_instance_network_and_d63_ingress_remain_guarded(change):
    before = resources()
    after = deepcopy(before)
    if change == "addressing":
        after["aws_subnet"]["private"]["map_public_ip_on_launch"] = True
    elif change == "subnet":
        after["aws_instance"]["edge"]["subnet_id"] = "${aws_subnet.public.id}"
    elif change == "route":
        after["aws_route"]["nat"]["nat_gateway_id"] = "${var.changed_nat}"
    else:
        after["aws_security_group"]["app"]["ingress"] = []
    assert plan_regressions(plan(False, "ec2"), package(before), package(after))
