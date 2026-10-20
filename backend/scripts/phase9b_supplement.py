"""One-time offline counts-only projection of author-cached proposal records."""

import argparse
import hashlib
import json
from pathlib import Path
from uuid import UUID

from app.domain.review import security_iterations
from scripts.phase9_common import ROOT, write_json
from scripts.secret_scan import matches

SOURCES = {
    "A3": "phase9f-a3-results",
    "smoke": "phase9h-smoke-results",
    "final set 1": "final-1-results",
    "final set 2": "final-2-results",
}


def project(source: Path, label: str) -> list[dict]:
    rows = []
    for path in sorted(source.glob("*.json")):
        if path.is_symlink():
            raise ValueError("Symlink inputs are forbidden")
        run_id = str(UUID(path.stem))
        raw = path.read_bytes()
        snapshot = json.loads(raw)
        for package in snapshot.get("packages", []):
            variant = package.get("variant")
            if variant not in {"cost", "performance", "security"}:
                raise ValueError("Invalid variant")
            fixes = [
                fix
                for iteration in security_iterations(package.get("security_report"))
                for fix in iteration.get("fixes", [])
                if fix.get("call_attempted") is not False
            ]
            rows.append(
                {
                    "benchmark": label,
                    "source_file": path.name,
                    "source_directory": source.name,
                    "source_sha256": hashlib.sha256(raw).hexdigest(),
                    "run_id": run_id,
                    "variant": variant,
                    "proposals": len(fixes),
                    "accepted": sum(fix.get("accepted") is True for fix in fixes),
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = [
        row
        for label, name in SOURCES.items()
        for row in project(ROOT / ".cache" / name, label)
    ]
    if not rows:
        raise ValueError("No cached inputs")
    content = json.dumps({"schema_version": 1, "records": rows}, indent=2) + "\n"
    if matches(content.encode(), set()):
        raise ValueError("Supplement secret scan failed")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_json(args.output_dir / "proposal-counts.json", json.loads(content))
    write_json(
        args.output_dir / "secret-scan.json",
        {"findings": 0, "scan_errors": 0, "files_scanned": 1},
    )
    print(f"Supplement: {len(rows)} package records; secret scan: 0 findings, 0 errors")


if __name__ == "__main__":
    main()
