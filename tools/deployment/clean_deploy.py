"""Author-run deployment; secrets stay in private local state, outside evidence."""

import argparse
import base64
import http.client
import json
import os
import secrets
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory


def commands() -> list[tuple[str, list[str]]]:
    return [
        ("backend_dependencies", ["make", "install"]),
        ("frontend_dependencies", ["make", "frontend-install"]),
        (
            "database",
            [
                "sudo",
                "--preserve-env=POSTGRES_PASSWORD,INFRAARCH_OWNER_PASSWORD,INFRAARCH_APP_PASSWORD",
                "docker",
                "compose",
                "--env-file",
                "/dev/null",
                "-p",
                "infraarch-clean",
                "up",
                "-d",
                "--wait",
                "postgres",
            ],
        ),
        ("migrations", ["make", "migrate"]),
        ("provider_mirror", ["make", "providers"]),
        ("provider_schemas", ["make", "provider-schema"]),
        ("frontend_build", ["make", "frontend-build"]),
    ]


def request(port: int, path: str, key: str, body: dict | None = None) -> dict:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    try:
        connection.request(
            "POST" if body else "GET",
            path,
            json.dumps(body) if body else None,
            {"X-API-Key": key, "Content-Type": "application/json"},
        )
        response = connection.getresponse()
        if response.status not in (200, 202):
            raise RuntimeError("Local API check failed")
        return json.loads(response.read())
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        print(json.dumps(commands(), indent=2))
        return
    root = args.checkout.resolve()
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    private = Path.home() / ".local/state/infraarchagent" / secrets.token_hex(8)
    private.mkdir(parents=True, mode=0o700)
    os.umask(0o077)
    owner, app, superuser = (secrets.token_hex(24) for _ in range(3))
    environment = {
        key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ
    }
    environment.update(
        {
            "POSTGRES_PASSWORD": superuser,
            "INFRAARCH_OWNER_PASSWORD": owner,
            "INFRAARCH_APP_PASSWORD": app,
            "DATABASE_URL": f"postgresql+asyncpg://infraarch_app:{app}@127.0.0.1:5432/infraarch",
            "MIGRATION_DATABASE_URL": f"postgresql+asyncpg://infraarch_owner:{owner}@127.0.0.1:5432/infraarch",
            "TEST_DATABASE_URL": f"postgresql+asyncpg://infraarch_app:{app}@127.0.0.1:5432/infraarch_test",
            "TEST_MIGRATION_DATABASE_URL": f"postgresql+asyncpg://infraarch_owner:{owner}@127.0.0.1:5432/infraarch_test",
            "CREDENTIAL_ENCRYPTION_KEY": base64.b64encode(
                secrets.token_bytes(32)
            ).decode(),
            "CREDENTIAL_ENCRYPTION_KEY_VERSION": "1",
            "API_KEY": secrets.token_urlsafe(32),
            "LLM_PROVIDER": "stub",
            "LLM_API_KEY": "",
            "LLM_MODEL": "stub",
            "SECURITY_FIX_PROVIDER": "stub",
            "PIPELINE_DEMO_SCENARIO": "clean",
            "LESSONS_ENABLED": "false",
        }
    )
    # Restart data is private operator state. Never copy it or the log to evidence.
    (private / "runtime.json").write_text(json.dumps(environment))
    report = {
        "status": "incomplete",
        "started_at": datetime.now(UTC).isoformat(),
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "scanner_note": "tfsec is superseded by Trivy 0.69.3 (D-31)",
        "steps": [],
    }
    try:
        with (private / "operations.log").open("w") as log:
            for name, command in commands():
                result = subprocess.run(
                    command,
                    cwd=root,
                    env=environment,
                    stdout=log,
                    stderr=log,
                    check=False,
                )
                report["steps"].append({"step": name, "exit_code": result.returncode})
                if result.returncode:
                    raise RuntimeError("Author deployment step failed")
            server = subprocess.Popen(
                [
                    str(root / "backend/.venv/bin/python"),
                    "-m",
                    "app.server",
                    "--port",
                    str(args.port),
                ],
                cwd=root / "backend",
                env=environment,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            (private / "backend.pid").write_text(str(server.pid))
            deadline = time.monotonic() + 120
            while True:
                try:
                    health = request(args.port, "/api/health", environment["API_KEY"])
                    if health.get("status") == "ok":
                        break
                except (OSError, RuntimeError):
                    pass
                if server.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("Health check did not pass")
                time.sleep(0.5)
            (evidence / "health.json").write_text(json.dumps(health, indent=2))
            accepted = request(
                args.port,
                "/api/pipeline/run",
                environment["API_KEY"],
                {
                    "text": "Synthetic clean-deployment demo: create an AWS web service with Terraform.",
                    "config": {"provider": "stub"},
                },
            )
            deadline = time.monotonic() + 600
            while True:
                result = request(
                    args.port,
                    f"/api/pipeline/{accepted['run_id']}/results",
                    environment["API_KEY"],
                )
                if result["run"]["status"] in {"success", "partial_success", "failed"}:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("Stub run did not settle")
                time.sleep(1)
            labels = {row["variant"]: row["status"] for row in result["packages"]}
            report["stub"] = {
                "run_id": accepted["run_id"],
                "status": result["run"]["status"],
                "labels": labels,
                "synthetic": True,
            }
            if len(labels) != 3 or set(labels.values()) != {"checks_passed"}:
                raise RuntimeError("Stub acceptance failed")
            with TemporaryDirectory(prefix="infraarch-version-") as probe_home:
                probe_environment = {
                    "PATH": environment["PATH"],
                    "HOME": probe_home,
                    "HTTP_PROXY": "http://127.0.0.1:9",
                    "HTTPS_PROXY": "http://127.0.0.1:9",
                    "NO_PROXY": "",
                }
                versions = {}
                for tool, argv in {
                    "python": [str(root / "backend/.venv/bin/python"), "--version"],
                    "node": ["node", "--version"],
                    "npm": ["npm", "--version"],
                    "docker": ["sudo", "docker", "--version"],
                    "checkov": ["checkov", "--version"],
                    "trivy": ["trivy", "--version"],
                    "terraform": ["terraform", "version"],
                    "postgres": [
                        "sudo",
                        "docker",
                        "compose",
                        "--env-file",
                        "/dev/null",
                        "-p",
                        "infraarch-clean",
                        "exec",
                        "-T",
                        "postgres",
                        "postgres",
                        "--version",
                    ],
                }.items():
                    probe = subprocess.run(
                        argv,
                        cwd=root,
                        env=probe_environment,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    versions[tool] = {
                        "exit_code": probe.returncode,
                        "version": probe.stdout.strip().splitlines()[:1],
                    }
            (evidence / "versions.json").write_text(json.dumps(versions, indent=2))
            report["status"] = "stub_passed_browser_checks_pending"
    except (OSError, RuntimeError):
        report["status"] = "failed"
        raise SystemExit(
            "Deployment failed; inspect the private operator log. No portability pass is recorded."
        ) from None
    finally:
        report["finished_at"] = datetime.now(UTC).isoformat()
        (evidence / "outcomes.json").write_text(json.dumps(report, indent=2))
        print(
            f"Evidence: {evidence}. Private restart state: {private}. Never commit private state."
        )


if __name__ == "__main__":
    main()
