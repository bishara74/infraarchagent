"""NFR-04: deployment recipes are inspectable without installing anything."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "tools/deployment/clean_deploy.py"
pytestmark = pytest.mark.req("NFR-04", "NFR-01")


def load_driver():
    spec = importlib.util.spec_from_file_location("clean_deploy", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_never_creates_files_or_invokes_installation(tmp_path):
    output = subprocess.check_output(
        [
            sys.executable,
            str(SCRIPT),
            "--checkout",
            str(tmp_path / "clone"),
            "--evidence",
            str(tmp_path / "evidence"),
        ],
        text=True,
    )
    rows = json.loads(output)
    assert [name for name, _ in rows] == [
        "backend_dependencies",
        "frontend_dependencies",
        "database",
        "migrations",
        "provider_mirror",
        "provider_schemas",
        "frontend_build",
    ]
    assert not list(tmp_path.iterdir())
    assert "--env-file" in rows[2][1] and "/dev/null" in rows[2][1]


def test_shell_recipes_are_valid_and_pin_verified_trivy():
    scripts = [
        ROOT / "tools/deployment/clean-ubuntu.sh",
        ROOT / "tools/deployment/install-prerequisites.sh",
    ]
    for script in scripts:
        subprocess.run(["bash", "-n", str(script)], check=True)
    installer = scripts[1].read_text()
    assert "trivy_version=0.69.3" in installer
    assert "sha256sum -c trivy.sha256" in installer
    assert installer.index("sha256sum -c trivy.sha256") < installer.index(
        'tar -xzf "$trivy_archive"'
    )


def test_smoke_request_is_loopback_and_does_not_disclose_key(monkeypatch):
    driver = load_driver()
    calls = []

    class Connection:
        def __init__(self, host, port, timeout):
            assert host == "127.0.0.1" and port == 8000

        def request(self, method, path, body, headers):
            calls.append((method, path, json.loads(body), headers))

        def getresponse(self):
            return type(
                "Response",
                (),
                {"status": 202, "read": lambda self: b'{"run_id":"synthetic"}'},
            )()

        def close(self):
            pass

    monkeypatch.setattr(driver.http.client, "HTTPConnection", Connection)
    result = driver.request(
        8000,
        "/api/pipeline/run",
        "synthetic-only-key",
        {"text": "Synthetic demo", "config": {"provider": "stub"}},
    )
    assert calls[0][2]["config"]["provider"] == "stub"
    assert calls[0][3]["X-API-Key"] == "synthetic-only-key"
    assert result == {"run_id": "synthetic"}
