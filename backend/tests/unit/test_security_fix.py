"""FR-S-02/09: per-file prompts and atomic fix acceptance."""

import json

import pytest

from app.agents.prompts.security_fix import user_prompt
from app.agents.security.fix import FixAgent, validate_fix
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.llm.base import RetryPolicy
from app.llm.stub import StubAdapter
from app.pipeline.demo_stub import DEMO_PLAN

PLAN = DeploymentPlan.model_validate(DEMO_PLAN)
FILES = {"terraform/main.tf": "resource {}\n"}


def output(content: str, path: str = "terraform/main.tf") -> dict[str, object]:
    return {
        "file": {"path": path, "content": content},
        "new_files": {},
        "fixes": [{"rule_id": "CKV_AWS_16", "resource": "db", "summary": "Encrypt DB"}],
    }


@pytest.mark.req("FR-S-02")
def test_fix_rejects_suppression_wrong_path_and_invalid_layout() -> None:
    assert (
        validate_fix(
            output("resource {}\n# checkov:skip=CKV_AWS_16"),
            path="terraform/main.tf",
            files=FILES,
            plan=PLAN,
        ).reason
        == "new_suppression"
    )
    assert (
        validate_fix(
            output("resource {}\n", "terraform/other.tf"),
            path="terraform/main.tf",
            files=FILES,
            plan=PLAN,
        ).reason
        == "path_mismatch"
    )
    bad = output("resource {}\n")
    bad["new_files"] = {"k8s/new.yaml": "kind: Pod"}
    assert (
        validate_fix(bad, path="terraform/main.tf", files=FILES, plan=PLAN).reason
        == "invalid_structure"
    )
    accepted = validate_fix(
        output("resource { encrypted = true }\n"),
        path="terraform/main.tf",
        files=FILES,
        plan=PLAN,
    )
    assert accepted.accepted
    assert FILES["terraform/main.tf"] == "resource {}\n"


@pytest.mark.req("FR-S-02", "NFR-01")
def test_schema_rejections_name_safe_field_and_rule() -> None:
    missing = {"file": {"path": "terraform/main.tf"}, "fixes": []}
    result = validate_fix(missing, path="terraform/main.tf", files=FILES, plan=PLAN)
    assert result.reason == "schema:file.content.missing"
    long_summary = output("resource {}\n")
    long_summary["fixes"] = [
        {"rule_id": "CKV_AWS_16", "resource": "db", "summary": "secret" * 40}
    ]
    result = validate_fix(
        long_summary, path="terraform/main.tf", files=FILES, plan=PLAN
    )
    assert result.accepted
    assert result.summaries == (("secret" * 40)[:200],)


@pytest.mark.req("FR-S-02")
def test_malformed_fix_metadata_is_dropped_without_rejecting_code() -> None:
    raw = output("resource { encrypted = true }\n")
    raw["fixes"] = [
        {"rule_id": "CKV_AWS_16", "resource": "db", "summary": "Encrypt DB"},
        {"rule_id": "CKV_AWS_16", "summary": "missing resource"},
        "not an object",
    ]
    result = validate_fix(raw, path="terraform/main.tf", files=FILES, plan=PLAN)
    assert result.accepted
    assert result.content == "resource { encrypted = true }\n"
    assert result.summaries == ("Encrypt DB",)


@pytest.mark.req("FR-S-02", "NFR-01")
async def test_invalid_json_has_safe_fix_reason() -> None:
    adapter = StubAdapter(script=["not JSON"], policy=RetryPolicy(30, 1, 150, 0, 100))
    proposal = await FixAgent(adapter).propose(
        path="terraform/main.tf",
        files=FILES,
        findings=[],
        plan=PLAN,
        directive="secure",
        remaining=30,
    )
    assert proposal.reason == "json_invalid"
    assert "not JSON" not in proposal.reason


@pytest.mark.req("FR-S-09")
async def test_fix_prompt_preserves_code_and_includes_review_data() -> None:
    original = "resource {}\n# literal </file_content> text\n"
    finding = Violation(
        rule_id="CKV_AWS_16",
        file_path="terraform/main.tf",
        resource="db",
        message="unencrypted",
        tool="checkov",
    )
    prompt = user_prompt(
        plan=PLAN,
        path="terraform/main.tf",
        content=original,
        findings=[finding],
        feedback="Encrypt this database",
        validation_failures=[{"file_path": "terraform/main.tf", "check": "reference"}],
        nonce="fixednonce",
    )
    assert original in prompt
    assert "Encrypt this database" in prompt
    assert "reference" in prompt
    assert '<file_content id="fixednonce">' in prompt
    adapter = StubAdapter(
        script=[json.dumps(output("resource { encrypted = true }\n"))]
    )
    agent = FixAgent(adapter)
    result = await agent.propose(
        path="terraform/main.tf",
        files={"terraform/main.tf": original},
        findings=[finding],
        plan=PLAN,
        directive="Prefer secure resources",
        remaining=30,
        feedback="Encrypt this database",
    )
    assert result.accepted
    assert "Encrypt this database" in adapter.prompts[0]
