"""FR-G-02/FR-V-03/FR-S-04/PR-05: A2 corrective regressions."""

import asyncio
import json
import time
from unittest.mock import AsyncMock

import pytest

from app.agents.generators.base import (
    GeneratorDeadlineExceeded,
    GeneratorIncompletePackage,
)
from app.core.deadlines import active_deadline, bounded_phase, iteration_window
from app.domain.package_layout import completeness_diagnostics
from app.domain.plan import FileType
from app.domain.validation import ValidationCheck
from app.scanners.runner import ProcessToolRunner
from app.validation.documents import PackageDocuments
from app.validation.references import reference_checks
from app.validation.repairs import repair_declarations
from app.validation.workspace import ValidationWorkspace
from scripts.phase9c_metrics import completeness_details
from scripts.phase9f_workloads import pr05_workloads
from tests.unit.test_generators import FakeClock, agent, plan, reply

pytestmark = pytest.mark.req("FR-G-02", "FR-V-03", "FR-S-04", "PR-05", "NFR-01")


async def test_third_package_attempt_and_explicit_missing_path_feedback():
    bad = {
        "terraform/main.tf": "PRIVATE_CONTENT",
        **{f"bad{i}.txt": "x" for i in range(12)},
    }
    good = {
        "terraform/main.tf": "terraform {}",
        "docker/web/Dockerfile": "FROM scratch",
    }
    generator = agent(reply(bad), reply(bad), reply(good))
    generator.max_package_attempts = 3
    assert (await generator.generate(plan("dockerfile"))).files == good
    for prompt in generator.llm_adapter.prompts[1:]:
        assert '"suggested_path": "docker/web/Dockerfile"' in prompt
        assert '"missing_types": ["dockerfile"]' in prompt
        assert "PRIVATE_CONTENT" not in prompt
    assert generator.last_run.package_attempts == 3
    assert [r["error_count"] for r in generator.last_run.completeness] == [13, 13, 0]
    assert "PRIVATE_CONTENT" not in repr(generator.last_run)


async def test_two_attempt_override_and_three_attempt_exhaustion():
    for limit in (2, 3):
        generator = agent(*[reply({"terraform/main.tf": "terraform {}"})] * limit)
        generator.max_package_attempts = limit
        with pytest.raises(GeneratorIncompletePackage):
            await generator.generate(plan("dockerfile"))
        assert len(generator.llm_adapter.prompts) == limit
        assert len(generator.last_run.completeness) == limit


async def test_three_attempt_limit_does_not_reset_shared_generator_deadline(
    monkeypatch,
):
    clock = FakeClock()
    incomplete = reply({"terraform/main.tf": "terraform {}"})
    generator = agent(incomplete, incomplete, incomplete, clock=clock)
    generator.max_package_attempts = 3
    original = generator.llm_adapter.send_prompt

    async def send(*args, **kwargs):
        result = await original(*args, **kwargs)
        clock.now_value += 75
        return result

    monkeypatch.setattr(generator.llm_adapter, "send_prompt", send)
    with pytest.raises(GeneratorDeadlineExceeded):
        await generator.generate(plan("dockerfile"))
    assert len(generator.llm_adapter.prompts) == 2


def test_completeness_alternative_path_and_source_free_projection():
    files = {
        "terraform/other.tf": "PRIVATE_CANARY",
        "docker/nested/Dockerfile": "FROM scratch",
    }
    details = completeness_diagnostics(
        files, [FileType.TERRAFORM, FileType.DOCKERFILE], "web"
    )
    assert details["missing_paths"] == []
    assert details["error_count"] == 0
    details.update(attempt=1, source="PRIVATE_CANARY")
    safe = completeness_details([details])
    assert "PRIVATE_CANARY" not in json.dumps(safe)


