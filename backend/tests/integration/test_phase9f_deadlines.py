"""PR-05/FR-S-03: a template timeout retains the verified catalogue checkpoint."""

from dataclasses import replace

import pytest

from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, Variant
from app.scanners.scan import ScanResult
from app.security.acceptance import CandidateGuard
from tests.integration.test_phase9f_automatic import prepare
from tests.integration.test_security_agent import ScriptedFix, agent, finding


@pytest.mark.req("PR-05", "FR-S-03", "FR-S-04")
async def test_template_deadline_finalizes_record_and_keeps_catalogue(
    db_engines, monkeypatch
):
    engine, _ = db_engines
    files = {
        "terraform/main.tf": """resource "aws_lb_listener" "https" {
  protocol = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-2016-08"
}
resource "aws_s3_bucket" "source" { bucket = "application-storage" }
"""
    }
    ctx, package = await prepare(engine, files)
    now = [0.0]
    ctx = replace(ctx, clock=lambda: now[0])
    kms = finding("CKV_AWS_145").model_copy(update={"resource": "aws_s3_bucket.source"})
    tls = finding("CKV_AWS_103").model_copy(
        update={"resource": "aws_lb_listener.https"}
    )

    class Scanner:
        async def scan(self, files, variant, **kwargs):
            return ScanResult(
                [kms] + ([] if "TLS13" in files["terraform/main.tf"] else [tls]), {}
            )

    evaluate = CandidateGuard.evaluate

    async def template_timeout(self, before, candidate, checks, scan, **kwargs):
        if "terraform/security_support.tf" in candidate:
            now[0] = 56
            raise TimeoutError
        return await evaluate(self, before, candidate, checks, scan, **kwargs)

    monkeypatch.setattr(CandidateGuard, "evaluate", template_timeout)
    fixer = ScriptedFix()
    result = await agent(engine, Scanner(), fixer).run(ctx, Variant.SECURITY, package)
    assert result == PackageStatus.SCAN_EXHAUSTED and not fixer.calls
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    verification = row.security_report["sessions"][0]["iterations"][0]["verification"]
    assert verification["catalogue"][0]["status"] == "retained"
    assert verification["templates"][0]["status"] == "rejected"
    assert verification["templates"][0]["reason"] == "iteration_deadline"
    assert "TLS13" in row.files["terraform/main.tf"]
    assert "terraform/security_support.tf" not in row.files
    assert now[0] < 60
