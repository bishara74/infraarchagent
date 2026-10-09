import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scanners.runner import ProcessToolRunner

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "backend/tests/fixtures/validation/linters"
CASES = {
    ("helm"): {
        ("helm/web/Chart.yaml"): ("apiVersion: v2\nname: web\nversion: 1.0.0\n"),
        ("helm/web/values.yaml"): ("replicas: 1\n"),
        ("helm/web/templates/deployment.yaml"): (
            "apiVersion: apps/v1\nkind: Deployment\nmetadata"
            ":\n  name: web\nspec:\n  replicas: {{ .Values.re"
            "plicas }}\n"
        ),
    },
    "hadolint": {"docker/Dockerfile": "FROM alpine:latest\nRUN echo hello\n"},
    ("ansible-lint"): {
        ("ansible/playbook.yaml"): ("- hosts: all\n  tasks:\n    - shell: echo hello\n")
    },
    ("promtool"): {
        ("monitoring/prometheus/prometheus.yaml"): (
            "scrape_configs:\n  - job_name: web\n    invalid_option: true\n"
        )
    },
}


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    runner = ProcessToolRunner(60)
    for tool, files in CASES.items():
        with TemporaryDirectory(prefix="infraarch-linter-capture-") as directory:
            root = Path(directory)
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            args = {
                ("helm"): [
                    ("helm"),
                    ("lint"),
                    ("helm/web"),
                    ("--skip-schema-validation"),
                ],
                ("hadolint"): [
                    ("hadolint"),
                    ("--format"),
                    ("json"),
                    ("docker/Dockerfile"),
                ],
                ("ansible-lint"): [
                    ("ansible-lint"),
                    ("--offline"),
                    ("--nocolor"),
                    ("-f"),
                    ("json"),
                    ("--project-dir"),
                    ("ansible"),
                    ("ansible/playbook.yaml"),
                ],
                ("promtool"): [
                    ("promtool"),
                    ("check"),
                    ("config"),
                    ("monitoring/prometheus/prometheus.yaml"),
                ],
            }[tool]
            result = await runner.run_command(tool, args, root)
            capture = {
                ("command"): args,
                ("exit_code"): result.exit_code,
                ("stdout"): result.stdout.replace(str(root), ("/__RECORDED_ROOT__")),
                ("stderr"): result.stderr.replace(str(root), ("/__RECORDED_ROOT__")),
                ("files"): files,
            }
            (OUT / (tool + ".json")).write_text(json.dumps(capture, indent=2) + "\n")
            print(tool, result.exit_code, result.stdout[:800], result.stderr[:800])


asyncio.run(main())
