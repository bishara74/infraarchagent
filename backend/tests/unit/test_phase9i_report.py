"""FR-V-01/FR-S-04: replay attribution includes rejected and unknown findings."""

import pytest

from scripts.phase9i_report import compare, proposal, select_before_context

pytestmark = pytest.mark.req("FR-V-01", "FR-S-04", "NFR-01")


def observation(findings, validation="invalid"):
    return {
        "validation": validation,
        "failed_checks": [] if validation == "valid" else [{"check_id": "helm.lint"}],
        "blockers": [
            dict(rule_id=r, file_path="terraform/main.tf", resource=n)
            for r, n in findings
        ],
        "profiles": {
            p: {"remaining_blocking": len(findings)}
            for p in ("strict", "contextual-v1", "contextual-v2")
        },
    }


def test_comparison_retains_new_findings_even_when_validation_improves():
    before = observation([("OLD", "aws_vpc.v")])
    after = observation([("NEW", "aws_vpc.v")], "valid")
    delta = compare(before, after)
    assert delta["validation_changed"]
    assert delta["removed"] == [("OLD", "terraform/main.tf", "aws_vpc.v")]
    assert delta["introduced"] == [("NEW", "terraform/main.tf", "aws_vpc.v")]
    assert delta["blocker_deltas"]["strict"] == 0


def test_security_replay_targets_only_observed_catalogue_findings():
    files = {
        "terraform/main.tf": (
            'resource "aws_subnet" "public" {\n map_public_ip_on_launch = true\n}\n'
        )
    }
    unchanged, records = proposal("addressing", files, observation([]))
    assert (unchanged, records) == (files, [])
    changed, records = proposal(
        "addressing", files, observation([("CKV_AWS_130", "aws_subnet.public")])
    )
    assert changed != files and records


def test_guidance_baseline_accepts_measured_legacy_or_current_sizes():
    from types import SimpleNamespace

    old = SimpleNamespace(
        schema_chars=1, checklist_chars=2, text="abc", truncated=False
    )
    new = SimpleNamespace(
        schema_chars=2, checklist_chars=2, text="abcd", truncated=True
    )
    assert (
        select_before_context(
            dict(schema=1, checklist=2, total=3, truncated=False), old, new
        )[0]
        is old
    )
    assert (
        select_before_context(
            dict(schema=2, checklist=2, total=4, truncated=True), old, new
        )[0]
        is new
    )
    with pytest.raises(ValueError):
        select_before_context(
            dict(schema=3, checklist=3, total=6, truncated=True), old, new
        )
