"""Replace capture-machine paths in recorded scanner JSON with a fixed root."""

import argparse
import json
from pathlib import Path

RECORDED_ROOT = "/__RECORDED_ROOT__"


def normalize_capture(raw: str, package_root: Path) -> str:
    root = str(package_root.resolve())
    data = json.loads(raw)
    if isinstance(data, dict) and "diagnostics" in data and "format_version" in data:
        for diagnostic in data["diagnostics"]:
            location = diagnostic.get("range")
            if location and not Path(location["filename"]).is_absolute():
                location["filename"] = (
                    RECORDED_ROOT
                    + "/terraform/"
                    + location["filename"].removeprefix("./")
                )
        return json.dumps(data, indent=2).replace(root, RECORDED_ROOT) + "\n"
    if (
        isinstance(data, dict)
        and data.get("ArtifactType") == "filesystem"
        and "SchemaVersion" in data
    ):
        data["ArtifactName"] = RECORDED_ROOT
        return json.dumps(data, indent=2).replace(root, RECORDED_ROOT) + "\n"
    if root not in raw:
        raise ValueError("capture does not contain the package root")
    return raw.replace(root, RECORDED_ROOT)


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