async def test_declaration_repair_after_syntax_and_content_invalidation():
    workspace = ValidationWorkspace()
    try:
        with workspace.activate():
            invalid = {
                "terraform/main.tf": 'output "x" { value = [var.name var.other] }'
            }
            assert await repair_declarations(invalid) == (invalid, [])
            assert not workspace.declaration_fingerprints
            valid = {
                "terraform/main.tf": 'output "x" { value = [var.name, var.other] }'
            }
            repaired, records = await repair_declarations(valid)
            assert len(records) == 2
            assert await repair_declarations(repaired) == (repaired, [])
            changed = {
                **repaired,
                "terraform/main.tf": 'output "x" { value = var.third }',
            }
            again, records = await repair_declarations(changed)
            assert [r["name"] for r in records] == ["third"]
            assert not [
                c
                for c in reference_checks(PackageDocuments.parse(again))
                if c.status == "failed"
            ]
    finally:
        workspace.close()


def test_parsed_documents_reuse_unchanged_entries_and_invalidate_changed_content(
    monkeypatch,
):
    import app.validation.documents as documents

    calls = []
    parse = documents.hcl2.parses_to_tree

    def tracked(source):
        calls.append(source)
        return parse(source)

    monkeypatch.setattr(documents.hcl2, "parses_to_tree", tracked)
    workspace = ValidationWorkspace()
    try:
        with workspace.activate():
            files = {
                "terraform/a.tf": "locals { x = 1 }",
                "terraform/b.tf": "locals { y = 2 }",
            }
            first = PackageDocuments.parse(files)
            assert PackageDocuments.parse(files).documents == first.documents
            second = PackageDocuments.parse(
                {**files, "terraform/b.tf": "locals { y = 3 }"}
            )
            assert (
                first.documents["terraform/a.tf"] is second.documents["terraform/a.tf"]
            )
            assert len(calls) == 3
            for _ in range(3):
                reference_checks(second)
            assert len(calls) == 3
    finally:
        workspace.close()
    assert not workspace.document_cache and not workspace.index_cache


def test_variable_origin_survives_partial_observation_and_line_movement():
    workspace = ValidationWorkspace()
    check = ValidationCheck(
        check_id="terraform.var_ref",
        category="reference",
        tool="builtin",
        status="failed",
        file_path="terraform/main.tf",
        line_start=1,
        message="var.name is not declared",
    )
    try:
        workspace.observe(
            [check],
            "generated",
            {"terraform/main.tf": 'output "x" { value = var.name }'},
        )
        workspace.observe(
            [],
            "security_fix",
            {"terraform/main.tf": 'output "x" { value = var.name }'},
            partial=True,
        )
        moved = check.model_copy(update={"line_start": 10})
        workspace.observe(
            [moved],
            "security_fix",
            {"terraform/main.tf": "\n" * 9 + 'output "x" { value = var.name }'},
            partial=True,
        )
        assert workspace.annotate((moved,))[0].origin == "generated"
    finally:
        workspace.close()


async def test_iteration_deadline_includes_finalization_and_does_not_restart():
    now = [0.0]
    record = {}
    with pytest.raises(TimeoutError):
        async with iteration_window(60, lambda: now[0], record):
            now[0] = 56
            async with bounded_phase("restoration"):
                now[0] = 59
            async with bounded_phase("closing_state_event"):
                now[0] = 61
    assert record["deadline_overrun_seconds"] == 1
    assert "closing_state_event" in record["deadline_timings"]
    assert active_deadline.get() is None


async def test_shutdown_when_expired_kills_without_new_wait(monkeypatch):
    from types import SimpleNamespace

    communicate = AsyncMock()
    transport = SimpleNamespace(close=lambda: None)
    process = SimpleNamespace(pid=99, communicate=communicate, _transport=transport)
    killed = []
    monkeypatch.setattr(
        "app.scanners.runner.os.killpg", lambda *args: killed.append(args)
    )
    now = [0.0]
    async with iteration_window(60, lambda: now[0], {}):
        now[0] = 60
        await ProcessToolRunner()._terminate(process)
        now[0] = (
            59  # Let this probe finish; the caller's deadline check is tested above.
        )
    assert killed
    communicate.assert_not_awaited()


