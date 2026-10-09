import json
import shutil
from pathlib import Path

import pytest

from app.scanners.runner import ProcessToolRunner, ToolFailure, ToolResult
from app.validation.documents import PackageDocuments
from app.validation.linters import linter_targets, parse_lint, run_linter

FIXTURES = Path(__file__).parents[1] / "fixtures/validation/linters"
TOOLS = ("helm", "hadolint", "ansible-lint", "promtool")


class Recorded:
    def __init__(self, result):
        self.result = result

    async def run_command(self, *args, **kwargs):
        if isinstance(self.result, ToolFailure):
            raise self.result
        return self.result


def recorded(tool):
    capture = json.loads((FIXTURES / f"{tool}.json").read_text())
    target = next(
        target
        for target in linter_targets(PackageDocuments.parse(capture[("files")]))
        if target.tool == tool
    )
    return (
        capture,
        target,
        ToolResult(capture[("stdout")], capture[("stderr")], capture[("exit_code")], 0),
    )


@pytest.mark.req("FR-V-04", "NFR-01")
@pytest.mark.parametrize("tool", TOOLS)
def test_actual_recorded_linter_formats(tool):
    capture, target, result = recorded(tool)
    checks = parse_lint(
        target, result, Path("/__RECORDED_ROOT__"), set(capture["files"])
    )
    assert checks and all(check.file_path in capture["files"] for check in checks)
    assert any(
        check.status == (("warning") if tool == ("hadolint") else ("failed"))
        for check in checks
    )
    if tool == "ansible-lint":
        assert len(checks) == 5
        assert {c.line_start for c in checks} == {1, 3}
    if tool == "promtool":
        assert checks[0].line_start == 3


@pytest.mark.req("FR-V-04")
@pytest.mark.parametrize("tool", TOOLS)
@pytest.mark.parametrize(
    ("failure,reason"),
    [
        (("not_installed"), ("not_installed")),
        (("timeout"), ("tool_error")),
        (("launch_error"), ("tool_error")),
    ],
)
async def test_missing_or_failed_optional_tools(tool, failure, reason, tmp_path):
    capture, target, _ = recorded(tool)
    checks = await run_linter(
        target, tmp_path, set(capture[("files")]), Recorded(ToolFailure(tool, failure))
    )
    assert checks[0].status == "skipped" and checks[0].skip_reason == reason


@pytest.mark.req("FR-V-04", "NFR-01")
@pytest.mark.parametrize("tool", TOOLS)
async def test_unusable_or_crashed_outputs_are_skips(tool, tmp_path):
    capture, target, _ = recorded(tool)
    for result in (
        ToolResult("nonsense", "canary-key", 0, 0),
        ToolResult("[]", "", -9, 0),
    ):
        checks = await run_linter(
            target, tmp_path, set(capture["files"]), Recorded(result)
        )
        assert checks[0].skip_reason == "tool_error"
        assert "canary-key" not in checks[0].model_dump_json()


@pytest.mark.req("FR-V-04")
@pytest.mark.parametrize(
    ("severity,status"),
    [
        (("error"), ("failed")),
        (("warning"), ("warning")),
        (("info"), ("warning")),
        (("style"), ("warning")),
    ],
)
def test_hadolint_severity_and_location_fallback(severity, status):
    capture, target, _ = recorded("hadolint")
    result = ToolResult(json.dumps([{"code": "DL3000", "level": severity}]), "", 1, 0)
    check = parse_lint(target, result, Path("/root"), set(capture["files"]))[0]
    assert (
        check.status == status
        and check.file_path == target.file_path
        and check.line_start == 1
    )


@pytest.mark.req("FR-V-04")
@pytest.mark.parametrize(
    ("severity,status"),
    [
        (("major"), ("failed")),
        (("critical"), ("failed")),
        (("minor"), ("warning")),
        (("info"), ("warning")),
    ],
)
def test_ansible_severity_and_supported_location_shapes(severity, status):
    capture, target, _ = recorded("ansible-lint")
    for location in (
        {("path"): ("ansible/playbook.yaml"), ("lines"): {("begin"): 3}},
        {("path"): ("playbook.yaml"), ("positions"): {("begin"): {("line"): 3}}},
    ):
        result = ToolResult(
            json.dumps([{("severity"): severity, ("location"): location}]), (), 2, 0
        )
        check = parse_lint(target, result, Path("/root"), set(capture["files"]))[0]
        assert check.status == status and check.line_start == 3


