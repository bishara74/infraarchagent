"""FR-S-03/07, FR-V-03, NFR-01: synthetic rerun refusal regressions."""

from pathlib import Path

import pytest

from app.agents.budget import AgentBudget
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.validation import ValidationCheck, ValidationReport
from app.scanners.scan import ScanResult
from app.security.acceptance import CandidateGuard
from app.security.partial import RetainedCandidate, accept_groups
from app.validation.documents import PackageDocuments
from app.validation.terraform import file_input_guard, terraform_skip

pytestmark = pytest.mark.req("FR-S-03", "FR-S-07", "FR-V-03", "NFR-01")


def files(kind="kms"):
    # Scenario 1 cost/security and scenario 3 performance, synthetic identities.
    target = (
        'resource "aws_kms_key" "backup_key" {\n description = "backup"\n}'
        if kind == "kms"
        else 'resource "aws_dynamodb_table" "table" {\n name = "synthetic"\n}'
    )
    return {
        "terraform/main.tf": target + '\nresource "aws_lambda_function" "backup" {\n'
        " source_code_hash = filebase64sha256(var.lambda_zip_path)\n}\n",
        "terraform/variables.tf": 'variable "lambda_zip_path" { type = string }\n',
    }


class Verifier:
    reason = "uninspectable_file_input"

    async def checks(self, source):
        checks = (
            file_input_guard(Path("/synthetic-package"), PackageDocuments.parse(source))
            if self.reason == "uninspectable_file_input"
            else [terraform_skip(self.reason)]
        )
        if "observed_failure" in str(source):
            checks.append(
                ValidationCheck(
                    check_id="terraform.validate",
                    category="terraform",
                    tool="terraform",
                    status="failed",
                    message="Unsupported argument",
                )
            )
        return checks


class Scanner:
    calls = 0

    async def scan(self, source, variant):
        self.calls += 1
        findings = [
            Violation(
                rule_id="TERRAFORM_FILE_INPUT",
                file_path="terraform/main.tf",
                resource="",
                message="File input refused",
                tool="terraform",
                blocking=True,
            )
        ]
        if "new_blocker" in str(source):
            findings.append(
                Violation(
                    rule_id="NEW",
                    file_path="terraform/main.tf",
                    resource="synthetic",
                    message="New blocker",
                    tool="trivy",
                    blocking=True,
                )
            )
        return ScanResult(findings, {"terraform": "file_input_blocked"})


def setup():
    verifier, scanner = Verifier(), Scanner()
    guard = CandidateGuard(
        verifier,
        scanner,
        Variant.SECURITY,
        AgentBudget(60),
        {"terraform_verification_seconds": 0.0, "security_verification_seconds": 0.0},
    )
    return guard


@pytest.mark.parametrize("kind", ["kms", "dynamodb"])
@pytest.mark.parametrize("partial", [False, True])
async def test_unchanged_refusal_keeps_independent_hardening_and_blocker(kind, partial):
    before = files(kind)
    field = (
        "enable_key_rotation = true"
        if kind == "kms"
        else "point_in_time_recovery { enabled = true }"
    )
    after = {
        **before,
        "terraform/main.tf": before["terraform/main.tf"].replace(
            ' name = "synthetic"' if kind == "dynamodb" else ' description = "backup"',
            " " + field,
        ),
    }
    guard = setup()
    checks = await guard.checks(before)
    scan = await guard.scanner.scan(before, Variant.SECURITY)
    if partial:
        records = []
        checkpoint = RetainedCandidate(before, scan)
        retained, checks, scanned = await accept_groups(
            guard, before, after, checks, scan, 6, records, checkpoint
        )
        assert retained == after
        assert records[0]["status"] == "kept"
    else:
        result = await guard.evaluate(before, after, checks, scan)
        assert result.reason is None
        checks, scanned = result.checks, result.scan
    assert scanned.violations[0].rule_id == "TERRAFORM_FILE_INPUT"
    assert (
        ValidationReport.build(checks, terraform_required=True).summary.result
        == "error"
    )
    assert guard.record["unchanged_terraform_unavailability"] == [
        "uninspectable_file_input"
    ]


