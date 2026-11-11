# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Offline control-flow and environment tests for the native soak."""

import asyncio
import signal
from types import SimpleNamespace

import httpx
import pytest

from app.scanners.runner import scanner_environment
from scripts import soak_native


def test_defaults_and_off_override(monkeypatch):
    for name in ("RUNS", "CONCURRENCY", "CANCEL_EVERY", "MALLOC_CHECK"):
        monkeypatch.delenv(name, raising=False)
    assert vars(soak_native.arguments([])) == {
        "runs": 60,
        "concurrency": 3,
        "cancel_every": 10,
        "malloc_check": "on",
    }
    monkeypatch.setenv("MALLOC_CHECK", "off")
    assert soak_native.arguments(["--runs", "3"]).malloc_check == "off"


@pytest.mark.parametrize("flag", ["--runs", "--concurrency", "--cancel-every"])
def test_positive_integer_arguments(flag):
    with pytest.raises(SystemExit) as error:
        soak_native.arguments([flag, "0"])
    assert error.value.code == 2


def test_rejects_invalid_malloc_environment(monkeypatch):
    monkeypatch.setenv("MALLOC_CHECK", "bad")
    with pytest.raises(SystemExit):
        soak_native.arguments([])


@pytest.mark.req("FR-P-04")
def test_cancel_every_uses_one_based_run_numbers():
    assert [i for i in range(1, 9) if soak_native.should_cancel(i, 3)] == [3, 6]


def test_allocator_off_removes_variables():
    original = dict.fromkeys(soak_native.ALLOCATOR_KEYS, "inherited")
    original["PATH"] = "/usr/bin"
    env, mode = soak_native.allocator_environment(original, "off")
    assert (env, mode) == ({"PATH": "/usr/bin"}, "off")
    assert all(key in original for key in soak_native.ALLOCATOR_KEYS)


@pytest.mark.req("FR-S-01", "FR-V-01")
def test_scanner_and_validator_environments_exclude_malloc_variables(
    tmp_path, monkeypatch
):
    for key in soak_native.ALLOCATOR_KEYS:
        monkeypatch.setenv(key, "server-only")
    for tool in (
        "checkov",
        "trivy",
        "terraform",
        "helm",
        "hadolint",
        "ansible-lint",
        "ansible-playbook",
        "promtool",
    ):
        assert not set(soak_native.ALLOCATOR_KEYS).intersection(
            scanner_environment(tmp_path, tool)
        )


@pytest.mark.req("FR-P-04")
async def test_cancelled_report_includes_failed_variants():
    row = {"cancel_requested": True, "cancel_attempted": False}
    run_id = "00000000-0000-0000-0000-000000000001"
    paths = []

    def respond(request):
        path = request.url.path
        paths.append(path)
        if path == "/api/pipeline/run":
            return httpx.Response(202, json={"run_id": run_id})
        if path.endswith("/stream"):
            return httpx.Response(
                200,
                text='data: {"seq": 1, "kind": "package_status", "status": "scanning",'
                ' "message": "security scan started", "payload": {}}\n\n',
            )
        if path.endswith("/cancel"):
            return httpx.Response(202)
        assert path.endswith("/results")
        return httpx.Response(
            200,
            json={
                "run": {"status": "cancelled"},
                "packages": [{"variant": "cost", "status": "checks_passed"}],
                "missing_variants": [{"variant": "security"}],
            },
        )

    async with httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(respond)
    ) as client:
        await soak_native.observe(client, "prompt", row)
    assert [path.split("/")[-1] for path in paths] == [
        "run",
        "stream",
        "cancel",
        "results",
    ]
    assert row["cancelled"] is True
    assert row["cancel_http_status"] == 202
    assert row["package_statuses"] == {"cost": "checks_passed", "security": "failed"}


@pytest.mark.req("FR-P-04")
async def test_soak_stops_on_server_death_during_stream(tmp_path, monkeypatch):
    server = SimpleNamespace(returncode=None, poll=lambda: server.returncode)
    submitted = []
    report = {
        "parameters": {"runs": 3, "concurrency": 1, "cancel_every": 3},
        "runs": [],
        "server_checks": [],
        "resources": [],
    }

    async def respond(request):
        if request.url.path == "/api/health":
            return httpx.Response(200)
        if request.url.path == "/api/pipeline/run":
            submitted.append(request)
            return httpx.Response(
                202, json={"run_id": "00000000-0000-0000-0000-000000000001"}
            )
        assert request.url.path.endswith("/stream")
        server.returncode = -signal.SIGABRT
        await asyncio.Event().wait()

    client = httpx.AsyncClient
    monkeypatch.setattr(
        soak_native.httpx,
        "AsyncClient",
        lambda **kwargs: client(transport=httpx.MockTransport(respond), **kwargs),
    )
    async with asyncio.timeout(5):
        with pytest.raises(soak_native.SoakError, match="exited unexpectedly"):
            await soak_native.drive(
                server, "http://test", report, tmp_path / "report.json"
            )
    assert len(submitted) == 1
    assert len(report["runs"]) == 1
    assert report["runs"][0]["ended_at"] is not None
    assert report["server_checks"][-1]["alive"] is False
