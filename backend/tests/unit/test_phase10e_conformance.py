"""FR-S-02/03/07: repairs proceed; only confirmed final changes require review."""

import json
from copy import deepcopy

import pytest

from app.domain.enums import PackageStatus as P
from app.domain.enums import RunStatus
from app.domain.review import package_presentation
from app.domain.states import readiness_after_validation
from app.security.plan_conformance import assess_plan_conformance
from tests.unit.test_phase10b_conformance import files, plan

pytestmark = pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-07")


def package(resources):
    return {"terraform/main.tf.json": json.dumps({"resource": resources})}


@pytest.mark.parametrize("public", [True, False])
@pytest.mark.parametrize("hcl", [True, False])
def test_final_known_exposure_change(public, hcl):
    before, after = files({"internal": not public}), files({"internal": public})
    if hcl:
        before = {
            "terraform/main.tf": 'resource "aws_lb" "edge" {\n'
            f" internal = {str(not public).lower()}\n}}\n"
        }
        after = {
            p: s.replace(str(not public).lower(), str(public).lower())
            for p, s in before.items()
        }
    assessment = assess_plan_conformance(plan(public), before, after)
    assert assessment.conflicts and not assessment.notes
    row = assessment.conflicts[0]
    assert row.property == "internal" and row.rule_id is None
    assert all(value in row.message for value in ("edge", "aws_lb.edge", "internal"))
    assert (
        readiness_after_validation(
            P.SCAN_CLEAN, P.VALID, plan_conformance_conflict=True
        )
        == P.PENDING_REVIEW
    )


@pytest.mark.parametrize("change", ["variable", "logging", "encryption", "eip"])
def test_unrelated_repairs_have_no_conformance_involvement(change):
    before = files(extra={"aws_eip": {"nat": {"vpc": True}}})
    after = json.loads(before["terraform/main.tf.json"])
    if change == "variable":
        after["variable"] = {"name": {"type": "string"}}
    elif change == "logging":
        after["resource"]["aws_lb"]["edge"]["access_logs"] = [{"enabled": True}]
    elif change == "encryption":
        after["resource"]["aws_ebs_volume"] = {"data": {"encrypted": True}}
    else:
        after["resource"]["aws_eip"]["nat"] = {"domain": "vpc"}
    assessment = assess_plan_conformance(
        plan(), before, {"terraform/main.tf.json": json.dumps(after)}
    )
    assert not assessment.conflicts and not assessment.notes


@pytest.mark.parametrize("missing", [True, False])
def test_unknowns_are_informational_and_do_not_prevent_checks_passed(missing):
    before = None if missing else files({"internal": "${var.flag}"})
    after = files({"internal": True})
    assessment = assess_plan_conformance(plan(), before, after)
    assert not assessment.conflicts and assessment.notes
    assert (
        readiness_after_validation(
            P.SCAN_CLEAN, P.VALID, plan_conformance_conflict=bool(assessment.conflicts)
        )
        == P.CHECKS_PASSED
    )
    presentation = package_presentation(
        RunStatus.SUCCESS,
        P.PENDING_REVIEW,
        after,
        {"final": {"outcome": "clean", "remaining_blocking": []}},
        {"summary": {"result": "valid"}, "plan_conformance": assessment.model_dump()},
        None,
    )
    assert "plan_conformance_conflict" not in presentation["review_reasons"]


def test_ambiguous_binding_never_blocks_fixes():
    before = package(
        {"aws_lb": {"one": {"internal": False}, "two": {"internal": False}}}
    )
    after = package({"aws_lb": {"one": {"internal": True}, "two": {"internal": False}}})
    assessment = assess_plan_conformance(plan(), before, after)
    assert (
        not assessment.conflicts and assessment.notes[0].property == "service_binding"
    )


def test_final_evidence_is_independent_of_scanner_findings_and_clears_history():
    assessment = assess_plan_conformance(plan(), files(), files({"internal": True}))
    security = {"final": {"outcome": "clean", "remaining_blocking": []}}
    presentation = package_presentation(
        RunStatus.SUCCESS,
        P.PENDING_REVIEW,
        files(),
        security,
        {"summary": {"result": "valid"}, "plan_conformance": assessment.model_dump()},
        None,
    )
    assert presentation["review_reasons"] == ["plan_conformance_conflict"]
    assert presentation["plan_conflicts"][0]["rule_id"] is None
    cleared = assess_plan_conformance(plan(), files(), files())
    presentation = package_presentation(
        RunStatus.SUCCESS,
        P.CHECKS_PASSED,
        files(),
        security,
        {"summary": {"result": "valid"}, "plan_conformance": cleared.model_dump()},
        None,
    )
    assert not presentation["review_reasons"] and not presentation["plan_conflicts"]