@pytest.mark.parametrize(
    "change", ["expression", "dependency", "hidden_call", "provider", "module"]
)
async def test_changed_refusal_context_is_not_grandfathered(change):
    before = files()
    after = dict(before)
    if change == "expression":
        after["terraform/main.tf"] = before["terraform/main.tf"].replace(
            "var.lambda_zip_path", "var.other_path"
        )
        after["terraform/variables.tf"] += 'variable "other_path" {}\n'
    elif change == "dependency":
        after["terraform/variables.tf"] = (
            'variable "lambda_zip_path" { default = "different.zip" }\n'
        )
    elif change == "hidden_call":
        after["terraform/main.tf"] += (
            '\noutput "second" { value = file(var.lambda_zip_path) }\n'
        )
    elif change == "provider":
        after["terraform/provider.tf"] = 'provider "aws" { region = "us-east-2" }\n'
    else:
        after["terraform/child/main.tf"] = 'resource "aws_kms_key" "child" {}\n'
    guard = setup()
    result = await guard.evaluate(
        before,
        after,
        await guard.checks(before),
        await guard.scanner.scan(before, Variant.SECURITY),
    )
    assert result.reason == "terraform_verification_unavailable"


async def test_unchanged_refusal_ignores_line_shifts_and_unrelated_variable():
    before = files()
    after = {
        **before,
        "terraform/main.tf": "\n\n" + before["terraform/main.tf"],
        "terraform/unrelated.tf": 'variable "unrelated" { default = "unused" }\n',
    }
    guard = setup()
    result = await guard.evaluate(
        before,
        after,
        await guard.checks(before),
        await guard.scanner.scan(before, Variant.SECURITY),
    )
    assert result.reason is None


@pytest.mark.parametrize(
    "change,reason",
    [
        ("syntax", "invalid_syntax"),
        ("reference", "reference_regression"),
        ("scanner", "new_blocking_findings"),
        ("observed", "terraform_regression"),
    ],
)
async def test_other_gates_still_reject_with_unchanged_refusal(change, reason):
    before = files()
    after = dict(before)
    addition = {
        "syntax": '\nresource "aws_kms_key" "broken" {\n',
        "reference": '\noutput "bad" { value = var.missing }\n',
        "scanner": "\n# new_blocker\n",
        "observed": "\n# observed_failure\n",
    }[change]
    if change == "syntax":
        after["terraform/broken.tf"] = addition
    else:
        after["terraform/main.tf"] += addition
    guard = setup()
    result = await guard.evaluate(
        before,
        after,
        await guard.checks(before),
        await guard.scanner.scan(before, Variant.SECURITY),
    )
    assert result.reason == reason


@pytest.mark.parametrize("same", [False, True])
async def test_generic_unavailability_compares_cause(same):
    before = files()
    after = {
        **before,
        "terraform/main.tf": before["terraform/main.tf"] + "\n# hardening\n",
    }
    guard = setup()
    guard.verifier.reason = "mirror_missing"
    baseline = await guard.checks(before)
    if not same:
        guard.verifier.reason = "tool_error"
    result = await guard.evaluate(
        before, after, baseline, await guard.scanner.scan(before, Variant.SECURITY)
    )
    assert result.reason == (None if same else "terraform_verification_unavailable")


async def test_transitive_file_dependency_changes_are_rejected():
    before = files()
    before["terraform/main.tf"] = (
        before["terraform/main.tf"].replace("var.lambda_zip_path", "local.zip")
        + "\nlocals { zip = var.lambda_zip_path }\n"
    )
    after = {
        **before,
        "terraform/variables.tf": (
            'variable "lambda_zip_path" { default = "new.zip" }\n'
        ),
    }
    guard = setup()
    result = await guard.evaluate(
        before,
        after,
        await guard.checks(before),
        await guard.scanner.scan(before, Variant.SECURITY),
    )
    assert result.reason == "terraform_verification_unavailable"


