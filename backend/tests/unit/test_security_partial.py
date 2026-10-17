"""FR-S-03: independent good changes survive while every bad group is rejected."""

import asyncio
import json

import pytest

from app.agents.budget import AgentBudget
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.validation import ValidationCheck
from app.scanners.scan import ScanResult
from app.security.acceptance import CandidateGuard
from app.security.partial import RetainedCandidate, accept_groups, change_groups
from app.validation.documents import PackageDocuments, blocks


class Verifier:
    calls = 0

    async def checks(self, files):
        self.calls += 1
        bad = any(
            body.get("invalid")
            for d in PackageDocuments.parse(files).documents.values()
            for _, body in blocks(d.data, "resource")
        )
        return [
            ValidationCheck(
                check_id="terraform.validate",
                category="structure",
                tool="terraform",
                status="failed" if bad else "passed",
                message="synthetic regression",
            )
        ]


class Scanner:
    calls = 0

    async def scan(self, files, variant):
        self.calls += 1
        return ScanResult(
            [
                Violation(
                    rule_id="NEW",
                    resource="aws_s3_bucket.new",
                    file_path=p,
                    message="synthetic",
                    tool="trivy",
                    blocking=True,
                )
                for p, s in files.items()
                if "new_blocker" in s
            ],
            {},
        )


def setup(files, clock=None):
    record = {
        "terraform_verification_seconds": 0.0,
        "security_verification_seconds": 0.0,
    }
    budget = AgentBudget(60, clock=clock) if clock else AgentBudget(60)
    guard = CandidateGuard(Verifier(), Scanner(), Variant.SECURITY, budget, record)
    checkpoint = RetainedCandidate(files, ScanResult([], {}))
    return guard, checkpoint


@pytest.mark.req("FR-S-03", "FR-V-03")
@pytest.mark.parametrize("json_format", [False, True])
async def test_mixed_good_bad_blocks_keep_only_verified_changes(json_format):
    if json_format:
        files = {
            "terraform/main.tf.json": json.dumps(
                {"resource": {"aws_s3_bucket": {"a": {}, "b": {}, "c": {}}}}
            )
        }
        candidate = {
            "terraform/main.tf.json": json.dumps(
                {
                    "resource": {
                        "aws_s3_bucket": {
                            "a": {"secure": True},
                            "b": {"invalid": True},
                            "c": {"new_blocker": True},
                        }
                    }
                }
            )
        }
    else:
        files = {
            "terraform/main.tf": "\n".join(
                f'resource "aws_s3_bucket" "{n}" {{}}' for n in "abc"
            )
        }
        candidate = {
            "terraform/main.tf": """resource "aws_s3_bucket" "a" { secure = true }
resource "aws_s3_bucket" "b" { invalid = true }
resource "aws_s3_bucket" "c" { new_blocker = true }
"""
        }
    guard, checkpoint = setup(files)
    records = []
    result, _, scan = await accept_groups(
        guard,
        files,
        candidate,
        await guard.checks(files),
        checkpoint.scan,
        6,
        records,
        checkpoint,
    )
    assert [r["status"] for r in records] == ["kept", "discarded", "discarded"]
    assert [r["reason"] for r in records] == [
        "guards_passed",
        "terraform_regression",
        "new_blocking_findings",
    ]
    assert "secure" in next(iter(result.values()))
    assert "invalid" not in next(iter(result.values()))
    assert "new_blocker" not in next(iter(result.values()))
    assert result == checkpoint.files and not scan.violations


@pytest.mark.req("FR-S-03")
def test_changed_supporting_declarations_are_one_dependency_group():
    files = {"terraform/main.tf": 'resource "aws_s3_bucket" "target" {}'}
    candidate = {
        "terraform/main.tf": """resource "aws_s3_bucket" "target" {
  bucket = var.name
}
""",
        "terraform/variables.tf": 'variable "name" { type = string }',
    }
    groups = change_groups(files, candidate)
    assert len(groups) == 1 and len(groups[0]) == 2


