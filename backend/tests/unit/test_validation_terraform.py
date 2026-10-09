import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from app.scanners.runner import (
    ProcessToolRunner,
    ToolFailure,
    ToolResult,
    scanner_environment,
)
from app.validation.terraform import (
    module_preflight,
    terraform_diagnostics,
    validate_terraform,
)
from app.validation.tools import mirror_present

FIXTURES = Path(__file__).parents[1] / "fixtures/validation/terraform"


class Commands:
    def __init__(self, *results):
        self.results = list(results)
        self.calls = []

    async def run_command(self, tool, args, root, **kwargs):
        self.calls.append(args)
        result = self.results.pop(0)
        if isinstance(result, ToolFailure):
            raise result
        return result


def write_fixture(root, case="valid"):
    tf = root / "terraform"
    tf.mkdir()
    (tf / "providers.tf").write_text((FIXTURES / "providers.tf").read_text())
    (tf / "main.tf").write_text((FIXTURES / f"{case}.main.tf").read_text())
    return {"terraform/providers.tf", "terraform/main.tf"}


@pytest.mark.req("FR-V-03", "FR-V-04")
@pytest.mark.parametrize(
    "case,line,title",
    [
        ("valid", None, None),
        ("invalid_resource", 1, "Invalid resource type"),
        ("invalid_argument", 2, "Unsupported argument"),
        ("syntax", 2, "Invalid expression"),
    ],
)
def test_real_recorded_schema_diagnostics(case, line, title):
    checks = terraform_diagnostics(
        (FIXTURES / f"{case}.json").read_text(),
        Path("/__RECORDED_ROOT__"),
        {"terraform/main.tf", "terraform/providers.tf"},
    )
    assert checks[0].status == ("passed" if title is None else "failed")
    if title:
        assert checks[0].message == title
        assert checks[0].file_path == "terraform/main.tf"
        assert checks[0].line_start == line


@pytest.mark.req("FR-V-03", "NFR-01")
@pytest.mark.parametrize(
    "raw",
    [
        "not json",
        "{}",
        '{"valid":false,"diagnostics":[]}',
        '{"valid":true,"diagnostics":[{"severity":"unknown"}]}',
    ],
)
def test_malformed_output_is_rejected(raw):
    with pytest.raises(ValueError):
        terraform_diagnostics(raw, Path("/root"), set())


@pytest.mark.req("FR-V-03", "NFR-01")
def test_diagnostic_rejects_external_paths_and_omits_source_details():
    data = json.loads((FIXTURES / "invalid_argument.json").read_text())
    data["diagnostics"][0]["summary"] = "canary-key"
    data["diagnostics"][0]["detail"] = "canary-key"
    check = terraform_diagnostics(
        json.dumps(data), Path("/__RECORDED_ROOT__"), {"terraform/main.tf"}
    )[0]
    assert "canary" not in check.model_dump_json()
    data["diagnostics"][0]["range"]["filename"] = "/tmp/canary-key.tf"
    with pytest.raises(ValueError):
        terraform_diagnostics(
            json.dumps(data), Path("/__RECORDED_ROOT__"), {"terraform/main.tf"}
        )


@pytest.mark.req("FR-V-03")
async def test_missing_mirror_does_not_invoke_runner(tmp_path):
    files = write_fixture(tmp_path)
    runner = Commands()
    checks = await validate_terraform(tmp_path, files, runner, tmp_path / "missing")
    assert checks[0].skip_reason == "mirror_missing"
    assert runner.calls == []


@pytest.mark.req("FR-V-03")
@pytest.mark.parametrize(
    "category,expected",
    [
        ("not_installed", "not_installed"),
        ("timeout", "tool_error"),
        ("launch_error", "tool_error"),
    ],
)
async def test_required_tool_errors(tmp_path, category, expected):
    files = write_fixture(tmp_path)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    (mirror / "test_linux_amd64.zip").touch()
    runner = Commands(ToolFailure("terraform", category))
    assert (await validate_terraform(tmp_path, files, runner, mirror))[
        0
    ].skip_reason == expected


