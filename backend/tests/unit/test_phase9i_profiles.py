"""FR-S-04/FR-UI-05: v2 is adjacent evidence, never strict acceptance."""

import json

import pytest

from app.security.profiles import assess, assess_v1

pytestmark = pytest.mark.req("FR-S-04", "FR-UI-05", "NFR-01")


def package(resources, rule="AWS-0053", address="aws_lb.edge", **extra):
    return {
        "files": {
            "terraform/main.tf.json": json.dumps({"resource": resources, **extra})
        },
        "validation_report": {"summary": {"result": "valid"}},
        "security_report": {
            "final": {
                "outcome": "exhausted",
                "remaining_blocking": [
                    {
                        "rule_id": rule,
                        "resource": address,
                        "file_path": "terraform/main.tf.json",
                    }
                ],
            }
        },
    }


def network(
    kind="application", protocol="HTTPS", policy="ELBSecurityPolicy-TLS13-1-2-2021-06"
):
    return {
        "aws_lb": {
            "edge": {
                "internal": False,
                "load_balancer_type": kind,
                "security_groups": ["${aws_security_group.edge.id}"],
            }
        },
        "aws_security_group": {"edge": {}},
        "aws_lb_listener": {
            "tls": {
                "load_balancer_arn": "${aws_lb.edge.arn}",
                "port": "443",
                "protocol": protocol,
                "certificate_arn": "${var.certificate_arn}",
                "ssl_policy": policy,
            }
        },
    }


def test_https_only_and_literal_normalisation_leave_v1_unchanged():
    value = package(network(protocol="https"))
    legacy = assess_v1(value)
    result = assess(value)
    assert {k: result[k] for k in legacy} == legacy
    assert result["strict"]["remaining_blocking"] == 1
    assert result["contextual-v1"]["remaining_blocking"] == 1
    assert result["contextual-v2"]["remaining_blocking"] == 0


@pytest.mark.parametrize(
    "protocol,policy,passed",
    [
        ("TLS", "ELBSecurityPolicy-TLS13-1-2-2021-06", True),
        ("TLS", "ELBSecurityPolicy-2016-08", False),
        ("TLS", "made-up-TLS-1-2-policy", False),
        ("TLS", "${var.policy}", False),
        ("TCP", "ELBSecurityPolicy-TLS13-1-2-2021-06", False),
        ("UDP", None, False),
        ("TLS", None, False),
    ],
)
def test_nlb_requires_only_tls_and_known_minimum_protocol(protocol, policy, passed):
    value = package(network("network", protocol, policy))
    assert assess(value)["contextual-v2"]["checks_passed"] is passed


@pytest.mark.parametrize("port", [True, False, 0, 65536, "${var.port}", "443bad"])
def test_unknown_or_invalid_listener_ports_do_not_qualify(port):
    resources = network()
    resources["aws_lb_listener"]["tls"]["port"] = port
    assert not assess(package(resources))["contextual-v2"]["checks_passed"]


def test_http_must_redirect_and_rules_cannot_bypass_it():
    resources = network()
    resources["aws_lb_listener"]["http"] = {
        "load_balancer_arn": "${aws_lb.edge.arn}",
        "port": "80",
        "protocol": "http",
        "default_action": [
            {
                "type": "redirect",
                "redirect": [
                    {"protocol": "HTTPS", "port": "443", "status_code": "HTTP_301"}
                ],
            }
        ],
    }
    assert assess(package(resources))["contextual-v2"]["checks_passed"]
    resources["aws_lb_listener_rule"] = {
        "bypass": {
            "listener_arn": "${aws_lb_listener.http.arn}",
            "action": [{"type": "forward"}],
        }
    }
    assert not assess(package(resources))["contextual-v2"]["checks_passed"]


def test_source_only_sg_reference_is_not_an_attachment():
    resources = network()
    resources["aws_security_group"]["app"] = {
        "ingress": [{"security_groups": ["${aws_security_group.edge.id}"]}]
    }
    resources["aws_security_group_rule"] = {
        "from_edge": {
            "security_group_id": "${aws_security_group.app.id}",
            "source_security_group_id": "${aws_security_group.edge.id}",
            "type": "ingress",
        }
    }
    value = package(resources, "AWS-0104", "aws_security_group.edge")
    assert assess(value)["contextual-v1"]["remaining_blocking"] == 1
    assert assess(value)["contextual-v2"]["remaining_blocking"] == 0
    resources["aws_instance"] = {
        "app": {"vpc_security_group_ids": ["${aws_security_group.edge.id}"]}
    }
    assert (
        assess(package(resources, "AWS-0104", "aws_security_group.edge"))[
            "contextual-v2"
        ]["remaining_blocking"]
        == 1
    )


