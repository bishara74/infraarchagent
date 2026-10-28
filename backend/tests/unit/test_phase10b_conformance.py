"""FR-S-02/03/07, FR-A-05: remediation preserves planned exposure."""

import json

import pytest

from app.agents.budget import AgentBudget
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.scanners.scan import ScanResult
from app.security.acceptance import CandidateGuard
from app.security.partial import RetainedCandidate, accept_groups
from app.security.plan_conformance import plan_regressions
from tests.unit.test_security_partial import Scanner, Verifier

pytestmark = pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-07", "FR-A-05")


def plan(public=True, kind="alb"):
    return DeploymentPlan.model_validate(
        {
            "cloud_provider": "aws",
            "services": [{"name": "edge", "aws_service": kind, "purpose": "API"}],
            "dependencies": [],
            "storage": [],
            "file_types": ["terraform"],
            "ambiguities": [],
            "network": {
                "public_services": ["edge"] if public else [],
                "private_services": [] if public else ["edge"],
                "ingress": ["HTTPS 443 from 0.0.0.0/0 to edge"],
                "notes": "",
            },
        }
    )


def files(body=None, extra=None):
    return {
        "terraform/main.tf.json": json.dumps(
            {
                "resource": {
                    "aws_lb": {"edge": body or {"internal": False}},
                    **(extra or {}),
                }
            }
        )
    }


def finding():
    return Violation(
        rule_id="AWS-0053",
        resource="aws_lb.edge",
        file_path="terraform/main.tf.json",
        message="public",
        tool="trivy",
        blocking=True,
    )


@pytest.mark.parametrize("hcl", [False, True])
def test_observed_alb_flip(hcl):
    before, after = files(), files({"internal": True})
    if hcl:
        before = {
            "terraform/main.tf": 'resource "aws_lb" "edge" { internal = false }\n'
        }
        after = {"terraform/main.tf": 'resource "aws_lb" "edge" { internal = true }\n'}
    conflict = plan_regressions(plan(), before, after, [finding()])
    assert conflict[0]["property"] == "exposure"
    assert conflict[0]["assessment"] == "regression"
    if not hcl:
        assert conflict[0]["rule_ids"] == ["AWS-0053"]


@pytest.mark.parametrize(
    "body",
    [
        {"internal": "${var.internal}"},
        {"scheme": "internal"},
        {"internal": "${local.internal}"},
    ],
)
def test_nlb_scheme_and_unknowns(body):
    result = plan_regressions(plan(kind="nlb"), files(), files(body))
    assert result and result[0]["property"] == "exposure"


def test_private_service_cannot_be_made_public():
    assert plan_regressions(plan(False), files({"internal": True}), files())


def test_unrelated_security_fix_with_unknown_exposure_is_accepted():
    before = files({"internal": "${var.internal}"})
    after = files({"internal": "${var.internal}", "drop_invalid_header_fields": True})
    assert not plan_regressions(plan(), before, after)


def test_local_dependency_change_fails_closed():
    before = {
        "terraform/main.tf": "locals { internal = false }\n"
        'resource "aws_lb" "edge" { internal = local.internal }\n'
    }
    after = {p: s.replace("= false", "= true") for p, s in before.items()}
    assert plan_regressions(plan(), before, after)


def test_missing_or_ambiguous_service_cannot_escape_guard():
    before = files(extra={"aws_alb": {"other": {"internal": False}}})
    data = json.loads(before["terraform/main.tf.json"])
    del data["resource"]["aws_lb"]
    assert plan_regressions(
        plan(), before, {"terraform/main.tf.json": json.dumps(data)}
    )


def test_subnet_move_and_route_removal():
    extra = {
        "aws_vpc": {"vpc": {}},
        "aws_subnet": {
            "public": {"vpc_id": "${aws_vpc.vpc.id}"},
            "private": {"vpc_id": "${aws_vpc.vpc.id}"},
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
            for n in ["public", "private"]
        },
    }
    before = files({"internal": False, "subnets": ["${aws_subnet.public.id}"]}, extra)
    after = files({"internal": False, "subnets": ["${aws_subnet.private.id}"]}, extra)
    assert any(
        r["property"] == "subnets" for r in plan_regressions(plan(), before, after)
    )
    extra["aws_route_table"]["public"]["route"] = []
    after = files({"internal": False, "subnets": ["${aws_subnet.public.id}"]}, extra)
    assert any(
        r["property"] == "subnets" for r in plan_regressions(plan(), before, after)
    )


def test_listener_and_planned_ingress_cannot_be_removed():
    extra = {
        "aws_lb_listener": {
            "https": {
                "load_balancer_arn": "${aws_lb.edge.arn}",
                "port": 443,
                "protocol": "HTTPS",
            }
        }
    }
    assert (
        plan_regressions(plan(), files(extra=extra), files())[0]["property"]
        == "ingress"
    )


