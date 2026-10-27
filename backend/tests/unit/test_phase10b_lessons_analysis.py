"""FR-A-05, FR-S-07: deterministic instruction judgments are evidence-based."""

import json

import pytest

from scripts.phase10b_lessons import inspect

pytestmark = pytest.mark.req("FR-A-05", "FR-S-07", "NFR-01")


def package():
    resources = {
        "aws_vpc": {"vpc": {}},
        "aws_internet_gateway": {"igw": {"vpc_id": "${aws_vpc.vpc.id}"}},
        "aws_nat_gateway": {"nat": {"subnet_id": "${aws_subnet.public_a.id}"}},
        "aws_subnet": {
            name: {"vpc_id": "${aws_vpc.vpc.id}", "availability_zone": zone}
            for name, zone in [
                ("public_a", "eu-central-1a"),
                ("public_b", "eu-central-1b"),
                ("private", "eu-central-1a"),
            ]
        },
        "aws_route_table": {
            "public": {
                "vpc_id": "${aws_vpc.vpc.id}",
                "route": [
                    {
                        "cidr_block": "0.0.0.0/0",
                        "gateway_id": "${aws_internet_gateway.igw.id}",
                    }
                ],
            },
            "private": {
                "vpc_id": "${aws_vpc.vpc.id}",
                "route": [
                    {
                        "cidr_block": "0.0.0.0/0",
                        "nat_gateway_id": "${aws_nat_gateway.nat.id}",
                    }
                ],
            },
        },
        "aws_route_table_association": {
            name: {
                "subnet_id": "${aws_subnet." + name + ".id}",
                "route_table_id": "${aws_route_table."
                + ("private" if name == "private" else "public")
                + ".id}",
            }
            for name in ["public_a", "public_b", "private"]
        },
        "aws_ecs_service": {
            "tasks": {
                "network_configuration": [
                    {
                        "subnets": ["${aws_subnet.private.id}"],
                        "security_groups": ["${aws_security_group.external.id}"],
                        "assign_public_ip": False,
                    }
                ]
            }
        },
        "aws_lb": {
            "edge": {
                "internal": False,
                "subnets": ["${aws_subnet.public_a.id}", "${aws_subnet.public_b.id}"],
                "access_logs": [{"enabled": True}],
            }
        },
    }
    return resources


def inspect_resources(resources):
    return inspect({"terraform/main.tf.json": json.dumps({"resource": resources})})


def test_positive_nat_route_and_distinct_public_az_evidence():
    view = inspect_resources(package())
    assert view["outbound"] == "followed"
    assert view["outbound_evidence"]["proven_nat_routes"] == 1
    assert view["public_lb_two_az"] == "followed"
    assert view["logging_and_no_duplicates"] == "followed"


@pytest.mark.parametrize("change", ["nat", "private_route", "igw_route"])
def test_nat_declaration_without_required_routes_is_not_followed(change):
    resources = package()
    if change == "nat":
        del resources["aws_nat_gateway"]
    elif change == "private_route":
        resources["aws_route_table"]["private"]["route"] = []
    else:
        resources["aws_route_table"]["public"]["route"] = []
    assert inspect_resources(resources)["outbound"] == "not_followed"


def test_dynamic_az_input_is_unknown_even_with_literal_default():
    resources = package()
    resources["aws_subnet"]["public_a"]["availability_zone"] = "${var.zone}"
    files = {
        "terraform/main.tf.json": json.dumps(
            {"variable": {"zone": {"default": "eu-central-1a"}}, "resource": resources}
        )
    }
    assert inspect(files)["public_lb_two_az"] == "unknown"


def test_logging_absence_and_duplicate_blocks_are_not_partial_success():
    resources = package()
    del resources["aws_lb"]["edge"]["access_logs"]
    assert inspect_resources(resources)["logging_and_no_duplicates"] == "not_followed"
    files = {
        "terraform/main.tf.json": json.dumps({"resource": package()}),
        "terraform/duplicate.tf": 'resource "aws_lb" "edge" { internal = false }\n',
    }
    assert inspect(files)["logging_and_no_duplicates"] == "not_followed"
    assert inspect(files)["outbound"] == "followed"  # Independent network evidence.


def test_committed_analysis_recomputes_exactly_without_model_calls():
    from scripts.phase10b_lessons import FOLDER, analyse

    snapshots = [
        (p.name, json.loads(p.read_text())) for p in sorted(FOLDER.glob("run*.json"))
    ]
    measured = analyse(snapshots)
    assert measured == json.loads((FOLDER / "analysis.json").read_text())
    assert len(measured["rows"]) == 12 and len(measured["calls"]) == 79
    assert sum(c["enabled"] for c in measured["calls"]) == 10
    assert measured["telemetry_issues"] == []


@pytest.mark.parametrize("corruption", ["block_hash", "lesson_ids", "fixer_scope"])
def test_corrupt_provenance_is_reported_instead_of_silently_accepted(corruption):
    from scripts.phase10b_lessons import FOLDER, analyse

    snapshot = json.loads((FOLDER / "run2-lesson-v1.json").read_text())
    if corruption == "fixer_scope":
        call = next(
            c
            for c in snapshot["telemetry"]
            if c.get("kind") == "llm" and c.get("role") == "fixer"
        )
        call["lesson_usage"] = {"enabled": True, "lesson_ids": ["unscoped"]}
    else:
        call = next(
            c
            for c in snapshot["telemetry"]
            if (c.get("lesson_usage") or {}).get("enabled")
        )
        call["lesson_usage"][corruption] = (
            ["wrong"] if corruption == "lesson_ids" else "wrong"
        )
    assert analyse([("run2-lesson-v1.json", snapshot)])["telemetry_issues"]
