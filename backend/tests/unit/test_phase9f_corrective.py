"""FR-G-02/FR-S-03/FR-V-03/PR-05: corrective generation and acceptance."""

import json
from copy import deepcopy

import pytest

from app.agents.budget import AgentBudget
from app.agents.generation_syntax import recover_generation_syntax
from app.agents.security.fix import FixProposal
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationCheck
from app.llm.base import LLMResponse
from app.pipeline.demo_stub import DEMO_PLAN
from app.validation.syntax import native_syntax, normalize_blocks
from app.validation.workspace import ValidationWorkspace
from tests.unit.test_generators import FakeClock, agent, reply

pytestmark = pytest.mark.req("FR-G-02", "FR-S-03", "FR-V-03", "PR-05")


def plan():
    data = deepcopy(DEMO_PLAN)
    data["file_types"] = ["terraform"]
    return DeploymentPlan.model_validate(data)


@pytest.mark.parametrize(
    "value",
    [
        "0",
        "var.port",
        "[for p in var.ports : p if p > 0]",
        '{one = "a b", two = "c"}',
        'var.flag ? "yes" : "no"',
    ],
)
async def test_normalization_is_idempotent_and_preserves_expressions(value):
    source = f'locals {{ first = {value} second = "unchanged string" }}\n'
    files = {"terraform/main.tf": source, "README.md": source}
    result, records = normalize_blocks(files)
    assert records and records[0]["before_hash"] != records[0]["after_hash"]
    assert value in result["terraform/main.tf"]
    assert result["README.md"] == source
    assert normalize_blocks(result) == (result, [])
    assert not await native_syntax(result)


@pytest.mark.parametrize(
    "source",
    [
        'locals { one = "missing two = 2 }',
        "locals { one = 1; two = 2 }",
        "locals { one = 1 # comment two = 2 }",
        "locals {\n one = <<EOF\na b\nEOF\n two = 2\n}\n",
    ],
)
def test_ambiguous_and_multiline_input_untouched(source):
    files = {"terraform/main.tf": source}
    assert normalize_blocks(files) == (files, [])


async def test_native_gate_detects_python_parser_false_positives():
    for source in ["locals { a = 1 b = 2 }", 'locals {\n a = "first\nsecond"\n}']:
        assert await native_syntax({"terraform/main.tf": source})


async def test_syntax_cache_reuses_content_and_invalidates_changes():
    class Runner:
        calls = 0

        async def run_command(self, *args, **kwargs):
            from app.scanners.runner import ToolResult

            self.calls += 1
            return ToolResult("", "", 0, 0)

    runner = Runner()
    workspace = ValidationWorkspace()
    try:
        with workspace.activate():
            files = {"terraform/main.tf": "locals { a = 1 }"}
            await native_syntax(files, runner=runner)
            await native_syntax(files, runner=runner)
            await native_syntax(
                {"terraform/main.tf": "locals { a = 2 }"}, runner=runner
            )
        assert runner.calls == 2
    finally:
        workspace.close()


