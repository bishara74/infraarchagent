"""FR-S-07/NFR-01: synthetic structural copies of final-round guard failures."""

import json
from copy import deepcopy

import pytest

from app.security.plan_conformance import plan_regressions
from tests.unit.test_phase10b_conformance import files, plan

pytestmark = pytest.mark.req("FR-S-02", "FR-S-07", "FR-V-03", "NFR-01")


def package(resources):
    return {"terraform/main.tf.json": json.dumps({"resource": resources})}


@pytest.mark.parametrize("kind", ["elasticache", "prometheus", "grafana", "iam"])
@pytest.mark.parametrize(
    "change", ["logging_policy", "encryption_policy", "unrelated_network"]
)
def test_unsupported_service_does_not_veto_unrelated_resource(kind, change):
    # Final sequences 7/9/10/11/19: a nonexistent binding compared any policy.
    before = files()
    data = json.loads(before["terraform/main.tf.json"])
    if change == "unrelated_network":
        data["resource"]["aws_vpc"] = {"unrelated": {"cidr_block": "10.4.0.0/16"}}
    else:
        resource = (
            "aws_iam_role_policy" if change == "logging_policy" else "aws_kms_key"
        )
        data["resource"][resource] = {"logs": {"policy": "{}"}}
    candidate = {"terraform/main.tf.json": json.dumps(data)}
    assert not plan_regressions(plan(kind=kind), before, candidate)


@pytest.mark.parametrize("kind", ["edgeproxy", "custom-service"])
@pytest.mark.parametrize(
    "field,value", [("internal", True), ("internal", "${var.private}")]
)
def test_unsupported_named_endpoint_still_guards_its_path(kind, field, value):
    assert plan_regressions(plan(kind=kind), files(), files({field: value}))


def test_unsupported_named_endpoint_does_not_guard_another_network():
    before = files(extra={"aws_vpc": {"other": {"cidr_block": "10.0.0.0/16"}}})
    after = files(extra={"aws_vpc": {"other": {"cidr_block": "10.1.0.0/16"}}})
    assert not plan_regressions(plan(kind="edgeproxy"), before, after)


@pytest.mark.parametrize("unknown", [False, True])
def test_preexisting_private_plan_mismatch_allows_unrelated_hardening(unknown):
    before = files({"internal": "${var.internal}" if unknown else False})
    after = files(
        {
            "internal": "${var.internal}" if unknown else False,
            "drop_invalid_header_fields": True,
        }
    )
    assert not plan_regressions(plan(False), before, after)


def test_changed_unknown_expression_still_fails_closed():
    assert plan_regressions(
        plan(),
        files({"internal": "${var.before}"}),
        files({"internal": "${var.after}"}),
    )


def test_final_eks_mismatch_is_unchanged_by_subnet_default():
    # Final sequence 10/performance: endpoint public -> public, plan private.
    resources = {
        "aws_eks_cluster": {
            "edge": {
                "vpc_config": [
                    {
                        "endpoint_public_access": True,
                        "subnet_ids": ["${aws_subnet.public.id}"],
                    }
                ]
            }
        },
        "aws_subnet": {"public": {"map_public_ip_on_launch": True}},
    }
    before = package(resources)
    resources["aws_subnet"]["public"]["map_public_ip_on_launch"] = False
    after = package(resources)
    assert not plan_regressions(plan(False, "eks"), before, after)
    resources["aws_eks_cluster"]["edge"]["vpc_config"][0]["endpoint_public_access"] = (
        "${var.endpoint}"
    )
    assert plan_regressions(plan(False, "eks"), after, package(resources))


def test_final_ecs_private_intent_public_placement_keeps_safe_default_change():
    # Final sequence 15/performance: explicit assign_public_ip=false, same routes.
    resources = {
        "aws_ecs_service": {
            "edge": {
                "network_configuration": [
                    {"assign_public_ip": False, "subnets": ["${aws_subnet.public.id}"]}
                ]
            }
        },
        "aws_vpc": {"main": {}},
        "aws_subnet": {
            "public": {"vpc_id": "${aws_vpc.main.id}", "map_public_ip_on_launch": True}
        },
        "aws_internet_gateway": {"igw": {"vpc_id": "${aws_vpc.main.id}"}},
        "aws_route_table": {
            "public": {
                "vpc_id": "${aws_vpc.main.id}",
                "route": [
                    {
                        "cidr_block": "0.0.0.0/0",
                        "gateway_id": "${aws_internet_gateway.igw.id}",
                    }
                ],
            }
        },
        "aws_route_table_association": {
            "public": {
                "subnet_id": "${aws_subnet.public.id}",
                "route_table_id": "${aws_route_table.public.id}",
            }
        },
    }
    before = package(resources)
    resources["aws_subnet"]["public"]["map_public_ip_on_launch"] = False
    assert not plan_regressions(plan(False, "ecs"), before, package(resources))


def test_ec2_inherited_address_default_is_an_exposure_path():
    before = package(
        {
            "aws_instance": {"edge": {"subnet_id": "${aws_subnet.public.id}"}},
            "aws_subnet": {"public": {"map_public_ip_on_launch": True}},
        }
    )
    data = json.loads(before["terraform/main.tf.json"])
    data["resource"]["aws_subnet"]["public"]["map_public_ip_on_launch"] = False
    assert plan_regressions(
        plan(kind="ec2"), before, {"terraform/main.tf.json": json.dumps(data)}
    )


def test_preexisting_mismatch_does_not_authorize_changed_ingress():
    before = files(
        {"internal": True, "security_groups": ["${aws_security_group.edge.id}"]},
        {"aws_security_group": {"edge": {"ingress": [{"from_port": 443}]}}},
    )
    after = files(
        {"internal": True, "security_groups": ["${aws_security_group.edge.id}"]},
        {"aws_security_group": {"edge": {"ingress": []}}},
    )
    assert plan_regressions(plan(), before, after)


def test_ambiguous_binding_accepts_unrelated_policy_but_blocks_shared_group():
    before = files(extra={"aws_alb": {"other": {"internal": False}}})
    candidate = deepcopy(json.loads(before["terraform/main.tf.json"]))
    candidate["resource"]["aws_kms_key"] = {"logs": {"policy": "{}"}}
    assert not plan_regressions(
        plan(), before, {"terraform/main.tf.json": json.dumps(candidate)}
    )


def test_ambiguous_s3_binding_does_not_adopt_new_unrelated_logging_bucket():
    before = package({"aws_s3_bucket": {"one": {}, "two": {}}})
    data = json.loads(before["terraform/main.tf.json"])
    data["resource"]["aws_s3_bucket"]["logs"] = {"bucket_prefix": "access-logs-"}
    after = {"terraform/main.tf.json": json.dumps(data)}
    assert not plan_regressions(plan(False, "s3"), before, after)
    data["resource"]["aws_s3_bucket"]["one"]["acl"] = "public-read"
    assert plan_regressions(
        plan(False, "s3"), before, {"terraform/main.tf.json": json.dumps(data)}
    )


def test_unsupported_named_network_interface_keeps_its_exposure_path():
    before = package(
        {"aws_network_interface": {"edge": {"subnet_id": "${var.before}"}}}
    )
    after = package({"aws_network_interface": {"edge": {"subnet_id": "${var.after}"}}})
    assert plan_regressions(plan(kind="custom-network"), before, after)
