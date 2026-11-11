# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Offline control-flow and environment tests for the native soak."""

import asyncio
import json
import signal
from types import SimpleNamespace

import httpx
import pytest

from app.scanners.runner import scanner_environment
from scripts import soak_native

KEY = "fixture-soak-auth-canary"


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


@pytest.mark.req("FR-P-04", "NFR-01")
async def test_cancelled_report_includes_failed_variants():
    row = {"cancel_requested": True, "cancel_attempted": False}
    run_id = "00000000-0000-0000-0000-000000000001"
    paths = []

    def respond(request):
        path = request.url.path
        paths.append(path)
        assert request.headers["X-API-Key"] == KEY
        if path == "/api/pipeline/run":
            return httpx.Response(202, json={"run_id": run_id})
        if path.endswith("/stream"):
            return httpx.Response(
                200,
                text='data: {"seq": 1, "kind": "package_status", "status": "scanning",'
                ' "message": "security scan started", "payload": {}}\n\n',
            )
        if path.endswith("/cancel"):
            assert json.loads(request.content) == {"reviewer_name": "soak"}
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

    async with soak_native.soak_client(
        "http://test", KEY, 1, transport=httpx.MockTransport(respond)
    ) as client:
        await soak_native.observe(
            client, "prompt", row, soak_native.error_redactor(KEY)
        )
    assert [path.split("/")[-1] for path in paths] == [
        "run",
        "stream",
        "cancel",
        "results",
    ]
    assert row["cancelled"] is True
    assert row["submit_http_status"] == 202
    assert row["cancel_http_status"] == 202
    assert row["package_statuses"] == {"cost": "checks_passed", "security": "failed"}


@pytest.mark.req("FR-P-04")
async def test_soak_stops_on_server_death_during_stream(tmp_path):
    server = SimpleNamespace(returncode=None, poll=lambda: server.returncode)
    submitted = []
    report = {
        "parameters": {"runs": 3, "concurrency": 1, "cancel_every": 3},
        "runs": [],
        "server_checks": [],
        "resources": [],
    }

    async def respond(request):
        assert request.headers["X-API-Key"] == KEY
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

    client = soak_native.soak_client(
        "http://test", KEY, 1, transport=httpx.MockTransport(respond)
    )
    async with asyncio.timeout(5):
        with pytest.raises(soak_native.SoakError, match="exited unexpectedly"):
            await soak_native.drive(
                server,
                client,
                report,
                tmp_path / "report.json",
                soak_native.error_redactor(KEY),
            )
    assert len(submitted) == 1
    assert len(report["runs"]) == 1
    assert report["runs"][0]["ended_at"] is not None
    assert report["server_checks"][-1]["alive"] is False


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("field", ["error", "code"])
async def test_failed_submission_records_http_status_and_server_code(field):
    def respond(request):
        return httpx.Response(401, json={field: "unauthorized"})

    row = {"run_id": None}
    async with soak_native.soak_client(
        "http://test", KEY, 1, transport=httpx.MockTransport(respond)
    ) as client:
        with pytest.raises(soak_native.SoakError, match=r"HTTP 401 \(unauthorized\)"):
            await soak_native.submit(
                client, "prompt", row, soak_native.error_redactor(KEY)
            )
    assert row == {
        "run_id": None,
        "submit_http_status": 401,
        "submit_error_code": "unauthorized",
    }


@pytest.mark.req("NFR-01")
def test_written_failure_report_redacts_secrets_in_all_group_errors(
    tmp_path, monkeypatch, capsys
):
    app_url = (
        "postgresql+asyncpg://infraarch_app:fixture%3Aapp@127.0.0.1/infraarch_test"
    )
    owner_url = (
        "postgresql+asyncpg://infraarch_owner:fixture-owner@127.0.0.1/infraarch_test"
    )
    monkeypatch.setenv("TEST_DATABASE_URL", app_url)
    monkeypatch.setenv("TEST_MIGRATION_DATABASE_URL", owner_url)
    monkeypatch.setattr(soak_native, "OUTPUT", tmp_path)
    monkeypatch.setattr(soak_native.sys, "argv", ["soak_native"])
    sizes = []

    def token_urlsafe(size):
        sizes.append(size)
        return KEY

    def fail(args, directory, report, api_key, redact):
        try:
            raise ValueError(f"submit with {api_key} failed")
        except ValueError as first:
            nested = ExceptionGroup(
                "nested group", [first, RuntimeError(f"connect {app_url}")]
            )
        other = [RuntimeError(f"worker {i} {owner_url}") for i in range(17)]
        raise ExceptionGroup(
            "soak workers", [nested, *other, RuntimeError("password fixture:app")]
        )

    monkeypatch.setattr(soak_native.secrets, "token_urlsafe", token_urlsafe)
    monkeypatch.setattr(soak_native, "run", fail)
    with pytest.raises(SystemExit) as error:
        soak_native.main()
    assert error.value.code == 1
    assert sizes == [32]
    (path,) = tmp_path.glob("*/report.json")
    raw = path.read_text()
    report = json.loads(raw)
    detail = report["error_detail"]
    assert "Traceback (most recent call last)" in detail
    assert "nested group" in detail
    assert "submit with [REDACTED] failed" in detail
    assert "worker 16 [REDACTED]" in detail
    assert "password [REDACTED]" in detail
    stdout, stderr = capsys.readouterr()
    assert "submit with [REDACTED] failed" in stderr
    assert "worker 16 [REDACTED]" in stderr
    readme = path.with_name("README.md").read_text()
    for secret in (
        KEY,
        app_url,
        owner_url,
        "fixture:app",
        "fixture%3Aapp",
        "fixture-owner",
    ):
        assert all(secret not in value for value in (raw, stdout, stderr, readme))
