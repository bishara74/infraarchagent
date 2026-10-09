import json
from pathlib import Path

import pytest

from app.scanners.runner import ProcessToolRunner, ToolFailure
from app.validation.tools import validator_versions


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("online", [False, True])
async def test_explicit_commands_preserve_minimal_environment(
    tmp_path, monkeypatch, online
):
    binary = tmp_path / "terraform"
    binary.write_text(
        "#!/usr/bin/env python3\nimport json,os\nprint(json.dumps(dict(os.environ)))\n"
    )
    binary.chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:/usr/bin:/bin")
    monkeypatch.setenv("LLM_API_KEY", "canary-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "canary-key")
    result = await ProcessToolRunner(5).run_command(
        "terraform",
        ["terraform", "providers", "mirror"],
        tmp_path,
        allow_provider_download=online,
    )
    env = json.loads(result.stdout)
    assert "canary" not in result.stdout
    assert env["TF_DATA_DIR"] == str(tmp_path / ".terraform-data")
    if online:
        assert "HTTPS_PROXY" not in env
    else:
        assert env["HTTPS_PROXY"] == "http://127.0.0.1:9"


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "args,kwargs,category",
    [
        (["/tmp/terraform"], {}, "unsafe_command"),
        (
            ["terraform", "validate"],
            {"allow_provider_download": True},
            "unsafe_network_command",
        ),
        (["terraform", "validate"], {"cwd": Path("/")}, "unsafe_workdir"),
    ],
)
async def test_unsafe_command_paths_and_network_modes(tmp_path, args, kwargs, category):
    with pytest.raises(ToolFailure) as caught:
        await ProcessToolRunner().run_command("terraform", args, tmp_path, **kwargs)
    assert caught.value.category == category


@pytest.mark.scanners
@pytest.mark.req("FR-V-03", "NFR-01")
def test_actual_installed_validator_versions_are_reported():
    versions = validator_versions()
    expected = {
        "terraform": "1.16.4",
        "helm": "v4.3.0+gbec5b06",
        "hadolint": "2.15.1",
        "ansible-lint": "26.9.0",
        "promtool": "3.15.0",
    }
    if not all(row["available"] for row in versions.values()):
        pytest.skip("validators not all installed")
    for tool, version in expected.items():
        assert version in versions[tool]["version"]
