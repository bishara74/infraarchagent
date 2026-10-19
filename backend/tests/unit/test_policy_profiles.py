"""FR-S-04/NFR-01: secondary exceptions require exact parsed relationships."""

import copy
import json

import pytest

from app.domain.enums import PackageStatus
from app.domain.states import readiness_after_validation
from app.security.profiles import assess, profile


def ref(address):
    return "${" + address + ".id}"


def source(resources):
    return {"terraform/main.tf.json": json.dumps({"resource": resources})}


def log_resources():
    return {
        "aws_s3_bucket": {"app": {}, "logs": {}},
        "aws_s3_bucket_logging": {
            "app": {
                "bucket": ref("aws_s3_bucket.app"),
                "target_bucket": ref("aws_s3_bucket.logs"),
            }
        },
        "aws_s3_bucket_server_side_encryption_configuration": {
            "logs": {
                "bucket": ref("aws_s3_bucket.logs"),
                "rule": [
                    {
                        "apply_server_side_encryption_by_default": [
                            {"sse_algorithm": "AES256"}
                        ]
                    }
                ],
            }
        },
    }


def network_resources():
    return {
        "aws_security_group": {
            "edge": {
                "ingress": [
                    {
                        "from_port": 80,
                        "to_port": 80,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"],
                    }
                ]
            }
        },
        "aws_lb": {
            "edge": {
                "internal": False,
                "security_groups": [ref("aws_security_group.edge")],
            }
        },
        "aws_lb_listener": {
            "http": {
                "load_balancer_arn": ref("aws_lb.edge"),
                "port": 80,
                "protocol": "HTTP",
                "default_action": [
                    {
                        "type": "redirect",
                        "redirect": [
                            {
                                "protocol": "HTTPS",
                                "port": "443",
                                "status_code": "HTTP_301",
                            }
                        ],
                    }
                ],
            },
            "https": {
                "load_balancer_arn": ref("aws_lb.edge"),
                "port": 443,
                "protocol": "HTTPS",
                "certificate_arn": "arn:synthetic-certificate",
            },
        },
    }


def package(files, rule, resource):
    return {
        "files": files,
        "validation_report": {"summary": {"result": "valid"}},
        "security_report": {
            "final": {
                "outcome": "exhausted",
                "remaining_blocking": [
                    {
                        "rule_id": rule,
                        "resource": resource,
                        "file_path": "terraform/main.tf.json",
                    }
                ],
            }
        },
    }


@pytest.mark.req("FR-S-04", "NFR-01")
@pytest.mark.parametrize(
    "rule,resource",
    [
        ("CKV_AWS_145", "aws_s3_bucket.logs"),
        ("AWS-0132", "aws_s3_bucket_server_side_encryption_configuration.logs"),
        ("CKV_AWS_18", "aws_s3_bucket.logs"),
        ("AWS-0089", "aws_s3_bucket.logs"),
    ],
)
def test_log_targets_are_resource_specific_and_strict_is_unchanged(rule, resource):
    value = package(source(log_resources()), rule, resource)
    before = copy.deepcopy(value)
    views = assess(value)
    assert (
        views["strict"]["remaining_blocking"] == 1
        and not views["strict"]["checks_passed"]
    )
    assert views["contextual-v1"]["checks_passed"]
    assert views["contextual-v1"]["excepted"][0]["classification"] == "excepted"
    assert value == before
    assert (
        readiness_after_validation(PackageStatus.SCAN_EXHAUSTED, PackageStatus.VALID)
        == PackageStatus.PENDING_REVIEW
    )


@pytest.mark.req("FR-S-04", "NFR-01")
@pytest.mark.parametrize(
    "change",
    [
        "unrelated",
        "unknown",
        "self",
        "dynamic",
        "no_encryption",
        "kms",
        "comment",
        "duplicate",
    ],
)
def test_log_encryption_counterexamples_stay_blocking(change):
    resources = log_resources()
    if change == "unrelated":
        resources["aws_s3_bucket_server_side_encryption_configuration"]["logs"][
            "bucket"
        ] = ref("aws_s3_bucket.app")
    if change == "unknown":
        resources["aws_s3_bucket_logging"]["app"]["target_bucket"] = "${var.logs}"
    if change == "self":
        resources["aws_s3_bucket_logging"]["app"]["bucket"] = ref("aws_s3_bucket.logs")
    if change == "dynamic":
        resources["aws_s3_bucket"]["logs"]["count"] = "${var.count}"
    if change in {"no_encryption", "comment"}:
        resources.pop("aws_s3_bucket_server_side_encryption_configuration")
    if change == "kms":
        resources["aws_s3_bucket_server_side_encryption_configuration"]["logs"]["rule"][
            0
        ]["apply_server_side_encryption_by_default"][0]["sse_algorithm"] = "aws:kms"
    files = source(resources)
    if change == "comment":
        files["README.md"] = "# AES256 and aws_s3_bucket.logs is a log target"
    if change == "duplicate":
        files["terraform/duplicate.tf.json"] = json.dumps(
            {"resource": {"aws_s3_bucket": {"logs": {}}}}
        )
    assert not assess(package(files, "CKV_AWS_145", "aws_s3_bucket.logs"))[
        "contextual-v1"
    ]["checks_passed"]


@pytest.mark.req("FR-S-04", "NFR-01")
@pytest.mark.parametrize(
    "rule,resource",
    [
        ("AWS-0104", "aws_security_group.edge"),
        ("CKV_AWS_260", "aws_security_group.edge"),
        ("AWS-0053", "aws_lb.edge"),
    ],
)
def test_public_lb_relationships(rule, resource):
    assert assess(package(source(network_resources()), rule, resource))[
        "contextual-v1"
    ]["checks_passed"]