@pytest.mark.req("FR-S-03", "PR-05")
async def test_group_limit_bounds_evaluations():
    files = {"terraform/main.tf": ""}
    candidate = {
        "terraform/main.tf": "\n".join(
            f'resource "aws_s3_bucket" "{n}" {{}}' for n in "abcd"
        )
    }
    guard, checkpoint = setup(files)
    records = []
    await accept_groups(
        guard, files, candidate, [], checkpoint.scan, 1, records, checkpoint
    )
    assert [r["status"] for r in records] == ["kept", *["unevaluated"] * 3]
    assert guard.scanner.calls == 1
    assert all(r["reason"] == "group_limit" for r in records[1:])


@pytest.mark.req("FR-S-03", "PR-05")
async def test_budget_expiry_preserves_only_previously_verified_groups():
    now = [0.0]
    files = {"terraform/main.tf": ""}
    candidate = {
        "terraform/main.tf": "\n".join(
            f'resource "aws_s3_bucket" "{n}" {{}}' for n in "abc"
        )
    }
    guard, checkpoint = setup(files, lambda: now[0])
    original = guard.scanner.scan

    async def expiring(source, variant):
        scan = await original(source, variant)
        now[0] += 31
        return scan

    guard.scanner.scan = expiring
    records = []
    retained, _, _ = await accept_groups(
        guard, files, candidate, [], checkpoint.scan, 6, records, checkpoint
    )
    assert records[0]["status"] == "kept"
    assert all(r["status"] == "unevaluated" for r in records[1:])
    assert (
        '"a"' in retained["terraform/main.tf"]
        and '"b"' not in retained["terraform/main.tf"]
    )


@pytest.mark.req("FR-S-03", "PR-05")
async def test_cancellation_keeps_verified_checkpoint():
    files = {"terraform/main.tf": ""}
    candidate = {
        "terraform/main.tf": "\n".join(
            f'resource "aws_s3_bucket" "{n}" {{}}' for n in "ab"
        )
    }
    guard, checkpoint = setup(files)
    checkpoint.fixes = [
        {
            "file": "terraform/main.tf",
            "accepted": True,
            "normalized_existing_paths": ["terraform/main.tf"],
        }
    ]
    original = guard.scanner.scan

    async def cancelled(source, variant):
        if '"b"' in source["terraform/main.tf"]:
            raise asyncio.CancelledError
        return await original(source, variant)

    guard.scanner.scan = cancelled
    with pytest.raises(asyncio.CancelledError):
        await accept_groups(
            guard, files, candidate, [], checkpoint.scan, 6, [], checkpoint
        )
    assert '"a"' in checkpoint.files["terraform/main.tf"]
    assert '"b"' not in checkpoint.files["terraform/main.tf"]
    assert checkpoint.fixes[0]["retained"]
    assert checkpoint.fixes[0]["recovered_existing_proposal"]


@pytest.mark.req("FR-S-03", "FR-V-03")
def test_changed_provider_configuration_stays_with_module_changes():
    files = {
        "terraform/main.tf": """terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "5.100.0" } }
}
resource "aws_s3_bucket" "target" {}
"""
    }
    candidate = {
        "terraform/main.tf": files["terraform/main.tf"]
        .replace("5.100.0", "6.68.0")
        .replace('"target" {}', '"target" { bucket_prefix = "secure-" }')
    }
    groups = change_groups(files, candidate)
    assert len(groups) == 1 and len(groups[0]) == 2


@pytest.mark.req("FR-S-03")
async def test_control_removal_cannot_be_partially_retained():
    files = {"terraform/main.tf": 'resource "aws_s3_bucket" "a" { encrypted = true }'}
    candidate = {
        "terraform/main.tf": """resource "aws_s3_bucket" "a" {}
resource "aws_s3_bucket" "b" {}
"""
    }
    guard, checkpoint = setup(files)
    records = []
    result, _, _ = await accept_groups(
        guard, files, candidate, [], checkpoint.scan, 6, records, checkpoint
    )
    assert records[0]["reason"] == "security_control_removed"
    assert "encrypted = true" in result["terraform/main.tf"]
    assert records[1]["status"] == "kept"