@pytest.mark.req("NFR-01")
def test_linter_paths_outside_package_are_rejected():
    capture, target, _ = recorded("hadolint")
    result = ToolResult(
        json.dumps(
            [
                {
                    ("code"): ("DL3000"),
                    ("level"): ("error"),
                    ("file"): ("/etc/secret"),
                    ("line"): 1,
                }
            ]
        ),
        (),
        1,
        0,
    )
    with pytest.raises(ValueError):
        parse_lint(target, result, Path("/root"), set(capture["files"]))


@pytest.mark.req("FR-V-04")
def test_prometheus_rule_and_supporting_file_target_discovery():
    files = {
        ("monitoring/prometheus/rules.yaml"): ("groups: []"),
        ("monitoring/prometheus/config.yaml"): ("scrape_configs: []"),
        ("ansible/roles/web/tasks/main.yaml"): ("- debug: {msg: hi}"),
    }
    targets = linter_targets(PackageDocuments.parse(files))
    assert [target.args[2] for target in targets] == ["config", "rules"]
    assert not any(target.tool == "ansible-lint" for target in targets)


@pytest.mark.scanners
@pytest.mark.req("FR-V-04", "NFR-01")
@pytest.mark.parametrize("tool", TOOLS)
async def test_actual_clean_optional_linters(tmp_path, tool):
    if not shutil.which(tool):
        pytest.skip("linter not installed")
    files = {
        ("helm"): {
            ("helm/web/Chart.yaml"): (
                "apiVersion: v2\nname: web\nversion: 1.0.0\nicon:"
                " https://example.com/icon.png"
            ),
            ("helm/web/values.yaml"): ("{}"),
            ("helm/web/templates/service.yaml"): (
                "apiVersion: v1\nkind: Service\nmetadata: {name:"
                " web}\nspec: {ports: [{port: 80}]}"
            ),
        },
        "hadolint": {"docker/Dockerfile": "FROM alpine:3.20\n"},
        ("ansible-lint"): {
            ("ansible/playbook.yaml"): (
                "- name: Validate playbook\n  hosts: all\n  gath"
                "er_facts: false\n  tasks:\n    - name: Say hell"
                "o\n      ansible.builtin.debug:\n        msg: H"
                "ello\n"
            )
        },
        "promtool": {"monitoring/prometheus/prometheus.yaml": "scrape_configs: []\n"},
    }[tool]
    for name, source in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    target = linter_targets(PackageDocuments.parse(files))[0]
    checks = await run_linter(target, tmp_path, set(files), ProcessToolRunner(60))
    assert checks and all(check.status == "passed" for check in checks)


@pytest.mark.req("FR-V-04", "NFR-01")
@pytest.mark.parametrize("tool", TOOLS)
def test_raw_diagnostic_text_never_enters_reports(tool):
    capture, target, result = recorded(tool)
    result = ToolResult(
        result.stdout.replace(("name[play]"), ("canary-key")).replace(
            ("Using latest"), ("canary-key Using latest")
        ),
        result.stderr + (" canary-key"),
        result.exit_code,
        0,
    )
    checks = parse_lint(
        target, result, Path("/__RECORDED_ROOT__"), set(capture["files"])
    )
    assert all("canary-key" not in check.model_dump_json() for check in checks)


@pytest.mark.req("NFR-01")
def test_promtool_unsafe_reported_paths_are_rejected():
    capture, target, _ = recorded("promtool")
    result = ToolResult("", "FAILED: parsing YAML file /etc/secret.yaml: error", 1, 0)
    with pytest.raises(ValueError):
        parse_lint(target, result, Path("/root"), set(capture["files"]))


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    ("path,source"),
    [
        (
            ("monitoring/prometheus/config.yaml"),
            ("scrape_configs: []\nrule_files: [/etc/private.yaml]"),
        ),
        (
            ("ansible/playbook.yaml"),
            ("- hosts: all\n  vars_files: [../../private.yaml]"),
        ),
        (
            ("ansible/playbook.yaml"),
            ("- hosts: all\n  vars: {value: \"{{ lookup('file', 'private') }}\"}"),
        ),
    ],
)
async def test_external_file_reads_and_dynamic_lookups_are_refused(
    path, source, tmp_path
):
    target = linter_targets(PackageDocuments.parse({path: source}))[0]
    assert not target.safe_to_run

    class NeverRun:
        async def run_command(self, *args, **kwargs):
            raise AssertionError("unsafe inputs must never launch a tool")

    assert (await run_linter(target, tmp_path, {path}, NeverRun()))[0].skip_reason == (
        "tool_error"
    )