async def test_unchanged_literal_refusal_remains_blocking_but_allows_hardening():
    before = files()
    before["terraform/main.tf"] = before["terraform/main.tf"].replace(
        "filebase64sha256(var.lambda_zip_path)",
        'filebase64sha256("/synthetic-outside")',
    )
    after = {
        **before,
        "terraform/main.tf": before["terraform/main.tf"].replace(
            ' description = "backup"', " enable_key_rotation = true"
        ),
    }
    guard = setup()
    result = await guard.evaluate(
        before,
        after,
        await guard.checks(before),
        await guard.scanner.scan(before, Variant.SECURITY),
    )
    assert result.reason is None
    assert any(
        c.check_id == "terraform.file_input" and c.status == "failed"
        for c in result.checks
    )
    assert result.scan.violations[0].rule_id == "TERRAFORM_FILE_INPUT"


@pytest.mark.parametrize("change", ["resource_dependency", "iteration_domain"])
async def test_file_input_resource_and_instance_context_changes_stay_closed(change):
    before = files()
    if change == "resource_dependency":
        before["terraform/main.tf"] = (
            before["terraform/main.tf"].replace(
                "var.lambda_zip_path", "random_id.archive.hex"
            )
            + '\nresource "random_id" "archive" { byte_length = 4 }\n'
        )
        after = {
            **before,
            "terraform/main.tf": before["terraform/main.tf"].replace(
                "byte_length = 4", "byte_length = 8"
            ),
        }
    else:
        before["terraform/main.tf"] = before["terraform/main.tf"].replace(
            'resource "aws_lambda_function" "backup" {',
            'resource "aws_lambda_function" "backup" {\n count = 1',
        )
        after = {
            **before,
            "terraform/main.tf": before["terraform/main.tf"].replace(
                "count = 1", "count = 2"
            ),
        }
    guard = setup()
    result = await guard.evaluate(
        before,
        after,
        await guard.checks(before),
        await guard.scanner.scan(before, Variant.SECURITY),
    )
    assert result.reason == "terraform_verification_unavailable"


async def test_changed_variable_used_by_input_iteration_domain_is_related():
    before = files()
    before["terraform/main.tf"] = before["terraform/main.tf"].replace(
        'resource "aws_lambda_function" "backup" {',
        'resource "aws_lambda_function" "backup" {\n count = var.replicas',
    )
    before["terraform/variables.tf"] += 'variable "replicas" { default = 1 }\n'
    after = {
        **before,
        "terraform/variables.tf": before["terraform/variables.tf"].replace(
            "default = 1", "default = 2"
        ),
    }
    guard = setup()
    result = await guard.evaluate(
        before,
        after,
        await guard.checks(before),
        await guard.scanner.scan(before, Variant.SECURITY),
    )
    assert result.reason == "terraform_verification_unavailable"


@pytest.mark.parametrize("kind", ["encryption", "logging"])
@pytest.mark.parametrize("partial", [False, True])
async def test_scenario1_s3_controls_survive_unchanged_lambda_refusal(kind, partial):
    before = files()
    before["terraform/main.tf"] += """
resource "aws_s3_bucket" "backup" {
  bucket = "synthetic-backups"
}
resource "aws_s3_bucket" "logs" {
  bucket = "synthetic-backup-logs"
}
"""
    if kind == "encryption":
        before["terraform/main.tf"] += """
resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
"""
        proposed = before["terraform/main.tf"].replace(
            'sse_algorithm = "AES256"',
            'sse_algorithm = "aws:kms"\n'
            "      kms_master_key_id = aws_kms_key.backup_key.arn",
        )
    else:
        proposed = (
            before["terraform/main.tf"]
            + """
resource "aws_s3_bucket_logging" "backup" {
  bucket = aws_s3_bucket.backup.id
  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "backups/"
}
"""
        )
    after = {**before, "terraform/main.tf": proposed}
    guard = setup()
    checks = await guard.checks(before)
    scan = await guard.scanner.scan(before, Variant.SECURITY)
    if partial:
        records = []
        retained, checks, scanned = await accept_groups(
            guard,
            before,
            after,
            checks,
            scan,
            6,
            records,
            RetainedCandidate(before, scan),
        )
        assert retained == after
        assert all(r["status"] == "kept" for r in records)
    else:
        result = await guard.evaluate(before, after, checks, scan)
        assert result.reason is None
        checks, scanned = result.checks, result.scan
    assert scanned.violations[0].rule_id == "TERRAFORM_FILE_INPUT"
    assert (
        ValidationReport.build(checks, terraform_required=True).summary.result
        == "error"
    )
