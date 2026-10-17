"""FR-S-03: real scanner-loop prompt path uses version-correct fixture schemas."""

import json
import re
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.agents.security.fix import FixAgent
from app.db.repositories.packages import PackageRepository
from app.db.session import make_session_factory
from app.domain.enums import PackageStatus, Variant
from app.scanners.scan import ScanResult
from tests.integration.test_security_agent import agent, finding, setup
from tests.unit.test_phase9e_iteration import checks
from tests.unit.test_schema_context import schemas as schemas

pytestmark = pytest.mark.req("FR-S-03", "FR-S-09", "FR-V-03", "NFR-01")


@pytest.mark.parametrize(
    "version,required_type", [("5.100.0", "string"), ("6.68.0", "number")]
)
async def test_scanner_loop_grounding_survives_rollback_and_reaches_retry(
    db_engines, schemas, monkeypatch, version, required_type
):
    from app.agents.security import fix as module

    original = module.schema_context
    monkeypatch.setattr(
        module,
        "schema_context",
        lambda *args, **kwargs: original(*args, **kwargs, directory=schemas),
    )
    engine, _ = db_engines
    ctx, package = await setup(engine, max_iterations=4)
    value = '"known"' if required_type == "string" else "1"
    main = 'resource "aws_widget" "main" {\n name = ' + value + "\n}\n"
    files = {
        "terraform/main.tf": main,
        "terraform/providers.tf": "terraform {\n required_providers {\n"
        ' aws = { source = "hashicorp/aws", version = "' + version + '" }\n }\n}\n',
    }
    package = package.model_copy(update={"files": files})
    async with make_session_factory(engine)() as session:
        async with session.begin():
            await PackageRepository(session).save_files(
                ctx.run_id, Variant.SECURITY, files
            )
    prompts = []

    async def complete(prompt, **kwargs):
        prompts.append(prompt)
        return SimpleNamespace(
            data={
                "file": {
                    "path": "terraform/main.tf",
                    "content": main + ("# bad\n" if len(prompts) == 1 else "# fixed\n"),
                }
            },
            response=SimpleNamespace(
                input_tokens=1, output_tokens=1, cached_input_tokens=None
            ),
        )

    adapter = SimpleNamespace(complete_json=AsyncMock(side_effect=complete))

    class Scanner:
        async def scan(self, files, *args, **kwargs):
            return ScanResult(
                []
                if "# fixed" in files["terraform/main.tf"]
                else [
                    finding("RULE").model_copy(update={"resource": "aws_widget.main"})
                ],
                {"terraform": "ok", "trivy": "ok", "checkov": "ok"},
            )

    class Verifier:
        async def checks(self, files):
            return checks(int("# bad" in files["terraform/main.tf"]))

    security = agent(
        engine, Scanner(), FixAgent(adapter, schema_context_max_chars=1500)
    )
    security.terraform_verifier = Verifier()
    assert (
        await security.run(ctx, Variant.SECURITY, package) == PackageStatus.SCAN_CLEAN
    )
    assert len(prompts) == 2
    for prompt in prompts:
        context = re.search(
            r"<provider_schema[^>]*>\n(.*?)\n</provider_schema", prompt, re.S
        )[1]
        entries = json.loads(context)
        assert len(context) <= 1500
        entry = next(e for e in entries if "schema" in e)
        assert entry["version"] == version
        assert entry["schema"]["required"]["name"] == required_type
    assert "<previous_attempt" not in prompts[0] and "<previous_attempt" in prompts[1]
    assert "terraform_regression" in prompts[1]
    async with make_session_factory(engine)() as session:
        row = await PackageRepository(session).get(ctx.run_id, Variant.SECURITY)
    fixes = [
        f for i in row.security_report["sessions"][0]["iterations"] for f in i["fixes"]
    ]
    assert all(f["schema_context_reason"] == "schema_available" for f in fixes)
    assert row.iteration_count == 2