async def test_second_syntax_round_after_rejection_and_no_regeneration():
    class Fixer:
        calls = []

        async def propose(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return FixProposal(
                    kwargs["path"], False, "invalid_syntax", None, {}, ()
                )
            return FixProposal(
                kwargs["path"], True, None, 'locals { a = "fixed" }\n', {}, ()
            )

    async def regenerate(feedback):
        pytest.fail("valid repair must not regenerate")

    files = {"terraform/main.tf": 'locals { a = "missing }'}
    fixer = Fixer()
    result, report = await recover_generation_syntax(
        files, plan(), fixer, AgentBudget(20), redact=lambda x: x, regenerate=regenerate
    )
    assert report["path"] == "syntax_round_2"
    assert len(fixer.calls) == 2
    assert fixer.calls[0]["validation_failures"][0]["excerpt"]
    assert not await native_syntax(result)


async def test_regeneration_once_after_two_failed_rounds():
    class Fixer:
        calls = 0

        async def propose(self, **kwargs):
            self.calls += 1
            return FixProposal(kwargs["path"], False, "invalid_syntax", None, {}, ())

    replacements = []

    async def regenerate(feedback):
        replacements.append(feedback)
        return {"terraform/main.tf": 'locals { a = "replacement" }\n'}

    fixer = Fixer()
    _, report = await recover_generation_syntax(
        {"terraform/main.tf": 'locals { a = "missing }'},
        plan(),
        fixer,
        AgentBudget(20),
        redact=lambda x: x,
        regenerate=regenerate,
    )
    assert fixer.calls == 2 and len(replacements) == 1
    assert report["path"] == "regeneration"


def test_provenance_deduplicates_and_tracks_shifted_lines():
    workspace = ValidationWorkspace()
    try:
        check = ValidationCheck(
            check_id="document.parse",
            category="structure",
            tool="builtin",
            status="failed",
            file_path="monitoring/grafana/x.json",
            line_start=1,
            message="Document could not be parsed",
        )
        files = {check.file_path: "{bad json}"}
        workspace.observe([check, check], "generated", files)
        assert workspace.annotate((check,))[0].origin == "generated"
        moved = check.model_copy(update={"line_start": 2})
        workspace.observe([moved], "security_fix", {check.file_path: "\n{bad json}"})
        assert workspace.annotate((moved,))[0].origin == "generated"
    finally:
        workspace.close()


async def test_generation_deadline_skips_repairs_and_regeneration():
    class Fixer:
        async def propose(self, **kwargs):
            pytest.fail("expired budget must not call a model")

    async def regenerate(feedback):
        pytest.fail("expired budget must not regenerate")

    budget = AgentBudget(0.1)
    _, report = await recover_generation_syntax(
        {"terraform/main.tf": 'locals { a = "missing }'},
        plan(),
        Fixer(),
        budget,
        redact=lambda x: x,
        regenerate=regenerate,
    )
    assert report["regeneration"] == "deadline"
    assert not report["rounds"]


async def test_scope_change_rejected_then_regeneration():
    class Fixer:
        async def propose(self, **kwargs):
            return FixProposal(
                kwargs["path"],
                True,
                None,
                'resource "aws_kms_key" "renamed" {}',
                {},
                (),
            )

    async def regenerate(feedback):
        return {"terraform/main.tf": 'resource "aws_kms_key" "original" {}'}

    _, report = await recover_generation_syntax(
        {
            "terraform/main.tf": 'resource "aws_kms_key" "original" { '
            'description = "missing }'
        },
        plan(),
        Fixer(),
        AgentBudget(20),
        redact=lambda x: x,
        regenerate=regenerate,
    )
    assert report["path"] == "regeneration"
    assert all(
        r["actions"][0]["reason"] == "syntax_scope_or_control_changed"
        for r in report["rounds"]
    )


@pytest.mark.parametrize(
    "path,source",
    [
        ("monitoring/grafana/x.json", '{"expr":"image!="""}'),
        ("k8s/x.yaml", "kind: [unterminated"),
        ("terraform/main.tf.json", '{"locals":{"x":"${unclosed"}}'),
    ],
)
async def test_json_yaml_and_tf_json_native_diagnostics(path, source):
    issues = await native_syntax({path: source})
    assert issues and issues[0].line >= 1


async def test_syntax_excerpts_are_redacted_and_not_persisted():
    class Fixer:
        calls = []

        async def propose(self, **kwargs):
            self.calls.append(kwargs)
            return FixProposal(
                kwargs["path"], True, None, 'locals { a = "safe" }', {}, ()
            )

    async def regenerate(feedback):
        pytest.fail("repair passes")

    fixer = Fixer()
    _, report = await recover_generation_syntax(
        {"terraform/main.tf": 'locals { a = "SECRET_CANARY }'},
        plan(),
        fixer,
        AgentBudget(20),
        redact=lambda x: json.loads(
            json.dumps(x).replace("SECRET_CANARY", "[REDACTED]")
        ),
        regenerate=regenerate,
    )
    assert "SECRET_CANARY" not in json.dumps(fixer.calls, default=str)
    assert "SECRET_CANARY" not in json.dumps(report)
    assert "excerpt" not in json.dumps(report)


async def test_regeneration_shares_deadline_and_aggregates_original_model_usage(
    monkeypatch,
):
    clock = FakeClock()
    generator = agent(
        LLMResponse(reply({"terraform/main.tf": "terraform {}"}), 5, 9),
        LLMResponse(reply({"terraform/main.tf": "terraform {}"}), 7, 11),
        clock=clock,
    )
    budget = AgentBudget(150, clock=clock.now)
    await generator.generate(plan(), budget=budget)
    clock.now_value = 100
    original = generator.llm_adapter.send_prompt
    received = []

    async def send(prompt, **kwargs):
        received.append(kwargs)
        clock.now_value += 10
        return await original(prompt, **kwargs)

    monkeypatch.setattr(generator.llm_adapter, "send_prompt", send)
    await generator.regenerate(
        plan(), [{"message": "Unterminated template string"}], budget
    )
    assert received[0]["timeout"] <= 50
    assert received[0]["max_output_tokens"] == 32000
    assert budget.remaining() == 40
    assert generator.last_run.package_attempts == 2
    assert generator.last_run.total_llm_attempts == 2
    assert generator.last_run.input_tokens == 12
    assert generator.last_run.output_tokens == 20
    assert generator.last_run.elapsed_seconds == 110
    assert "Unterminated template string" in generator.llm_adapter.prompts[-1]


def test_syntax_only_scope_preserves_unrelated_tokens_and_control_values():
    from app.agents.generation_syntax import preserves_intent, syntax_edit_scope

    before = 'locals { a = "keep spaces" }\n' + "\n" * 8 + 'locals { b = "missing }'
    assert syntax_edit_scope(before, before.replace("missing }", 'missing" }'), [10])
    assert not syntax_edit_scope(
        before, before.replace("keep spaces", "keepspaces"), [10]
    )
    assert not preserves_intent("encrypted = true", "encrypted = false")
    assert not preserves_intent('"encrypted":true', '"encrypted":false')
