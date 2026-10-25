"""Timing wrappers preserve evidence and forward only isolated test settings."""

import json
from types import SimpleNamespace

import pytest

from scripts import measure_performance


@pytest.mark.req("PR-02", "NFR-01")
@pytest.mark.parametrize("kind", ["backend", "ui"])
def test_wrapper_raw_reports_and_safe_child_environment(tmp_path, kind):
    def runner(command, **kwargs):
        env = kwargs["env"]
        assert env["INFRAARCH_TEST_BOOTSTRAP"] == "1"
        assert env["LLM_API_KEY"] == "" and env["API_KEY"] == ""
        assert env["DATABASE_URL"] == env["TEST_DATABASE_URL"]
        assert env["LLM_PROVIDER"] == "stub"
        if kind == "backend":
            (tmp_path / "results.xml").write_text(
                '<testsuites><testsuite tests="6" failures="0" errors="0" '
                'skipped="0"/></testsuites>'
            )
            assert "--junitxml" in command
        else:
            (tmp_path / "playwright.json").write_text(
                json.dumps(
                    {
                        "stats": {
                            "expected": 1,
                            "unexpected": 0,
                            "skipped": 0,
                            "flaky": 0,
                        }
                    }
                )
            )
            assert "@perf" in command
            assert env["INFRAARCH_PHASE9_OUTPUT_DIR"] == str(tmp_path)
        return SimpleNamespace(returncode=0, stdout="recorded test output", stderr="")

    report = measure_performance.run(kind, tmp_path, runner=runner)
    assert report["counts"]["passed"] == (6 if kind == "backend" else 1)
    assert (tmp_path / "console.txt").read_text() == "recorded test output"
    assert "PASS" in (tmp_path / "summary.md").read_text()


@pytest.mark.req("PR-02")
def test_wrapper_missing_results_stays_incomplete(tmp_path):
    def runner(*args, **kwargs):
        return SimpleNamespace(
            returncode=1, stdout="", stderr="prerequisite unavailable"
        )

    report = measure_performance.run("ui", tmp_path, runner=runner)
    assert report["counts"] is None
    assert "INCOMPLETE" in (tmp_path / "summary.md").read_text()


