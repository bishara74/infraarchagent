# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Exercise the direct fault descriptor without changing pytest's own handler."""

import os
import signal
import subprocess
import sys
from pathlib import Path

from app.core import diagnostics

BACKEND = Path(__file__).resolve().parents[2]


def test_enable_keeps_one_append_descriptor(tmp_path, monkeypatch, capsys):
    path = diagnostics.fault_log_path(os.getpid(), tmp_path)
    path.write_bytes(b"previous entry\n")
    calls = []

    def enable(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(diagnostics, "_fault_log", None)
    monkeypatch.setattr(diagnostics, "_fault_pid", None)
    monkeypatch.setattr(diagnostics.faulthandler, "enable", enable)
    assert diagnostics.enable_fault_diagnostics(tmp_path) == path
    with calls[0]["file"] as log:
        assert diagnostics.enable_fault_diagnostics(tmp_path) == path
        assert calls == [{"file": log, "all_threads": True}]
        assert not log.closed
        assert path.read_text().startswith("previous entry\nNative runtime ")
        lines = capsys.readouterr().err.splitlines()
        assert len(lines) == 2
        assert lines[0].startswith("Native runtime ")
        assert lines[1] == f"Faulthandler log {path}"


def test_sigabrt_writes_fatal_stack_to_direct_log(tmp_path):
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            """
import ctypes
import faulthandler
import sys
from pathlib import Path
from app.core.diagnostics import enable_fault_diagnostics

assert ctypes.CDLL(None).prctl(4, 0, 0, 0, 0) == 0  # PR_SET_DUMPABLE
enable_fault_diagnostics(Path(sys.argv[1]))
assert faulthandler.is_enabled()

def abort_for_test():
    faulthandler._sigabrt()

abort_for_test()
""",
            str(tmp_path),
        ],
        cwd=BACKEND,
        stderr=subprocess.PIPE,
    )
    with child:
        _, stderr = child.communicate(timeout=10)
    assert child.returncode == -signal.SIGABRT
    path = diagnostics.fault_log_path(child.pid, tmp_path)
    assert str(path).encode() in stderr
    contents = path.read_text()
    assert "Fatal Python error" in contents
    assert "in abort_for_test" in contents
