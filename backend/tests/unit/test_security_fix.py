"""FR-S-02/09: per-file prompts and atomic fix acceptance."""

import json

import pytest

from app.agents.prompts.security_fix import user_prompt
from app.agents.security.fix import FixAgent, validate_fix
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
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
        == "wrong_path"
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