@pytest.mark.parametrize(
    "kind,resource,old,new",
    [
        (
            "apigateway",
            "aws_api_gateway_rest_api",
            {"endpoint_configuration": [{"types": ["REGIONAL"]}]},
            {"endpoint_configuration": [{"types": ["PRIVATE"]}]},
        ),
        (
            "cloudfront",
            "aws_cloudfront_distribution",
            {"enabled": True},
            {"enabled": False},
        ),
        (
            "rds",
            "aws_db_instance",
            {"publicly_accessible": False},
            {"publicly_accessible": True},
        ),
    ],
)
def test_other_endpoint_types(kind, resource, old, new):
    def package(body):
        return {
            "terraform/main.tf.json": json.dumps(
                {"resource": {resource: {"edge": body}}}
            )
        }

    assert plan_regressions(
        plan(public=kind != "rds", kind=kind), package(old), package(new)
    )


async def test_combined_and_partial_acceptance_defers_exposure_to_final_check():
    before = files(extra={"aws_s3_bucket": {"data": {}}})
    candidate = files(
        {"internal": True}, {"aws_s3_bucket": {"data": {"force_destroy": False}}}
    )
    record = {
        "terraform_verification_seconds": 0.0,
        "security_verification_seconds": 0.0,
    }

    class ExposureScanner(Scanner):
        async def scan(self, files, variant):
            data = json.loads(files["terraform/main.tf.json"])
            return ScanResult(
                [finding()]
                if not data["resource"]["aws_lb"]["edge"]["internal"]
                else [],
                {},
            )

    guard = CandidateGuard(
        Verifier(),
        ExposureScanner(),
        Variant.SECURITY,
        AgentBudget(60),
        record,
        plan=plan(),
        targeted=[finding()],
    )
    scan = ScanResult([finding()], {})
    checks = await guard.checks(before)
    result = await guard.evaluate(before, candidate, checks, scan)
    assert result.reason is None and not result.scan.violations
    records = []
    retained, _, final = await accept_groups(
        guard,
        before,
        candidate,
        checks,
        scan,
        6,
        records,
        RetainedCandidate(before, scan),
    )
    data = json.loads(retained["terraform/main.tf.json"])
    assert data["resource"]["aws_lb"]["edge"]["internal"] is True
    assert data["resource"]["aws_s3_bucket"]["data"]["force_destroy"] is False
    assert all(r["status"] == "kept" for r in records)
    assert not final.violations
    from app.security.plan_conformance import assess_plan_conformance

    assert assess_plan_conformance(plan(), before, retained).conflicts


def test_subnet_dependency_through_local_is_not_invisible():
    before = {
        "terraform/main.tf": "locals { subnet = aws_subnet.edge.id }\n"
        'resource "aws_lb" "edge" {\n internal = false\n subnets = [local.subnet]\n}\n'
        'resource "aws_subnet" "edge" { cidr_block = "10.0.1.0/24" }\n'
    }
    after = {
        p: s.replace("10.0.1.0/24", "10.0.2.0/24").replace(
            'cidr_block = "10.0.2.0/24"', "vpc_id = var.other_vpc"
        )
        for p, s in before.items()
    }
    assert plan_regressions(plan(), before, after)


def test_ambiguous_binding_rejects_changed_network_dependency_only():
    def package(port, secure=False):
        return {
            "terraform/main.tf.json": json.dumps(
                {
                    "resource": {
                        "aws_lb": {
                            "one": {
                                "internal": False,
                                "security_groups": ["${aws_security_group.edge.id}"],
                                "drop_invalid_header_fields": secure,
                            },
                            "two": {"internal": False},
                        },
                        "aws_security_group": {
                            "edge": {
                                "ingress": [
                                    {
                                        "from_port": port,
                                        "to_port": port,
                                        "protocol": "tcp",
                                        "cidr_blocks": ["0.0.0.0/0"],
                                    }
                                ]
                            }
                        },
                    }
                }
            )
        }

    assert (
        plan_regressions(plan(), package(443), package(80))[0]["assessment"]
        == "unknown"
    )
    assert not plan_regressions(plan(), package(443), package(443, True))


def test_unsupported_service_cannot_silently_accept_exposure_change():
    assert (
        plan_regressions(plan(kind="edgeproxy"), files(), files({"internal": True}))[0][
            "assessment"
        ]
        == "unknown"
    )
    assert not plan_regressions(
        plan(kind="edgeproxy"),
        files(),
        files({"internal": False, "drop_invalid_header_fields": True}),
    )


async def test_provisional_syntax_fixer_has_no_conformance_rejection():
    from app.agents.generation_syntax import recover_generation_syntax
    from app.agents.security.fix import FixProposal

    original = {
        "terraform/main.tf": 'resource "aws_lb" "edge" {\n'
        ' internal = false\n name = "unfinished\n}\n'
    }
    repaired = 'resource "aws_lb" "edge" {\n internal = false\n name = "fixed"\n}\n'

    class Fixer:
        async def propose(self, **kwargs):
            return FixProposal(
                kwargs["path"], True, None, repaired.replace("false", "true"), {}, ()
            )

    async def regenerate(feedback):
        return {"terraform/main.tf": repaired}

    files, report = await recover_generation_syntax(
        original,
        plan(),
        Fixer(),
        AgentBudget(30),
        redact=lambda x: x,
        regenerate=regenerate,
    )
    assert files["terraform/main.tf"] == repaired.replace("false", "true")
    assert report["path"] == "syntax_round_1"
    assert all(
        a["reason"] != "plan_conformance_regression"
        for r in report["rounds"]
        for a in r["actions"]
    )