def test_counted_subnet_associations_and_unresolved_variables():
    resources = {
        "aws_vpc": {"v": {}},
        "aws_internet_gateway": {"igw": {"vpc_id": "${aws_vpc.v.id}"}},
        "aws_subnet": {
            "public": {"count": "${length(local.names)}", "vpc_id": "${aws_vpc.v.id}"}
        },
        "aws_route_table": {
            "public": {
                "vpc_id": "${aws_vpc.v.id}",
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
                "count": 2,
                "subnet_id": "${aws_subnet.public[count.index].id}",
                "route_table_id": "${aws_route_table.public.id}",
            }
        },
    }
    value = package(
        resources, "CKV_AWS_130", "aws_subnet.public[0]", locals={"names": ["a", "b"]}
    )
    assert assess(value)["contextual-v2"]["remaining_blocking"] == 0
    resources["aws_subnet"]["public"]["count"] = "${length(var.names)}"
    assert (
        assess(package(resources, "CKV_AWS_130", "aws_subnet.public[0]"))[
            "contextual-v2"
        ]["remaining_blocking"]
        == 1
    )


def test_unresolved_conditional_is_not_proven_unrelated():
    from app.security.instances import Instances
    from app.security.profiles_v2 import EvidenceV2

    graph = Instances({"terraform/main.tf": 'resource "aws_subnet" "public" {}'})
    subnet = graph.find("terraform", "aws_subnet.public")
    assert not EvidenceV2.unrelated_subnet(
        "${var.test ? aws_subnet.private.id : local.public_id}", subnet
    )
    assert EvidenceV2.unrelated_subnet("${aws_subnet.private[count.index].id}", subnet)


def test_nlb_with_mixed_tcp_listener_stays_blocking():
    resources = network("network", "TLS")
    resources["aws_lb_listener"]["plain"] = {
        "load_balancer_arn": "${aws_lb.edge.arn}",
        "port": 80,
        "protocol": "TCP",
    }
    assert not assess(package(resources))["contextual-v2"]["checks_passed"]


def test_all_saved_final_packages_keep_exact_strict_and_v1_assessments():
    from scripts.phase9i_replay import inventory

    try:
        packages, _ = inventory()
    except FileNotFoundError:
        pytest.skip("read-only final-set snapshots are unavailable")
    assert len(packages) == 81
    for item in packages:
        actual = assess(item["package"])
        for profile in ("strict", "contextual-v1"):
            assert actual[profile] == item["package"]["profile_assessments"][profile], (
                item["key"]
            )


@pytest.mark.parametrize("conflict", ["duplicate", "unknown_binding"])
def test_public_subnet_requires_unique_known_default_routes(conflict):
    resources = {
        "aws_vpc": {"v": {}},
        "aws_subnet": {"public": {"vpc_id": "${aws_vpc.v.id}"}},
        "aws_internet_gateway": {"igw": {"vpc_id": "${aws_vpc.v.id}"}},
        "aws_route_table": {
            "public": {
                "vpc_id": "${aws_vpc.v.id}",
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
    value = package(resources, "CKV_AWS_130", "aws_subnet.public")
    assert assess(value)["contextual-v2"]["remaining_blocking"] == 0
    if conflict == "duplicate":
        resources["aws_route_table"]["public"]["route"].append(
            {
                "cidr_block": "0.0.0.0/0",
                "nat_gateway_id": "${aws_nat_gateway.nat.id}",
            }
        )
    else:
        resources["aws_route"] = {
            "ambiguous": {
                "count": "${var.count}",
                "route_table_id": (
                    "${var.choice ? aws_route_table.other.id : local.public_table}"
                ),
            }
        }
    assert (
        assess(package(resources, "CKV_AWS_130", "aws_subnet.public"))["contextual-v2"][
            "remaining_blocking"
        ]
        == 1
    )