@pytest.mark.req("FR-V-03")
async def test_unavailable_version_and_malformed_output(tmp_path):
    files = write_fixture(tmp_path)
    mirror = tmp_path / "mirror"
    mirror.mkdir()
    (mirror / "test_linux_amd64.zip").touch()
    missing = json.dumps(
        dict(
            valid=False,
            diagnostics=[dict(severity="error", summary="Missing required provider")],
        )
    )
    runner = Commands(
        ToolResult("Failed to query available provider packages", "", 1, 0),
        ToolResult(missing, "", 1, 0),
    )
    assert (await validate_terraform(tmp_path, files, runner, mirror))[
        0
    ].skip_reason == "provider_version_not_in_mirror"
    runner = Commands(ToolResult("", "", 0, 0), ToolResult("malformed", "", 0, 0))
    assert (await validate_terraform(tmp_path, files, runner, mirror))[
        0
    ].skip_reason == "tool_error"


@pytest.mark.req("FR-V-01", "FR-V-03")
@pytest.mark.parametrize(
    "source,reason",
    [
        ("remote/registry/aws", "remote_module_not_available_offline"),
        ("../../escape", "unsafe_local_module"),
        ("./missing", "local_module_missing"),
    ],
)
def test_module_preflight_reasons(tmp_path, source, reason):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform/main.tf").write_text(
        f'module "test" {{ source = "{source}" }}'
    )
    assert module_preflight(tmp_path, {"terraform/main.tf"})[0] == reason


@pytest.mark.req("FR-V-01", "FR-V-03")
def test_recursive_local_modules_and_json_sources(tmp_path):
    tf = tmp_path / "terraform"
    tf.mkdir()
    child = tf / "child"
    child.mkdir()
    (tf / "main.tf.json").write_text(
        json.dumps({"module": {"child": {"source": "./child"}}})
    )
    (child / "main.tf").write_text('module "escape" { source = "../../../escape" }')
    assert module_preflight(tmp_path, set())[0] == "unsafe_local_module"
    (child / "main.tf").write_text('output "test" { value = 1 }')
    assert module_preflight(tmp_path, set()) == (None, True)


@pytest.mark.scanners
@pytest.mark.req("FR-V-03")
@pytest.mark.parametrize(
    "case", ["valid", "invalid_resource", "invalid_argument", "syntax"]
)
async def test_real_mirror_backed_validation(tmp_path, case):
    if not shutil.which("terraform") or not mirror_present():
        pytest.skip("Terraform or provider mirror unavailable")
    files = write_fixture(tmp_path, case)
    checks = await validate_terraform(tmp_path, files, ProcessToolRunner(30))
    assert checks[0].status == ("passed" if case == "valid" else "failed")


@pytest.mark.scanners
@pytest.mark.req("FR-V-03", "NFR-01")
def test_real_terraform_in_network_namespace(tmp_path):
    if not shutil.which("terraform") or not mirror_present():
        pytest.skip("Terraform or provider mirror unavailable")
    if (
        not shutil.which("unshare")
        or subprocess.run(["unshare", "-Urn", "true"], capture_output=True).returncode
    ):
        pytest.skip("network namespaces unavailable")
    write_fixture(tmp_path, "invalid_argument")
    script = """import asyncio,sys
from pathlib import Path
from app.validation.terraform import validate_terraform
from app.scanners.runner import ProcessToolRunner
async def main():
 files={'terraform/main.tf','terraform/providers.tf'}
 checks=await validate_terraform(Path(sys.argv[1]),files,ProcessToolRunner(30))
 assert checks[0].status=='failed' and checks[0].message=='Unsupported argument'
asyncio.run(main())
"""
    env = scanner_environment(tmp_path, "terraform")
    env["PYTHONPATH"] = str(Path(__file__).parents[2])
    completed = subprocess.run(
        ["unshare", "-Urn", sys.executable, "-c", script, str(tmp_path)],
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.req("FR-V-01", "FR-V-03")
def test_preflight_reuses_shared_parser_index(tmp_path, monkeypatch):
    import hcl2

    from app.validation.documents import PackageDocuments

    files = write_fixture(tmp_path)
    documents = PackageDocuments.parse(
        {path: (tmp_path / path).read_text() for path in files}
    )

    def unexpected(*args, **kwargs):
        raise AssertionError("Terraform must not parse the source a second time")

    monkeypatch.setattr(hcl2, "loads", unexpected)
    assert module_preflight(tmp_path, files, documents) == (None, False)
