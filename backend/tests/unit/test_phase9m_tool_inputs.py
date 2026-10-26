"""NFR-01/FR-V-03: all Terraform evaluation paths refuse escaped file reads."""

from unittest.mock import AsyncMock

import pytest

from app.scanners.runner import ProcessToolRunner, ToolFailure
from app.validation.documents import PackageDocuments
from app.validation.syntax import native_syntax
from app.validation.terraform import file_input_guard

pytestmark = pytest.mark.req("NFR-01", "FR-V-03")
FUNCTIONS = [
    "file",
    "filebase64",
    "filemd5",
    "filesha1",
    "filesha256",
    "filesha512",
    "filebase64sha256",
    "filebase64sha512",
    "fileexists",
    "fileset",
    "templatefile",
]


def source(function, path):
    extra = (
        ', "*"'
        if function == "fileset"
        else ", {}"
        if function == "templatefile"
        else ""
    )
    return f'output "probe" {{ value = {function}("{path}"{extra}) }}\n'


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("json_mode", [False, True])
def test_all_file_function_families_reject_outside_paths(tmp_path, function, json_mode):
    import json

    text = source(function, str(tmp_path.parent / "synthetic-outside.txt"))
    if json_mode:
        text = json.dumps(
            {
                "output": {
                    "probe": {
                        "value": "${"
                        + text.split("value = ", 1)[1].rsplit(" }", 1)[0]
                        + "}"
                    }
                }
            }
        )
    path = "terraform/main.tf.json" if json_mode else "terraform/main.tf"
    checks = file_input_guard(tmp_path, PackageDocuments.parse({path: text}))
    assert checks and checks[0].status == "failed"


@pytest.mark.parametrize("command", ["init", "validate"])
@pytest.mark.parametrize("layout", ["terraform/main.tf", "main.tf.json"])
async def test_process_boundary_rejects_before_launch(
    tmp_path, monkeypatch, command, layout
):
    import json

    text = source("filesha256", str(tmp_path.parent / "synthetic-canary.txt"))
    if layout.endswith("json"):
        text = json.dumps(
            {
                "output": {
                    "probe": {
                        "value": '${filesha256("'
                        + str(tmp_path.parent / "synthetic-canary.txt")
                        + '")}'
                    }
                }
            }
        )
    target = tmp_path / layout
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    launch = AsyncMock(side_effect=AssertionError("unsafe command launched"))
    monkeypatch.setattr("asyncio.create_subprocess_exec", launch)
    with pytest.raises(ToolFailure, match="unsafe_file_input"):
        await ProcessToolRunner().run_command(
            "terraform", ["terraform", command], tmp_path, cwd=target.parent
        )
    launch.assert_not_called()


async def test_json_native_syntax_cannot_read_outside_package():
    files = {
        "terraform/main.tf.json": (
            '{"output":{"probe":{"value":"${filesha256('
            '\\"/synthetic-outside-canary\\")}"}}}'
        )
    }
    with pytest.raises(ToolFailure, match="unsafe_file_input"):
        await native_syntax(files)


async def test_scanner_validate_cannot_read_outside_package(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform/main.tf").write_text(
        source("file", str(tmp_path.parent / "synthetic-outside.txt"))
    )
    with pytest.raises(ToolFailure, match="unsafe_file_input"):
        await ProcessToolRunner().run("terraform", tmp_path)


def test_inside_package_and_dynamic_inputs_use_existing_policy(tmp_path):
    files = {"terraform/main.tf": source("filesha256", "${path.module}/safe.txt")}
    assert file_input_guard(tmp_path, PackageDocuments.parse(files)) == []
    files = {"terraform/main.tf": 'output "x" { value = filesha256(var.filename) }'}
    assert (
        file_input_guard(tmp_path, PackageDocuments.parse(files))[0].skip_reason
        == "uninspectable_file_input"
    )


async def test_real_validate_reads_only_synthetic_package_local_file(tmp_path):
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform/safe.txt").write_text("synthetic test data")
    (tmp_path / "terraform/main.tf").write_text(
        source("filesha256", "${path.module}/safe.txt")
    )
    result = await ProcessToolRunner(10).run("terraform", tmp_path)
    assert result.exit_code == 0


@pytest.mark.parametrize("function", ["file", "filesha256"])
async def test_unicode_escaped_paths_are_decoded_before_any_launch(
    tmp_path, monkeypatch, function
):
    escaped = str(tmp_path.parent / "synthetic-outside.txt").replace("/", r"\u002f")
    (tmp_path / "terraform").mkdir()
    (tmp_path / "terraform/main.tf").write_text(source(function, escaped))
    launch = AsyncMock(side_effect=AssertionError("escaped outside read launched"))
    monkeypatch.setattr("asyncio.create_subprocess_exec", launch)
    with pytest.raises(ToolFailure, match="unsafe_file_input"):
        await ProcessToolRunner().run("terraform", tmp_path)
    launch.assert_not_called()
