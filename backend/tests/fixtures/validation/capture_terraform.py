import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scanners.runner import ProcessToolRunner

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "backend/tests/fixtures/validation/terraform"
PROVIDERS = """terraform {
  required_providers {
    random = {
      source = "hashicorp/random"
      version = "= 3.9.1"
    }
  }
}
"""
CASES = {
    "valid": 'resource "random_pet" "example" {\n  length = 2\n}\n',
    "invalid_resource": 'resource "random_nonexistent" "example" {\n  length = 2\n}\n',
    "invalid_argument": 'resource "random_pet" "example" {\n  lenghtt = 2\n}\n',
    "syntax": 'resource "random_pet" "example" {\n  length =\n}\n',
}


async def main():
    runner = ProcessToolRunner(60)
    for name, source in CASES.items():
        with TemporaryDirectory(prefix="infraarch-validation-capture-") as directory:
            root = Path(directory)
            tf = root / "terraform"
            tf.mkdir()
            (tf / "providers.tf").write_text(PROVIDERS)
            (tf / "main.tf").write_text(source)
            init = await runner.run_command(
                "terraform",
                [
                    "terraform",
                    "init",
                    "-backend=false",
                    "-input=false",
                    f"-plugin-dir={ROOT}/.cache/terraform-providers",
                    "-get=false",
                    "-no-color",
                ],
                root,
                cwd=tf,
            )
            validate = await runner.run_command(
                "terraform",
                ["terraform", "validate", "-json", "-no-color"],
                root,
                cwd=tf,
            )
            data = json.loads(validate.stdout)
            for diag in data["diagnostics"]:
                diag.pop("snippet", None)
                location = diag.get("range")
                if location:
                    location["filename"] = (
                        "/__RECORDED_ROOT__/terraform/" + location["filename"]
                    )
            (OUT / f"{name}.json").write_text(json.dumps(data, indent=2) + "\n")
            (OUT / f"{name}.init.txt").write_text(
                (init.stdout + init.stderr)
                .replace(str(root), "/__RECORDED_ROOT__")
                .replace(str(ROOT / ".cache/terraform-providers"), "<mirror>")
            )
            (OUT / f"{name}.main.tf").write_text(source)
            print(
                name,
                "init",
                init.exit_code,
                "validate",
                validate.exit_code,
                [
                    (d["summary"], d.get("range", {}).get("start", {}).get("line"))
                    for d in data["diagnostics"]
                ],
            )
    (OUT / "providers.tf").write_text(PROVIDERS)


asyncio.run(main())
