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
        f"cd backend && .venv/bin/python -m app.server --host 127.0.0.1 --port {port}"
    )


@pytest.mark.req("FR-UI-01")
def test_operator_docs_match_worker_reload_and_current_scanner_commands():
    from app.scanners.runner import TOOLS

    root = Path(__file__).resolve().parents[3]
    agents = (root / "AGENTS.md").read_text()
    readme = (root / "README.md").read_text()
    caption = next(line for line in agents.splitlines() if "| `make run` |" in line)
    assert "one worker" in caption and "with reload" not in caption
    assert "one worker without automatic reload" in readme
    assert "checkov" in TOOLS and "trivy" in TOOLS and "tfsec" not in TOOLS
    assert "Checkov and Trivy" in agents.split("## 2.")[0]
    assert "Checkov and tfsec" not in agents.split("## 2.")[0]