@pytest.mark.req("PR-04", "NFR-01")
def test_backend_uses_shared_settings_resolver_and_same_perf_selection(
    tmp_path, monkeypatch
):
    from tests.unit.test_run_verification import synthetic_settings

    resolved = []

    def settings():
        resolved.append(True)
        return synthetic_settings()

    monkeypatch.setattr(measure_performance, "get_settings", settings)

    def runner(command, **kwargs):
        assert command[1:6] == ["-m", "scripts.run_verification", "pytest", "-q", "-m"]
        assert command[6] == "perf"
        assert not any(argument.startswith("tests/") for argument in command)
        assert kwargs["env"]["DATABASE_URL"] == "test-app-canary"
        assert kwargs["env"]["LLM_PROVIDER"] == "stub"
        (tmp_path / "results.xml").write_text(
            '<testsuite tests="1" failures="0" errors="0" skipped="0">'
            '<testcase classname="tests.download" name="pr04"><properties>'
            '<property name="pr04_seconds" value="0.75"/>'
            "</properties></testcase></testsuite>"
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    report = measure_performance.run("backend", tmp_path, runner=runner)
    assert resolved == [True]
    assert report["status"] == "PASS"
    assert report["measurements"] == [
        {"id": "tests.download::pr04", "pr04_seconds": 0.75}
    ]


@pytest.mark.req("PR-04", "NFR-01")
@pytest.mark.parametrize("tag", ["failure", "error"])
def test_failing_test_or_prerequisite_is_named_and_all_reports_are_redacted(
    tmp_path, monkeypatch, tag
):
    from tests.unit.test_run_verification import synthetic_settings

    settings = synthetic_settings()
    monkeypatch.setattr(measure_performance, "get_settings", lambda: settings)
    secrets = [
        "llm-secret-canary",
        "api-secret-canary",
        "test-app-canary",
        "normal-owner-canary",
    ]
    leaked = " ".join(secrets)

    def runner(*args, **kwargs):
        failure = int(tag == "failure")
        (tmp_path / "results.xml").write_text(
            f'<testsuite tests="1" failures="{failure}" '
            f'errors="{1 - failure}" skipped="0">'
            f'<testcase classname="tests.download" name="pr04[llm-secret-canary]">'
            f'<{tag} message="Database prerequisite: {leaked}">{leaked}</{tag}>'
            "</testcase></testsuite>"
        )
        return SimpleNamespace(returncode=1, stdout=leaked, stderr=leaked)

    report = measure_performance.run("backend", tmp_path, runner=runner)
    assert report["returncode"] == 1 and report["status"] == "FAIL"
    assert report["failed_tests"][0]["id"] == "tests.download::pr04[[REDACTED]]"
    assert report["failed_tests"][0]["kind"] == tag
    assert "Database prerequisite:" in report["failed_tests"][0]["message"]
    for path in tmp_path.iterdir():
        assert all(secret not in path.read_text() for secret in secrets), path


@pytest.mark.req("PR-04", "NFR-01")
def test_setting_failure_reports_only_declared_field_names(tmp_path, monkeypatch):
    from app.core.config import Settings

    def invalid():
        return Settings(_env_file=None, llm_provider="invalid-provider-secret-canary")

    monkeypatch.setattr(measure_performance, "get_settings", invalid)

    def forbidden(*args, **kwargs):
        pytest.fail("Invalid settings must not launch tests")

    report = measure_performance.run("backend", tmp_path, runner=forbidden)
    assert report["status"] == "INCOMPLETE" and report["returncode"] == 2
    assert report["stage"] == "settings" and "LLM_PROVIDER" in report["reason"]
    for path in tmp_path.iterdir():
        assert "invalid-provider-secret-canary" not in path.read_text()


@pytest.mark.req("PR-04", "NFR-01")
@pytest.mark.parametrize("problem", ["timeout", "launch", "settings_access"])
def test_execution_prerequisite_failures_have_safe_stages(
    tmp_path, monkeypatch, problem
):
    import subprocess

    from tests.unit.test_run_verification import synthetic_settings

    settings = synthetic_settings()

    def resolve():
        if problem == "settings_access":
            raise PermissionError("settings-access-secret-canary")
        return settings

    monkeypatch.setattr(measure_performance, "get_settings", resolve)

    def runner(*args, **kwargs):
        if problem == "timeout":
            (tmp_path / "results.xml").write_text("llm-secret-canary")
            raise subprocess.TimeoutExpired(
                args[0], 1800, output=b"llm-secret-canary", stderr="api-secret-canary"
            )
        raise FileNotFoundError("launch-secret-canary")

    report = measure_performance.run("backend", tmp_path, runner=runner)
    assert report["status"] == "INCOMPLETE" and report["returncode"] == 2
    assert report["stage"] == ("settings" if problem == "settings_access" else problem)
    assert report["reason"]
    for path in tmp_path.iterdir():
        assert all(
            secret not in path.read_text()
            for secret in [
                "llm-secret-canary",
                "api-secret-canary",
                "launch-secret-canary",
                "settings-access-secret-canary",
            ]
        )


@pytest.mark.req("PR-04")
@pytest.mark.parametrize(
    "contents",
    [
        None,
        "not XML",
        "<unrelated/>",
        "<testsuites/>",
        '<testsuite tests="0"/>',
        '<testsuite tests="1" failures="2"/>',
    ],
)
@pytest.mark.parametrize("returncode", [0, 4])
def test_missing_or_malformed_report_cannot_pass_and_preserves_failure_exit(
    tmp_path, contents, returncode
):
    def runner(*args, **kwargs):
        if contents is not None:
            (tmp_path / "results.xml").write_text(contents)
        return SimpleNamespace(
            returncode=returncode, stdout="collection/prerequisite output", stderr=""
        )

    report = measure_performance.run("backend", tmp_path, runner=runner)
    assert report["status"] == "INCOMPLETE" and report["counts"] is None
    assert report["returncode"] == (returncode or 2)
    assert "results.xml" in report["reason"]
    assert "collection/prerequisite output" in (tmp_path / "console.txt").read_text()


@pytest.mark.req("PR-04", "NFR-01")
def test_main_prints_failure_reason_and_evidence_directory(
    tmp_path, monkeypatch, capsys
):
    import sys

    from app.core.config import Settings

    monkeypatch.setattr(sys, "argv", ["measure_performance", "backend"])
    monkeypatch.setattr(
        measure_performance, "evidence_directory", lambda *a, **kw: tmp_path
    )

    def invalid():
        return Settings(_env_file=None, llm_provider="console-secret-canary")

    monkeypatch.setattr(measure_performance, "get_settings", invalid)
    with pytest.raises(SystemExit) as error:
        measure_performance.main()
    assert error.value.code == 2
    output = capsys.readouterr().out
    assert (
        "INCOMPLETE" in output and "LLM_PROVIDER" in output and str(tmp_path) in output
    )
    assert "console-secret-canary" not in output


@pytest.mark.req("PR-04", "NFR-01")
def test_evidence_creation_failure_identifies_safe_prerequisite(
    tmp_path, monkeypatch, capsys
):
    import sys

    monkeypatch.setattr(sys, "argv", ["measure_performance", "backend"])

    def unavailable(*args, **kwargs):
        raise FileExistsError("evidence-path-secret-canary")

    monkeypatch.setattr(measure_performance, "evidence_directory", unavailable)
    with pytest.raises(SystemExit) as error:
        measure_performance.main()
    assert error.value.code == 2
    output = capsys.readouterr().err
    assert "FileExistsError" in output and "--output-dir" in output
    assert "evidence-path-secret-canary" not in output
