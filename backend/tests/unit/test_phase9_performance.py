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
