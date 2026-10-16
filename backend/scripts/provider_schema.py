"""Export compact indexes using only installed Terraform and the offline mirror."""

import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scanners.runner import ProcessToolRunner, ToolFailure
from app.validation.provider_schema import DEFAULT_INDEX, PINS, compact_block
from app.validation.tools import DEFAULT_MIRROR


def encoded(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def atomic_write(path: Path, raw: bytes) -> None:
    temporary = path.with_suffix(f".tmp-{os.getpid()}")
    temporary.write_bytes(raw)
    temporary.replace(path)


async def export_schemas(
    mirror: Path = DEFAULT_MIRROR, destination: Path = DEFAULT_INDEX
) -> int:
    if not mirror.is_dir():
        print("Provider schema export unavailable: mirror_missing")
        return 1
    runner = ProcessToolRunner(120)
    manifest = {
        "format_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "providers": {},
    }
    destination.mkdir(parents=True, exist_ok=True)
    for provider, versions in PINS.items():
        for version in versions:
            with TemporaryDirectory(prefix="infraarch-schema-") as directory:
                root = Path(directory)
                (root / ".terraformrc").write_text(
                    "provider_installation { filesystem_mirror { path = "
                    + json.dumps(str(mirror.resolve()))
                    + " } }\n"
                )
                (root / "providers.tf").write_text(
                    "terraform {\n required_providers {\n"
                    f' {provider} = {{ source = "hashicorp/{provider}", '
                    f'version = "= {version}" }}\n'
                    " }\n}\n"
                )
                try:
                    init = await runner.run_command(
                        "terraform",
                        [
                            "terraform",
                            "init",
                            "-backend=false",
                            "-input=false",
                            "-get=false",
                            f"-plugin-dir={mirror}",
                            "-no-color",
                        ],
                        root,
                    )
                    if init.exit_code:
                        raise ValueError("init")
                    schema = await runner.run_command(
                        "terraform", ["terraform", "providers", "schema", "-json"], root
                    )
                    if schema.exit_code:
                        raise ValueError("schema")
                    raw = json.loads(schema.stdout)["provider_schemas"][
                        f"registry.terraform.io/hashicorp/{provider}"
                    ]
                    index = {
                        key: {
                            name: compact_block(value["block"])
                            for name, value in raw.get(key, {}).items()
                        }
                        for key in ("resource_schemas", "data_source_schemas")
                    }
                    output = encoded(index)
                    atomic_write(destination / f"{provider}-{version}.json", output)
                    manifest["providers"][f"{provider}/{version}"] = {
                        "index_sha256": hashlib.sha256(output).hexdigest(),
                        "schema_sha256": hashlib.sha256(
                            schema.stdout.encode()
                        ).hexdigest(),
                        "raw_bytes": len(schema.stdout.encode()),
                        "index_bytes": len(output),
                        "archive_sha256": hashlib.sha256(
                            (
                                mirror
                                / "registry.terraform.io"
                                / "hashicorp"
                                / provider
                                / (
                                    f"terraform-provider-{provider}_"
                                    f"{version}_linux_amd64.zip"
                                )
                            ).read_bytes()
                        ).hexdigest(),
                    }
                    print(f"{provider} {version}: {len(output)} index bytes")
                except (ToolFailure, ValueError, KeyError, TypeError):
                    print(f"Provider schema export failed: {provider} {version}")
                    return 1
    atomic_write(destination / "manifest.json", encoded(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(export_schemas()))
