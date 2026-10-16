"""FR-V-03/PR-05: bounded iteration clocks and isolated reusable workspaces."""

import asyncio

import pytest

from app.agents.budget import AgentBudget
from app.domain.enums import Variant
from app.domain.validation import RemediationReport
from app.scanners.runner import ToolResult
from app.validation.documents import PackageDocuments
from app.validation.gate import GenerationGate
from app.validation.terraform import init_failure_category
from app.validation.workspace import ValidationWorkspace
from scripts.phase9e_metrics import measurement_summary
from tests.unit.test_phase9e_gate import Runner, engine, plan
from tests.unit.test_phase9e_iteration import setup
from tests.unit.test_validation_repair import setup as repair_setup

pytestmark = pytest.mark.req("FR-V-03", "FR-S-09", "PR-05", "NFR-01")


@pytest.mark.parametrize(
    "category,text,source",
    [
        ("missing_required_providers", "", 'resource "aws_vpc" "x" {}'),
        (
            "invalid_required_providers",
            "Invalid provider source",
            "terraform { required_providers { aws = {} } }",
        ),
        (
            "mirror_constraint_unavailable",
            "Failed to query available provider packages",
            'terraform { required_providers { aws = { source = "hashicorp/aws" '
            'version = "999.0" } } }',
        ),
        (
            "syntax",
            "Error: Invalid expression",
            'terraform { required_providers { aws = { source = "hashicorp/aws" '
            'version = "5.100.0" } } }',
        ),
    ],
)
def test_init_categories_are_safe(category, text, source):
    docs = PackageDocuments.parse({"terraform/main.tf": source})
    assert init_failure_category(text + " DO-NOT-EXPORT", docs, "terraform") == category


async def test_private_concurrent_workspaces_and_cancelled_waiter_cleanup(tmp_path):
    entered = asyncio.Event()
    release = asyncio.Event()
    active = set()

    class Blocking(Runner):
        async def run_command(self, tool, args, root, **kwargs):
            if args[1] == "init":
                active.add(str(root))
                if len(active) == 2:
                    entered.set()
                await release.wait()
            return await super().run_command(tool, args, root, **kwargs)

    runner = Blocking()
    validator = engine(tmp_path, runner)
    workspaces = [ValidationWorkspace(), ValidationWorkspace()]
    files = {"terraform/main.tf": 'resource "aws_vpc" "x" {}\n'}

    async def check(workspace):
        with workspace.activate():
            return await validator.validate(plan(), files)

    tasks = [asyncio.create_task(check(w)) for w in workspaces]
    try:
        await asyncio.wait_for(entered.wait(), 2)
        assert len(active) == 2
        waiter = asyncio.create_task(check(workspaces[0]))
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter
        release.set()
        await asyncio.gather(*tasks)
        environments = {str(kw["environment_dir"]) for _, _, _, kw in runner.calls}
        assert len(environments) == 2
    finally:
        release.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        for workspace in workspaces:
            workspace.close()
    assert not any(w.root.exists() for w in workspaces)


async def test_dependency_rollback_reinitializes_and_local_module_graph_invalidates(
    tmp_path,
):
    runner = Runner()
    validator = engine(tmp_path, runner)
    workspace = ValidationWorkspace()
    files = {"terraform/main.tf": 'resource "aws_vpc" "main" {}\n'}
    changed = {
        **files,
        "terraform/providers.tf": "terraform { required_providers { aws = { "
        'source = "hashicorp/aws" version = "6.68.0" } } }\n',
    }
    try:
        with workspace.activate():
            await validator.validate(plan(), files)
            await validator.validate(plan(), changed)
            await validator.validate(plan(), files)
            assert sum(args[1] == "init" for _, args, _, _ in runner.calls) == 3
            local = {
                **files,
                "terraform/module.tf": 'module "local" { source = "./child" }\n',
                "terraform/child/main.tf": 'resource "aws_vpc" "child" {}\n',
            }
            await validator.validate(plan(), local)
            assert sum(args[1] == "init" for _, args, _, _ in runner.calls) == 5
    finally:
        workspace.close()


async def test_gate_records_all_installed_tool_checks_and_renders_helm_json(tmp_path):
    class Tools(Runner):
        async def run_command(self, tool, args, root, **kwargs):
            if tool != "terraform":
                self.calls.append((tool, args, root, kwargs))
                return ToolResult(
                    '{"apiVersion":"v1","kind":"ConfigMap"}\n'
                    if tool == "helm" and args[1] == "template"
                    else "",
                    "",
                    0,
                    0,
                )
            return await super().run_command(tool, args, root, **kwargs)

    runner = Tools()
    files = {
        "terraform/main.tf": 'resource "aws_vpc" "main" {}\n',
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 0.1.0\n",
        "helm/app/values.yaml": "name: app\n",
        "helm/app/templates/config.json": '{"name": {{ .Values.name | quote }} }\n',
        "ansible/playbook.yaml": "- hosts: localhost\n  tasks: []\n",
        "monitoring/prometheus/rules.yaml": "groups: []\n",
    }
    result = await GenerationGate(engine(tmp_path, runner)).run(plan(), files)
    assert not any(c.check_id == "document.parse" for c in result.report.checks)
    assert any(
        tool == "helm" and args[1] == "template" for tool, args, _, _ in runner.calls
    )
    assert any(tool == "ansible-playbook" for tool, _, _, _ in runner.calls)
    assert any(
        tool == "promtool" and args[1:3] == ["check", "rules"]
        for tool, args, _, _ in runner.calls
    )


