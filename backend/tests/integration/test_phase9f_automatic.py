"""FR-S-02/04: automatic changes and introduced template findings in stored reports."""

import json

import pytest

from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, Variant
from app.domain.models import IaCPackage
from app.scanners.scan import ScanResult
from tests.integration.test_security_agent import ScriptedFix, agent, finding, setup


async def prepare(engine, files):
    ctx, _ = await setup(engine, max_iterations=1)
    async with make_session_factory(engine)() as session:
        async with session.begin():
            await PackageRepository(session).save_files(
                ctx.run_id, Variant.SECURITY, files
            )
    return ctx, IaCPackage(variant=Variant.SECURITY, files=files)


@pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-04")
async def test_catalogue_retention_precedes_and_can_avoid_llm(db_engines):
    engine, _ = db_engines
    files = {
        "terraform/main.tf": 'resource "aws_db_instance" "db" { engine = "postgres" }'
    }
    ctx, package = await prepare(engine, files)

    class Scanner:
        async def scan(self, source, variant, **kwargs):
            return ScanResult(
                []
                if "deletion_protection = true" in source["terraform/main.tf"]
                else [finding("CKV_AWS_293")],
                {},
            )

    fixer = ScriptedFix()
    security = agent(engine, Scanner(), fixer)
    assert (
        await security.run(ctx, Variant.SECURITY, package) == PackageStatus.SCAN_CLEAN
    )
    assert not fixer.calls
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    record = row.security_report["sessions"][0]["iterations"][0]["verification"]
    assert record["catalogue"][0]["status"] == "retained"
    assert record["catalogue"][0]["rule_ids"] == ["CKV_AWS_293"]
    assert "deletion_protection = true" in row.files["terraform/main.tf"]


@pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-04", "NFR-01")
async def test_template_introduced_findings_remain_rejected_and_reported(db_engines):
    engine, _ = db_engines
    files = {"terraform/main.tf": 'resource "aws_s3_bucket" "source" {}'}
    ctx, package = await prepare(engine, files)
    original = finding("CKV_AWS_18").model_copy(
        update={"resource": "aws_s3_bucket.source"}
    )
    introduced = finding("CKV_AWS_145").model_copy(
        update={
            "resource": "aws_s3_bucket.infraarch_access_logs",
            "file_path": "terraform/security_support.tf.json",
        }
    )

    class Scanner:
        async def scan(self, source, variant, **kwargs):
            return ScanResult(
                [original, introduced]
                if "terraform/security_support.tf.json" in source
                else [original],
                {},
            )

    security = agent(engine, Scanner(), ScriptedFix())
    assert (
        await security.run(ctx, Variant.SECURITY, package)
        == PackageStatus.SCAN_EXHAUSTED
    )
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    record = row.security_report["sessions"][0]["iterations"][0]["verification"][
        "templates"
    ][0]
    assert (
        record["status"] == "rejected" and record["reason"] == "new_blocking_findings"
    )
    assert record["introduced_findings"][0]["rule_id"] == "CKV_AWS_145"
    assert "terraform/security_support.tf.json" not in row.files
    assert "aws_s3_bucket.source" in json.dumps(row.security_report)
