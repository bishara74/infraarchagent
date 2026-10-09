"""The sole online provisioning command; never import application settings."""

import asyncio
import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scanners.runner import ProcessToolRunner, ToolFailure

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "tools/terraform-providers"
MIRROR = ROOT / ".cache/terraform-providers"
CONFIG_ROOTS = (CONFIG, CONFIG / "aws5")


def archive_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


async def mirror_providers() -> int:
    """Mirror exact pins first; derive lock hashes offline only after success."""
    MIRROR.mkdir(parents=True, exist_ok=True)
    runner = ProcessToolRunner(600)
    evidence: list[str] = []
    with TemporaryDirectory(prefix="infraarch-provider-provision-") as directory:
        for config in CONFIG_ROOTS:
            try:
                result = await runner.run_command(
                    "terraform",
                    [
                        "terraform",
                        "providers",
                        "mirror",
                        "-platform=linux_amd64",
                        str(MIRROR),
                    ],
                    config,
                    environment_dir=Path(directory),
                    allow_provider_download=True,
                )
            except ToolFailure as error:
                print(f"Provider download stopped: {error.category}", file=sys.stderr)
                return 1
            print(result.stdout, end="", flush=True)
            print(result.stderr, end="", file=sys.stderr, flush=True)
            if result.exit_code != 0:
                print(
                    "Provider download failed; no retry or workaround attempted.",
                    file=sys.stderr,
                )
                return 1
            evidence.append(result.stdout)
        for config in CONFIG_ROOTS:
            try:
                result = await runner.run_command(
                    "terraform",
                    [
                        "terraform",
                        "providers",
                        "lock",
                        f"-fs-mirror={MIRROR}",
                        "-platform=linux_amd64",
                    ],
                    config,
                    environment_dir=Path(directory),
                )
            except ToolFailure as error:
                print(
                    f"Offline lock recording failed: {error.category}", file=sys.stderr
                )
                return 1
            print(result.stdout, end="", flush=True)
            print(result.stderr, end="", file=sys.stderr, flush=True)
            if result.exit_code != 0:
                return 1
    archives = sorted(MIRROR.rglob("*.zip"))
    size = sum(path.stat().st_size for path in MIRROR.rglob("*") if path.is_file())
    lines = [
        "# Terraform provider mirror",
        "",
        "Exact pins cover both AWS majors in the original Phase 3 packages; random",
        "also appears in those packages. Kubernetes and Helm preserve their saved",
        "major-2 constraints. TLS and null provide the requested minimum coverage.",
        "",
        "Provision with `make providers` using existing Terraform. This is the only",
        "online step. Runtime init uses the mirror with network access disabled.",
        "Separate configuration roots allow AWS 5 and 6 in the same shared mirror.",
        "The mirror is gitignored; lock records and the hashes below are committed.",
        "",
        f"Captured UTC: {datetime.now(UTC).isoformat()}",
        f"Mirror file bytes: {size} ({size / 1024**2:.2f} MiB).",
        "",
        "| Archive | SHA-256 |",
        "|---|---|",
        *(
            f"| `{path.relative_to(MIRROR)}` | `{archive_hash(path)}` |"
            for path in archives
        ),
        "",
        "## Terraform signature-verification output",
        "",
        "```text",
        "\n".join(evidence).replace(str(MIRROR), ".cache/terraform-providers"),
        "```",
        "",
        "Lock records were derived with `terraform providers lock",
        "-fs-mirror=<mirror> -platform=linux_amd64`; that command uses local archives.",
    ]
    (CONFIG / "README.md").write_text("\n".join(lines) + "\n")
    print(
        f"Mirror size: {size} bytes ({size / 1024**2:.2f} MiB), "
        f"{len(archives)} archives."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(mirror_providers()))