@pytest.mark.parametrize("moment", ["baseline", "fix", "regression"])
async def test_injected_clock_iteration_deadline_causes(moment):
    files, ctx, security, baseline, _, verifier = setup((0, 1))
    now = [0.0]
    budget = AgentBudget(60, clock=lambda: now[0])
    if moment == "fix":
        original = security.fix_agent.propose

        async def propose(**kwargs):
            result = await original(**kwargs)
            now[0] = 61
            return result

        security.fix_agent.propose = propose
    else:
        original = verifier.checks

        async def check(source):
            result = await original(source)
            if moment == "baseline" or len(verifier.inputs) == 2:
                now[0] = 61
            return result

        verifier.checks = check
    record = {}
    with pytest.raises(TimeoutError):
        await security._fix_iteration(
            ctx,
            Variant.SECURITY,
            files,
            {"terraform/main.tf": []},
            budget,
            baseline,
            record,
            feedback=None,
            validation_failures=[],
        )
    record["deadline_only"] = bool(
        record.get("candidate_created") and not record["reasons"]
    )
    record["reasons"].append("iteration_deadline")
    record.update(
        stage="security_iteration_verification", phase="security", duration_seconds=0
    )
    counts = measurement_summary([record])[0]["iterations"]
    assert counts["deadline_before_candidate"] == (moment == "baseline")
    assert counts["deadline_only_rollbacks"] == (moment == "fix")
    assert counts["multiple_cause_deadline_rollbacks"] == (moment == "regression")
    assert files["terraform/main.tf"].endswith("original = true }\n")


async def test_independent_repair_budgets_after_long_security_stage():
    now = [0.0]
    initial = AgentBudget(120, clock=lambda: now[0])
    repair, ctx, package = repair_setup([1, 0])
    now[0] = 230  # Security elapsed time cannot consume a newly created budget.
    post = AgentBudget(60, clock=lambda: now[0])
    fixed, _, metadata = await repair.run(
        ctx,
        Variant.COST,
        package,
        rounds=1,
        budget=post,
        phase="after_security",
        metadata=RemediationReport(),
    )
    assert initial.expired() and post.remaining() == 60
    assert fixed.files != package.files and metadata.rounds[0].outcome == "accepted"


async def test_cancelled_initialization_is_never_reused(tmp_path):
    entered = asyncio.Event()

    class Cancelled(Runner):
        async def run_command(self, tool, args, root, **kwargs):
            if args[1] == "init":
                entered.set()
                await asyncio.Event().wait()
            return await super().run_command(tool, args, root, **kwargs)

    workspace = ValidationWorkspace()
    validator = engine(tmp_path, Cancelled())
    files = {"terraform/main.tf": 'resource "aws_vpc" "x" {}\n'}

    async def check():
        with workspace.activate():
            await validator.validate(plan(), files)

    task = asyncio.create_task(check())
    try:
        await asyncio.wait_for(entered.wait(), 2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not workspace.initialized
        runner = Runner()
        validator.runner = runner
        with workspace.activate():
            await validator.validate(plan(), files)
        assert sum(args[1] == "init" for _, args, _, _ in runner.calls) == 1
        assert workspace.terraform_metrics[0]["init_seconds"] > 0
    finally:
        workspace.close()


async def test_helm_patch_rejects_touched_failure_and_retains_unrelated_failure(
    monkeypatch,
):
    from app.domain.validation import ValidationCheck
    from app.validation.gate import patch_syntax_failure

    before = {
        "helm/app/Chart.yaml": "name: app\n",
        "helm/app/templates/old.yaml": "{{ old }}",
        "helm/app/templates/new.yaml": "{{ new }}",
    }
    candidate = {**before, "helm/app/templates/new.yaml": "{{ changed }}"}
    location = ["helm/app/templates/new.yaml"]

    async def extra(self, files, **kwargs):
        return (
            files,
            [
                ValidationCheck(
                    check_id="gate.helm",
                    category="lint",
                    tool="helm",
                    status="failed",
                    message="Helm template failed",
                    file_path=location[0],
                )
            ],
            [],
        )

    monkeypatch.setattr(GenerationGate, "extra_checks", extra)
    assert await patch_syntax_failure(
        before, candidate, {"helm/app/templates/new.yaml"}
    )
    location[0] = "helm/app/templates/old.yaml"
    assert not await patch_syntax_failure(
        before, candidate, {"helm/app/templates/new.yaml"}
    )
