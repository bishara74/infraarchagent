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
    if mode == "cancel":
        task=asyncio.create_task(runner.run("checkov",parent))
        async with asyncio.timeout(3):
            while not (parent/"pgids").exists(): await asyncio.sleep(.01)
        task.cancel()
        try: await task
        except asyncio.CancelledError: pass
        else: raise AssertionError("cancellation not propagated")
    else:
        try:
            if mode == "scan":
                await Scanner(runner).scan(
                    {"terraform/main.tf":"locals {}"},Variant.SECURITY
                )
            else:
                await runner.run("checkov",parent)
        except ToolFailure as e: assert e.category == "timeout"
        else: raise AssertionError("timeout not raised")
    assert time.monotonic()-started < 8
    # Scanner mode stores its PID file in its temporary HOME before removal;
    # the executable also writes to a dedicated observation directory.
    pgids=[int(x) for x in (parent/"observed").read_text().splitlines()]
    deadline=time.monotonic()+2
    for pgid in pgids:
        while True:
            try:
                while os.waitpid(-1,os.WNOHANG)[0]: pass
            except ChildProcessError: pass
            try: os.killpg(pgid,0)
            except ProcessLookupError: break
            assert time.monotonic()<deadline,"process group survived"
            await asyncio.sleep(.01)
    if mode == "scan":
        assert not list(parent.glob("infraarch-scan-*")),"temporary directory survived"
asyncio.run(main())
"""


@pytest.mark.req("FR-S-01")
@pytest.mark.parametrize("mode", ["timeout", "cancel", "scan"])
def test_timeout_kills_forked_stdout_owner(tmp_path: Path, mode: str) -> None:
    fake = tmp_path / "checkov"
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
        "TMPDIR": str(tmp_path),
        "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
    }
    try:
        completed = subprocess.run(
            [sys.executable, "-c", HARNESS],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=12,
        )
        assert completed.returncode == 0, completed.stderr
    finally:
        if (tmp_path / "observed").exists():
            for value in (tmp_path / "observed").read_text().splitlines():
                try:
                    os.killpg(int(value), signal.SIGKILL)
                except ProcessLookupError:
                    pass
