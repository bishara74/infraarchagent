import pytest

from app.scanners.runner import ToolFailure, ToolResult
from scripts import mirror_providers as script


class Provision:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    async def run_command(self, tool, args, root, **kwargs):
        self.calls.append((args, kwargs.get("allow_provider_download", False)))
        result = self.results.pop(0)
        if isinstance(result, ToolFailure):
            raise result
        return result


def configure(tmp_path, monkeypatch, runner):
    config = tmp_path / "tools"
    config.mkdir()
    (config / "aws5").mkdir()
    monkeypatch.setattr(script, "CONFIG", config)
    monkeypatch.setattr(script, "CONFIG_ROOTS", (config, config / "aws5"))
    monkeypatch.setattr(script, "MIRROR", tmp_path / "mirror")
    monkeypatch.setattr(script, "ProcessToolRunner", lambda timeout: runner)


@pytest.mark.req("FR-V-03")
@pytest.mark.parametrize(
    "failure",
    [ToolResult("", "Download failed", 1, 0), ToolFailure("terraform", "timeout")],
)
async def test_download_failure_stops_without_retry_or_lock(
    tmp_path, monkeypatch, failure
):
    runner = Provision([failure])
    configure(tmp_path, monkeypatch, runner)
    assert await script.mirror_providers() == 1
    assert len(runner.calls) == 1
    assert runner.calls[0][0][1:3] == ["providers", "mirror"]
    assert not (script.CONFIG / "README.md").exists()


@pytest.mark.req("FR-V-03")
async def test_mirror_success_locks_offline_and_records_hashes(tmp_path, monkeypatch):
    runner = Provision(
        [ToolResult("Package authenticated: signed by HashiCorp\n", "", 0, 0)] * 2
        + [ToolResult("Offline locks", "", 0, 0)] * 2
    )
    configure(tmp_path, monkeypatch, runner)
    script.MIRROR.mkdir()
    archive = script.MIRROR / "test_linux_amd64.zip"
    archive.write_bytes(b"archive")
    assert await script.mirror_providers() == 0
    assert [online for _, online in runner.calls] == [True, True, False, False]
    assert all(args[1:3] == ["providers", "lock"] for args, _ in runner.calls[2:])
    report = (script.CONFIG / "README.md").read_text()
    assert script.archive_hash(archive) in report
    assert "signed by HashiCorp" in report
    assert "Mirror file bytes: 7" in report