def network():
    return {
        "aws_lb": {
            "edge": {
                "internal": False,
                "subnets": ["${aws_subnet.public.id}"],
                "security_groups": ["${aws_security_group.edge.id}"],
            }
        },
        "aws_vpc": {"vpc": {}},
        "aws_subnet": {
            n: {"vpc_id": "${aws_vpc.vpc.id}"} for n in ("public", "private")
        },
        "aws_internet_gateway": {"igw": {"vpc_id": "${aws_vpc.vpc.id}"}},
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
            "private": {"vpc_id": "${aws_vpc.vpc.id}"},
        },
        "aws_route_table_association": {
            n: {
                "subnet_id": "${aws_subnet." + n + ".id}",
                "route_table_id": "${aws_route_table." + n + ".id}",
            }
            for n in ("public", "private")
        },
        "aws_lb_listener": {
            "https": {
                "load_balancer_arn": "${aws_lb.edge.arn}",
                "port": 443,
                "protocol": "HTTPS",
            }
        },
        "aws_security_group": {
            "edge": {
                "ingress": [
                    {
                        "from_port": 443,
                        "to_port": 443,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"],
                    }
                ]
            }
        },
    }


@pytest.mark.parametrize("change", ["subnets", "route", "listener", "ingress", "cidr"])
def test_final_removed_public_path_requires_review(change):
    before = network()
    after = deepcopy(before)
    if change == "subnets":
        after["aws_lb"]["edge"]["subnets"] = ["${aws_subnet.private.id}"]
    elif change == "route":
        after["aws_route_table"]["public"]["route"] = []
    elif change == "listener":
        del after["aws_lb_listener"]
    elif change == "ingress":
        after["aws_security_group"]["edge"]["ingress"] = []
    else:
        after["aws_security_group"]["edge"]["ingress"][0]["cidr_blocks"] = [
            "10.0.0.0/8"
        ]
    assessment = assess_plan_conformance(plan(), package(before), package(after))
    assert assessment.conflicts


def test_equivalent_listener_rename_and_tls_change_are_not_regressions():
    before = network()
    after = deepcopy(before)
    after["aws_lb_listener"]["renamed"] = after["aws_lb_listener"].pop("https")
    after["aws_lb_listener"]["renamed"]["protocol"] = "TLS"
    assert not assess_plan_conformance(
        plan(), package(before), package(after)
    ).conflicts


def test_restored_final_exposure_clears_intermediate_flip():
    original = files()
    intermediate = files({"internal": True})
    final = files({"internal": False, "drop_invalid_header_fields": True})
    assert assess_plan_conformance(plan(), original, intermediate).conflicts
    assert not assess_plan_conformance(plan(), original, final).conflicts


def test_unknown_security_group_source_cannot_hide_removed_literal_listener():
    before = network()
    before["aws_security_group"]["edge"]["ingress"] = [
        {
            "from_port": 443,
            "to_port": 443,
            "protocol": "tcp",
            "source_security_group_id": "${var.allowed_group}",
        }
    ]
    after = deepcopy(before)
    del after["aws_lb_listener"]
    assessment = assess_plan_conformance(plan(), package(before), package(after))
    assert any(c.property == "listener/ingress" for c in assessment.conflicts)


def test_unresolved_replacement_listener_is_informational_only():
    before = network()
    after = deepcopy(before)
    after["aws_lb_listener"]["https"]["port"] = "${var.port}"
    assessment = assess_plan_conformance(plan(), package(before), package(after))
    assert not assessment.conflicts and assessment.notes


def test_attached_eip_domain_migration_is_also_informationally_silent():
    resources = {
        "aws_instance": {"edge": {"subnet_id": "${var.subnet}"}},
        "aws_eip": {"edge": {"instance": "${aws_instance.edge.id}", "vpc": True}},
    }
    after = deepcopy(resources)
    after["aws_eip"]["edge"].pop("vpc")
    after["aws_eip"]["edge"]["domain"] = "vpc"
    assessment = assess_plan_conformance(
        plan(kind="ec2"), package(resources), package(after)
    )
    assert not assessment.conflicts and not assessment.notes


def test_disabling_a_planned_public_cloudfront_endpoint_is_a_known_regression():
    before = package({"aws_cloudfront_distribution": {"edge": {"enabled": True}}})
    after = package({"aws_cloudfront_distribution": {"edge": {"enabled": False}}})
    assessment = assess_plan_conformance(plan(kind="cloudfront"), before, after)
    assert assessment.conflicts[0].property == "enabled"
    assert "disabled" in assessment.conflicts[0].message
