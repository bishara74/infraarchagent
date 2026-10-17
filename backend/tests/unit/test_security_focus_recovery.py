"""FR-S-02/09: focused calls and measured recovery of existing-path proposals."""

import json
import re
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.agents.budget import AgentBudget
from app.agents.remediation import apply_proposals
from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixAgent, validate_fix
from app.core.config import get_settings
from app.core.logging import RedactingFilter
from app.domain.enums import Severity, Variant
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.llm.stub import StubAdapter
from app.pipeline.demo_stub import DEMO_PLAN
from app.scanners.scan import ScanResult
from app.security.focus import focused_findings

PLAN = DeploymentPlan.model_validate(DEMO_PLAN)
FILES = {
    "terraform/main.tf": 'output "encrypted" { value = var.encrypt }\n',
    "terraform/variables.tf": 'variable "encrypt" { default = false }\n',
}


def raw(kind="existing"):
    content = FILES["terraform/main.tf"]
    extra = {"terraform/variables.tf": 'variable "encrypt" { default = true }\n'}
    if kind == "primary":
        content = 'output "encrypted" { value = true }\n'
        extra = {"terraform/main.tf": content}
    if kind == "mixed":
        extra["terraform/audit.tf"] = 'output "audit" { value = true }\n'
    return {
        "file": {"path": "terraform/main.tf", "content": content},
        "new_files": extra,
    }


def finding(resource, rule="RULE", severity=Severity.HIGH):
    return Violation(
        rule_id=rule,
        file_path="terraform/main.tf",
        resource=resource,
        severity=severity,
        tool="trivy",
        message="synthetic",
        blocking=True,
    )


@pytest.mark.req("FR-S-02", "FR-S-09")
def test_focus_limits_severity_and_equal_severity_rotation():
    findings = [
        finding(f"aws_instance.{name}", f"RULE_{i}")
        for name in "abc"
        for i in range(20)
    ]
    first = focused_findings(findings, 2, 12)
    second = focused_findings(findings, 2, 12, 1)
    assert len(first) == len(second) == 12
    assert {f.resource for f in first} == {"aws_instance.a", "aws_instance.b"}
    assert {f.resource for f in second} == {"aws_instance.c", "aws_instance.a"}
    assert all(
        sum(f.resource == r for f in first) == 6 for r in {f.resource for f in first}
    )
    critical = finding("aws_instance.critical", "CRIT", Severity.CRITICAL)
    assert focused_findings([*findings, critical], 2, 12)[0] == critical


@pytest.mark.req("FR-S-02", "FR-S-03", "NFR-01")
async def test_scripted_existing_file_recovery_measured_after_all_guards():
    normalized = recovered = 0
    for kind in ("existing", "primary", "mixed", "guard_rejected"):
        adapter = StubAdapter(script=[json.dumps(raw(kind))])

        class Verifier:
            async def checks(self, files):
                return []

        class Scanner:
            async def scan(self, files, variant, reject=(kind == "guard_rejected")):
                return ScanResult(
                    [finding("new.blocker", "NEW")] if reject else [],
                    {},
                )

        settings = get_settings()
        security = SecurityAgent(
            Scanner(), FixAgent(adapter), None, settings, terraform_verifier=Verifier()
        )
        record = {}
        retained, fixes, _, _ = await security._fix_iteration(
            SimpleNamespace(plan=PLAN),
            Variant.SECURITY,
            FILES,
            {"terraform/main.tf": [finding("original.target")]},
            AgentBudget(60),
            ScanResult([finding("original.target")], {}),
            record,
            feedback=None,
            validation_failures=[],
        )
        normalized += bool(fixes[0]["normalized_existing_paths"])
        recovered += bool(fixes[0]["recovered_existing_proposal"])
        assert "terraform/variables.tf" in adapter.prompts[0]
        related = re.search(
            r'<related_files id="[^"]+">\n(.*?)\n</related_files',
            adapter.prompts[0],
            re.S,
        )
        assert (
            json.loads(related[1])["terraform/variables.tf"]
            == FILES["terraform/variables.tf"]
        )
        assert (retained != FILES) == (kind != "guard_rejected")
    # Four colliding proposals normalized; three retained after every guard.
    assert (normalized, recovered) == (4, 3)


@pytest.mark.req("FR-S-02", "NFR-01")
@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("conflict", "conflicting_edits"),
        ("unseen", "existing_file_context_missing"),
        ("missing", "edit_file_missing"),
        ("suppression", "new_suppression"),
        ("syntax", "invalid_syntax"),
    ],
)
def test_existing_file_recovery_rejects_invalid_changes_with_feedback(mutation, reason):
    data = raw()
    context = None
    if mutation == "conflict":
        data["new_files"]["terraform/main.tf"] = "locals { changed = true }"
    if mutation == "unseen":
        context = {"terraform/main.tf"}
    if mutation == "missing":
        data["edits"] = {"terraform/missing.tf": "locals {}"}
    if mutation == "suppression":
        data["new_files"]["terraform/variables.tf"] += "# checkov:skip=RULE\n"
    if mutation == "syntax":
        data["new_files"]["terraform/variables.tf"] = "variable {"
    proposal = validate_fix(
        data, path="terraform/main.tf", files=FILES, plan=PLAN, context_paths=context
    )
    assert not proposal.accepted and proposal.reason == reason


@pytest.mark.req("FR-S-02")
def test_edits_are_backward_compatible_and_stale_bases_reject():
    data = raw()
    data["edits"] = data.pop("new_files")
    proposal = validate_fix(data, path="terraform/main.tf", files=FILES, plan=PLAN)
    assert proposal.accepted
    changed = {
        **FILES,
        "terraform/variables.tf": 'variable "encrypt" { default = true }',
    }
    _, records = apply_proposals(
        changed, [proposal], {"terraform/main.tf": []}, PLAN, RedactingFilter()
    )
    assert not records[0]["accepted"] and records[0]["reason"] == "stale_edit_base"
    no_base = replace(proposal, edit_bases={})
    _, records = apply_proposals(
        FILES, [no_base], {"terraform/main.tf": []}, PLAN, RedactingFilter()
    )
    assert records[0]["reason"] == "edit_base_missing"


@pytest.mark.req("FR-S-04", "PR-05")
async def test_budget_skip_does_not_claim_findings_were_sent():
    class Fix:
        async def propose(self, **kwargs):
            raise AssertionError("no fixer call allowed after budget cutoff")

    security = SecurityAgent(None, Fix(), None, get_settings())
    _, records, _ = await security._fix_pass(
        SimpleNamespace(plan=PLAN),
        Variant.SECURITY,
        FILES,
        {"terraform/main.tf": [finding("original.target")]},
        AgentBudget(0.5),
        feedback=None,
        validation_failures=[],
    )
    assert records[0]["call_attempted"] is False
    assert records[0]["findings_sent"] == records[0]["resources_sent"] == 0
    assert records[0]["findings_deferred"] == 1