@pytest.mark.req("FR-S-04", "NFR-01")
@pytest.mark.parametrize(
    "change",
    [
        "private",
        "extra_consumer",
        "unknown_consumer",
        "forward",
        "listener_rule",
        "missing_https",
        "wide_ingress",
        "dynamic",
    ],
)
def test_public_lb_counterexamples(change):
    resources = network_resources()
    if change == "private":
        resources["aws_lb"]["edge"]["internal"] = True
    if change == "extra_consumer":
        resources["aws_instance"] = {
            "private": {"vpc_security_group_ids": [ref("aws_security_group.edge")]}
        }
    if change == "unknown_consumer":
        resources["aws_instance"] = {
            "private": {"vpc_security_group_ids": "${var.groups}"}
        }
    if change == "forward":
        resources["aws_lb_listener"]["http"]["default_action"][0]["type"] = "forward"
    if change == "listener_rule":
        resources["aws_lb_listener_rule"] = {
            "bypass": {
                "listener_arn": ref("aws_lb_listener.http"),
                "action": [{"type": "forward"}],
            }
        }
    if change == "missing_https":
        resources["aws_lb_listener"].pop("https")
    if change == "wide_ingress":
        resources["aws_security_group"]["edge"]["ingress"][0]["from_port"] = 0
    if change == "dynamic":
        resources["aws_security_group"]["edge"]["for_each"] = "${var.groups}"
    assert not assess(
        package(source(resources), "CKV_AWS_260", "aws_security_group.edge")
    )["contextual-v1"]["checks_passed"]


@pytest.mark.req("FR-S-04", "NFR-01")
@pytest.mark.parametrize(
    "change", [None, "nat", "missing", "ambiguous", "wrong_vpc", "dynamic"]
)
@pytest.mark.parametrize("rule", ["CKV_AWS_130", "AWS-0164"])
def test_public_subnets_require_exact_routing(change, rule):
    resources = {
        "aws_vpc": {"v": {}, "other": {}},
        "aws_internet_gateway": {"igw": {"vpc_id": ref("aws_vpc.v")}},
        "aws_subnet": {"public": {"vpc_id": ref("aws_vpc.v")}},
        "aws_route_table": {
            "public": {
                "vpc_id": ref("aws_vpc.v"),
                "route": [
                    {
                        "cidr_block": "0.0.0.0/0",
                        "gateway_id": ref("aws_internet_gateway.igw"),
                    }
                ],
            }
        },
        "aws_route_table_association": {
            "public": {
                "subnet_id": ref("aws_subnet.public"),
                "route_table_id": ref("aws_route_table.public"),
            }
        },
    }
    if change == "nat":
        resources["aws_route_table"]["public"]["route"][0] = {
            "cidr_block": "0.0.0.0/0",
            "nat_gateway_id": "${var.nat}",
        }
    if change == "missing":
        resources.pop("aws_route_table_association")
    if change == "ambiguous":
        resources["aws_route_table_association"]["second"] = dict(
            resources["aws_route_table_association"]["public"]
        )
    if change == "wrong_vpc":
        resources["aws_internet_gateway"]["igw"]["vpc_id"] = ref("aws_vpc.other")
    if change == "dynamic":
        resources["aws_route_table_association"]["public"]["count"] = "${var.count}"
    assert assess(package(source(resources), rule, "aws_subnet.public"))[
        "contextual-v1"
    ]["checks_passed"] is (change is None)


@pytest.mark.req("FR-S-04")
def test_profiles_are_versioned_and_replication_is_not_excepted():
    assert profile("strict")["entries"] == []
    entries = profile("contextual-v1")["entries"]
    assert all(
        e["justification"] and e["references"] and e["resource_types"] for e in entries
    )
    assert not assess(
        package(source(log_resources()), "CKV_AWS_144", "aws_s3_bucket.logs")
    )["contextual-v1"]["checks_passed"]


@pytest.mark.req("FR-S-04", "NFR-01")
@pytest.mark.parametrize("kind", ["main", "default"])
def test_public_subnet_configured_main_and_default_tables(kind):
    resources = {
        "aws_vpc": {"v": {}},
        "aws_internet_gateway": {"igw": {"vpc_id": ref("aws_vpc.v")}},
        "aws_subnet": {"public": {"vpc_id": ref("aws_vpc.v")}},
    }
    route = {"cidr_block": "0.0.0.0/0", "gateway_id": ref("aws_internet_gateway.igw")}
    if kind == "main":
        resources["aws_route_table"] = {
            "main": {"vpc_id": ref("aws_vpc.v"), "route": [route]}
        }
        resources["aws_main_route_table_association"] = {
            "main": {
                "vpc_id": ref("aws_vpc.v"),
                "route_table_id": ref("aws_route_table.main"),
            }
        }
    else:
        resources["aws_default_route_table"] = {
            "main": {
                "default_route_table_id": "${aws_vpc.v.default_route_table_id}",
                "route": [route],
            }
        }
    assert assess(package(source(resources), "AWS-0164", "aws_subnet.public"))[
        "contextual-v1"
    ]["checks_passed"]


@pytest.mark.req("FR-S-04", "NFR-01")
@pytest.mark.parametrize("port,expected", [(80, True), (22, False)])
def test_standalone_ingress_finding_is_resolved_to_its_own_rule(port, expected):
    resources = network_resources()
    resources["aws_security_group_rule"] = {
        "web": {
            "type": "ingress",
            "security_group_id": ref("aws_security_group.edge"),
            "from_port": port,
            "to_port": port,
            "protocol": "tcp",
            "cidr_blocks": ["0.0.0.0/0"],
        }
    }
    assert (
        assess(
            package(source(resources), "CKV_AWS_260", "aws_security_group_rule.web")
        )["contextual-v1"]["checks_passed"]
        is expected
    )
