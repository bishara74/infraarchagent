"""Operator command defaults without starting a server or reading dotenv."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.req("FR-UI-01")
@pytest.mark.parametrize("arguments,port", [([], 8000), (["PORT=8765"], 8765)])
def test_run_port_default_and_override(arguments, port):
    root = Path(__file__).resolve().parents[3]
    completed = subprocess.run(
        ["make", "-n", "run", *arguments],
        cwd=root,
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == (
        f"cd backend && .venv/bin/uvicorn app.main:app --workers 1 --port {port}"
    )
