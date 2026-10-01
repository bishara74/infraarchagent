"""Replace capture-machine paths in recorded scanner JSON with a fixed root."""

import argparse
import json
from pathlib import Path

RECORDED_ROOT = "/__RECORDED_ROOT__"


def normalize_capture(raw: str, package_root: Path) -> str:
    root = str(package_root.resolve())
    if root not in raw:
        raise ValueError("capture does not contain the package root")
    normalized = raw.replace(root, RECORDED_ROOT)
    json.loads(normalized)
    return normalized


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_root", type=Path)
    parser.add_argument("captured_json", type=Path)
    parser.add_argument("fixture_json", type=Path)
    args = parser.parse_args()
    normalized = normalize_capture(
        args.captured_json.read_text(encoding="utf-8"), args.package_root
    )
    args.fixture_json.write_text(normalized, encoding="utf-8")


if __name__ == "__main__":
    main()