@pytest.mark.parametrize(
    "phase", ["workspace", "event_publication", "closing_state_event"]
)
async def test_waits_clip_to_same_absolute_window(phase):
    record = {}
    entered = asyncio.Event()
    with pytest.raises(TimeoutError):
        async with iteration_window(time.monotonic() + 0.02, time.monotonic, record):
            async with bounded_phase(phase):
                entered.set()
                await asyncio.Event().wait()
    assert entered.is_set() and phase in record["deadline_timings"]


def test_workload_partitions_preserve_failed_observations():
    runs = [
        {"run_id": k, "measurement": m, "role": r}
        for k, m, r in [
            ("a", "pr01", None),
            ("b", "pr03", "baseline"),
            ("c", "pr03", "cohort"),
        ]
    ]
    rows = [
        {
            "run_id": k,
            "agent": "security_iteration",
            "variant": "cost",
            "iteration": 0,
            "seconds": seconds,
            "threshold_seconds": 60,
            "pass": passed,
        }
        for k, seconds, passed in [("a", 59, True), ("b", None, None), ("c", 69, False)]
    ]
    result = pr05_workloads(runs, rows)
    assert result["isolated_pr01"]["verdict"] == "PASS"
    assert result["isolated_pr03_baseline"]["verdict"] == "INCOMPLETE"
    assert result["concurrent_pr03_cohort"]["failures"] == 1
    assert result["concurrent_pr03_cohort"]["failed_observations"][0]["seconds"] == 69
    assert sum(r["failures"] for r in result.values()) == sum(
        r.get("pass") is False for r in rows
    )


async def test_nine_packages_keep_cache_and_deadline_contexts_independent():
    async def one(number):
        workspace = ValidationWorkspace()
        files = {"terraform/main.tf": f'output "x" {{ value = var.input_{number} }}'}
        try:
            with workspace.activate():
                async with iteration_window(60 + number, lambda: 0.0, {}):
                    for _ in range(4):
                        checks = reference_checks(PackageDocuments.parse(files))
                        assert (
                            checks[0].message == f"var.input_{number} is not declared"
                        )
                        assert active_deadline.get().end == 60 + number
                        await asyncio.sleep(0)
                assert len(workspace.document_cache) == 1
        finally:
            workspace.close()

    await asyncio.gather(*(one(n) for n in range(9)))


async def test_initial_scanning_write_has_the_same_absolute_deadline():
    from types import SimpleNamespace

    from app.agents.security.agent import SecurityAgent
    from app.domain.enums import Variant

    security = object.__new__(SecurityAgent)
    security.settings = SimpleNamespace(security_deadline_seconds=240)
    security._loop = AsyncMock()
    entered = asyncio.Event()

    async def transition(*args, **kwargs):
        entered.set()
        window = active_deadline.get()
        assert window.end == 60
        window.end = window.clock()
        async with bounded_phase("initial_state_event"):
            await asyncio.Event().wait()

    ctx = SimpleNamespace(
        clock=lambda: 0.0,
        run_id="test",
        writer=SimpleNamespace(
            agent_state=AsyncMock(),
            package_transition=transition,
        ),
    )
    with pytest.raises(TimeoutError):
        await security.run(ctx, Variant.SECURITY, None)
    assert entered.is_set()
    security._loop.assert_not_awaited()


async def test_expiration_during_provenance_cannot_return_an_accepted_candidate(
    monkeypatch,
):
    from tests.unit.test_security_partial import setup

    now = [0.0]
    files = {"terraform/main.tf": 'output "x" { value = 1 }'}
    guard, checkpoint = setup(files, clock=lambda: now[0])
    workspace = ValidationWorkspace()
    observe = workspace.observe

    def slow_observation(*args, **kwargs):
        observe(*args, **kwargs)
        now[0] = 61

    monkeypatch.setattr(workspace, "observe", slow_observation)
    try:
        with workspace.activate():
            checks = await guard.checks(files)
            with pytest.raises(TimeoutError):
                await guard.evaluate(
                    files,
                    {"terraform/main.tf": 'output "x" { value = 2 }'},
                    checks,
                    checkpoint.scan,
                )
        assert checkpoint.files == files
    finally:
        workspace.close()
