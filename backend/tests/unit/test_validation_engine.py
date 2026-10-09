import asyncio
import json

import pytest

from app.domain.validation import ValidationCheck
from app.scanners.runner import ToolFailure, ToolResult
from app.validation.engine import ValidationEngine
from tests.unit.test_generators import plan


class Clean:
    async def run_command(self, tool, args, root, **kwargs):
        if tool == "terraform":
            return ToolResult(
                json.dumps(dict(valid=True, diagnostics=[]))
                if args[1] == ("validate")
                else (),
                (),
                0,
                0,
            )
        if tool == "hadolint":
            return ToolResult("[]", "", 0, 0)
        if tool == ("helm"):
            return ToolResult(("1 chart(s) linted, 0 chart(s) failed"), (), 0, 0)
        raise ToolFailure(tool, "not_installed")


def mirror(tmp_path):
    path = tmp_path / "mirror"
    path.mkdir()
    (path / "fake_linux_amd64.zip").touch()
    return path


@pytest.mark.req("FR-V-03", "FR-V-04")
async def test_complete_engine_outcomes_and_required_unavailability(tmp_path):
    engine = ValidationEngine(Clean(), mirror=mirror(tmp_path), versions={})
    report = await engine.validate(plan(), {"terraform/main.tf": "terraform {}"})
    assert report.summary.result == "valid"
    assert any(
        c.check_id == ("terraform.validate") and c.status == ("passed")
        for c in report.checks
    )
    engine.mirror = tmp_path / "missing"
    assert (
        await engine.validate(plan(), {("terraform/main.tf"): ("terraform {}")})
    ).summary.result == ("error")
    report = await engine.validate(
        plan("dockerfile"),
        {
            ("terraform/main.tf"): ("terraform {}"),
            ("docker/Dockerfile"): ("RUN echo hello"),
        },
    )
    assert report.summary.result == "invalid" and report.summary.failed >= 1


@pytest.mark.req("FR-V-04", "NFR-01")
@pytest.mark.parametrize(
    ("files"),
    [
        {("../unsafe.tf"): ("canary-key")},
        {(".env"): ("canary-key")},
        {("terraform/main.tf"): ("x") * 200001},
    ],
)
async def test_unsafe_or_oversized_inputs_abort_safely(files, tmp_path):
    report = await ValidationEngine(Clean(), versions={}).validate(plan(), files)
    assert report.summary.result == "error" and report.abort_reason == "internal_error"
    assert "canary-key" not in report.model_dump_json()


@pytest.mark.req("FR-V-05", "NFR-01")
async def test_barrier_proves_three_tool_limit_and_cleanup(tmp_path):
    class Barrier(Clean):
        def __init__(self):
            self.started = asyncio.Event()
            self.release = asyncio.Event()
            self.count = 0
            self.maximum = 0
            self.roots = []

        async def run_command(self, tool, args, root, **kwargs):
            self.count += 1
            self.maximum = max(self.maximum, self.count)
            self.roots.append(root)
            if self.count == 3:
                self.started.set()
            try:
                await self.release.wait()
                return await super().run_command(tool, args, root, **kwargs)
            finally:
                self.count -= 1

    runner = Barrier()
    files = {
        ("terraform/main.tf"): ("terraform {}"),
        **{f"docker/app{i}/Dockerfile": ("FROM alpine:3.20") for i in range(5)},
    }
    engine = ValidationEngine(runner, mirror=mirror(tmp_path), versions={})
    task = asyncio.create_task(engine.validate(plan("dockerfile"), files))
    await asyncio.wait_for(runner.started.wait(), 2)
    assert runner.count == 3 and runner.maximum == 3
    runner.release.set()
    report = await task
    assert report.summary.result == "valid" and runner.maximum == 3
    assert all(not root.exists() for root in runner.roots)


@pytest.mark.req("FR-V-05")
@pytest.mark.parametrize("mode", ["deadline", "cancel"])
async def test_deadline_and_cancellation_cleanup(tmp_path, mode):
    class Blocked(Clean):
        def __init__(self):
            self.started = asyncio.Event()
            self.cancelled = asyncio.Event()
            self.root = None

        async def run_command(self, tool, args, root, **kwargs):
            self.root = root
            self.started.set()
            try:
                await asyncio.Event().wait()
            finally:
                self.cancelled.set()

    runner = Blocked()
    engine = ValidationEngine(
        runner,
        mirror=mirror(tmp_path),
        versions={},
        deadline_seconds=0.05 if mode == ("deadline") else 10,
    )
    task = asyncio.create_task(
        engine.validate(plan(), {("terraform/main.tf"): ("terraform {}")})
    )
    await runner.started.wait()
    if mode == "cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        report = await task
        assert report.summary.result == "error" and report.abort_reason == "deadline"
    assert runner.cancelled.is_set() and not runner.root.exists()


@pytest.mark.req("FR-V-05")
async def test_internal_abort_preserves_completed_failures(tmp_path, monkeypatch):
    from app.validation import engine as module

    class Broken(Clean):
        async def run_command(self, *args, **kwargs):
            raise RuntimeError("canary-key")

    failure = ValidationCheck(
        check_id=("test.failure"),
        category=("structure"),
        tool=("builtin"),
        status=("failed"),
        file_path=("terraform/main.tf"),
        line_start=1,
        message=("Safe failure"),
    )
    monkeypatch.setattr(module, "structural_checks", lambda *args: [failure])
    report = await ValidationEngine(
        Broken(), mirror=mirror(tmp_path), versions={}
    ).validate(plan(), {("terraform/main.tf"): ("terraform {}")})
    assert report.summary.result == "error" and report.abort_reason == "internal_error"
    assert report.failed_checks_for_remediation == (failure,)
    assert "canary-key" not in report.model_dump_json()


@pytest.mark.req("FR-V-03", "NFR-01")
@pytest.mark.parametrize(
    ("expression,expected"),
    [
        (('file("/etc/private")'), ("invalid")),
        (("file(var.path)"), ("error")),
        (('file("${path.module}/main.tf")'), ("valid")),
    ],
)
async def test_terraform_file_functions_cannot_read_outside_copy(
    tmp_path, expression, expected
):
    files = {
        "terraform/main.tf": 'variable "path" { default = "main.tf" }\n'
        + f'output "value" {{ value = {expression} }}'
    }
    report = await ValidationEngine(
        Clean(), mirror=mirror(tmp_path), versions={}
    ).validate(plan(), files)
    assert report.summary.result == expected


@pytest.mark.req("NFR-01")
async def test_literal_file_function_text_is_not_an_executed_reference(tmp_path):
    files = {"terraform/main.tf": 'locals { text = "file(\\"/etc/private\\")" }'}
    report = await ValidationEngine(
        Clean(), mirror=mirror(tmp_path), versions={}
    ).validate(plan(), files)
    assert report.summary.result == "valid"
