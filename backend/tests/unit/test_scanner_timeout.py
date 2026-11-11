# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""FR-S-01: inherited stdout must not survive a scanner deadline."""

import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

SCANNER = """#!/usr/bin/env python3
import os,time
from pathlib import Path
try:
    os.setsid()
except PermissionError:
    pass
r,w=os.pipe()
child=os.fork()
if child == 0:
    os.close(r)
    os.write(w,b"ready")
    os.close(w)
    while True: time.sleep(60)
os.close(w)
os.read(r,5)
os.close(r)
with Path("pgids").open("a") as f: f.write(str(os.getpgrp())+"\\n")
while True: time.sleep(60)
"""

HARNESS = """
import asyncio,ctypes,os,time
from pathlib import Path
from tempfile import TemporaryDirectory
from app.domain.enums import Variant
from app.scanners.runner import ProcessToolRunner,ToolFailure
from app.scanners.scan import Scanner
# Adopt and reap killed grandchildren, even when the host PID 1 is not a reaper.
assert ctypes.CDLL(None).prctl(36,1,0,0,0) == 0
async def main():
    parent=Path.cwd()
    runner=ProcessToolRunner(1)
    mode=os.environ["TEST_MODE"]
    started=time.monotonic()
    if mode in {"validator", "cancel_validator"}:
        from app.validation.engine import ValidationEngine
        from app.validation.documents import PackageDocuments
        from tests.unit.test_generators import plan
        files={"terraform/main.tf":"terraform {}"}
        PackageDocuments.parse(files)
        mirror=parent/"mirror"
        mirror.mkdir()
        (mirror/"fake_linux_amd64.zip").touch()
        engine=ValidationEngine(
            ProcessToolRunner(30),mirror=mirror,versions={},
            deadline_seconds=30 if mode=="cancel_validator" else 1
        )
        if mode == "validator":
            report=await engine.validate(plan(),files)
            assert report.abort_reason=="deadline"
    if mode.startswith("cancel"):
        release_launch=asyncio.Event()
        if mode == "cancel_launch":
            launch=asyncio.create_subprocess_exec
            async def delayed_launch(*args,**kwargs):
                process=await launch(*args,**kwargs)
                await release_launch.wait()
                return process
            asyncio.create_subprocess_exec=delayed_launch
        if mode == "cancel_validator":
            work=engine.validate(plan(),files)
        elif mode == "cancel_scan":
            work=Scanner(ProcessToolRunner(30)).scan(
                {"terraform/main.tf":"locals {}"},Variant.SECURITY
            )
        else:
            work=ProcessToolRunner(30).run("checkov",parent)
        task=asyncio.create_task(work)
        observed=parent/"observed"
        async with asyncio.timeout(3):
            while not observed.exists() or not observed.read_text().strip():
                await asyncio.sleep(.01)
        cancel_deadline=time.monotonic()+5
        task.cancel()
        # Deliver cancellation while delayed_launch still owns the handle.
        await asyncio.sleep(0)
        release_launch.set()
        try: await asyncio.wait_for(task,5)
        except asyncio.CancelledError: pass
        else: raise AssertionError("cancellation not propagated")
    elif mode != "validator":
        try:
            if mode == "scan":
                await Scanner(runner).scan(
                    {"terraform/main.tf":"locals {}"},Variant.SECURITY
                )
            else:
                await runner.run("checkov",parent)
        except ToolFailure as e: assert e.category == "timeout"
        else: raise AssertionError("timeout not raised")
    if os.environ["TEST_PERFORMANCE"] == "1":
        assert time.monotonic()-started < 8
    # Scanner mode stores its PID file in its temporary HOME before removal;
    # the executable also writes to a dedicated observation directory.
    pgids=[int(x) for x in (parent/"observed").read_text().splitlines()]
    assert pgids,"stub did not report a process group"
    deadline=cancel_deadline if mode.startswith("cancel") else time.monotonic()+2
    for pgid in pgids:
        while True:
            try:
                while os.waitpid(-1,os.WNOHANG)[0]: pass
            except ChildProcessError: pass
            try: os.killpg(pgid,0)
            except ProcessLookupError: break
            assert time.monotonic()<deadline,"process group survived"
            await asyncio.sleep(.01)
    if mode in {"scan","validator","cancel_scan","cancel_validator"}:
        assert not list(parent.glob("infraarch-*-*")),"temporary directory survived"
asyncio.run(main())
"""


def _check_process_cleanup(
    tmp_path: Path, mode: str, *, performance: bool = False
) -> None:
    fake = tmp_path / ("terraform" if "validator" in mode else "checkov")
    # Observation survives Scanner's directory cleanup, without inheriting an
    # arbitrary environment variable into the fake executable.
    script = SCANNER.replace(
        "while True: time.sleep(60)\n", "while True: time.sleep(60)\n"
    ).replace(
        'with Path("pgids").open("a") as f:',
        f'with Path({str(tmp_path / "observed")!r}).open("a") as f: '
        'f.write(str(os.getpgrp())+"\\n")\n'
        'with Path("pgids").open("a") as f:',
    )
    fake.write_text(script)
    fake.chmod(0o755)
    env = {
        "PATH": f"{tmp_path}:/usr/bin:/bin",
        "TEST_MODE": mode,
        "TEST_PERFORMANCE": "1" if performance else "0",
        "TMPDIR": str(tmp_path),
        "INFRAARCH_TEST_BOOTSTRAP": "1",
        "PYTHONPATH": (
            f"{Path(__file__).resolve().parents[2] / 'tests/bootstrap'}:"
            f"{Path(__file__).resolve().parents[2]}"
        ),
    }
    try:
        completed = subprocess.run(
            [sys.executable, "-c", HARNESS],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert completed.returncode == 0, completed.stderr
    finally:
        if (tmp_path / "observed").exists():
            for value in (tmp_path / "observed").read_text().splitlines():
                try:
                    os.killpg(int(value), signal.SIGKILL)
                except ProcessLookupError:
                    pass


@pytest.mark.req("FR-S-01", "FR-V-05", "NFR-01")
@pytest.mark.parametrize("mode", ["timeout", "cancel", "scan", "validator"])
def test_timeout_kills_forked_stdout_owner(tmp_path: Path, mode: str) -> None:
    _check_process_cleanup(tmp_path, mode)


@pytest.mark.req("FR-S-01", "FR-V-05")
@pytest.mark.parametrize("mode", ["cancel_scan", "cancel_validator", "cancel_launch"])
def test_cancellation_kills_tool_process_group_within_five_seconds(
    tmp_path: Path, mode: str
) -> None:
    _check_process_cleanup(tmp_path, mode)


@pytest.mark.perf
@pytest.mark.req("FR-S-01", "FR-V-05", "NFR-01")
@pytest.mark.parametrize("mode", ["timeout", "cancel", "scan", "validator"])
def test_process_cleanup_finishes_under_eight_seconds(
    tmp_path: Path, mode: str
) -> None:
    _check_process_cleanup(tmp_path, mode, performance=True)
