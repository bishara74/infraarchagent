"""Conservative, source-preserving FR-V-01 Terraform declaration repairs."""

import json
import re
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any

import hcl2
from hcl2.utils import SerializationOptions
from lark import Tree
from lark.exceptions import LarkError

from app.validation.documents import (
    blocks,
    hcl_reference_locations,
    json_reference_locations,
)

DATA_SOURCES = {
    "aws_availability_zones": '  state = "available"\n',
    "aws_caller_identity": "",
    "aws_region": "",
    "aws_partition": "",
}
SECRET_NAME = re.compile(r"password|secret|token|credential|private[_-]?key", re.I)


def repair_terraform(
    files: dict[str, str],
) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Skip a module if any declaration cannot be safely inspected."""
    result = dict(files)
    repairs: list[dict[str, str]] = []
    modules: dict[str, list[str]] = defaultdict(list)
    for path in sorted(files):
        if path.startswith("terraform/") and path.endswith((".tf", ".tf.json")):
            modules[str(PurePosixPath(path).parent)].append(path)
    for module, paths in sorted(modules.items()):
        trees: dict[str, Tree[Any]] = {}
        variables: set[str] = set()
        data_sources: set[str] = set()
        references: set[str] = set()
        try:
            for path in paths:
                # JSON declarations must not be overlooked when adding HCL inputs.
                if path.endswith(".tf.json"):
                    data = json.loads(files[path])
                    variables.update(data.get("variable", {}))
                    for kind, entries in data.get("data", {}).items():
                        data_sources.update(f"{kind}.{name}" for name in entries)
                    references.update(
                        json_reference_locations(files[path], include_data=True)
                    )
                    continue
                tree = hcl2.parses_to_tree(files[path])
                trees[path] = tree
                references.update(hcl_reference_locations(tree, include_data=True))
                data = hcl2.serialize(
                    hcl2.transform(tree),
                    serialization_options=SerializationOptions(
                        strip_string_quotes=True,
                        with_comments=False,
                        explicit_blocks=False,
                    ),
                )
                variables.update(labels[0] for labels, _ in blocks(data, "variable"))
                data_sources.update(
                    f"{labels[0]}.{name}"
                    for labels, body in blocks(data, "data")
                    for name in body
                )
        except (LarkError, ValueError, TypeError, AttributeError):
            continue
        seen: set[tuple[str, str]] = set()
        for path, tree in trees.items():
            edits = []
            for node in tree.find_data("block"):
                source = files[path][node.meta.start_pos : node.meta.end_pos]
                match = re.match(r'variable\s+"([\w-]+)"\s*\{', source)
                if match is None:
                    continue
                name = match.group(1)
                key = (name, source)
                if key in seen:
                    edits.append((node.meta.start_pos, node.meta.end_pos))
                    repairs.append(
                        {"file": path, "kind": "duplicate_variable", "name": name}
                    )
                else:
                    seen.add(key)
            for start, end in reversed(sorted(edits)):
                result[path] = result[path][:start] + result[path][end:]
        additions = []
        for ref in sorted(references):
            parts = ref.split(".")
            name = parts[1]
            if parts[0] == "var" and name not in variables:
                sensitive = "  sensitive = true\n" if SECRET_NAME.search(name) else ""
                additions.append(
                    f'variable "{name}" {{\n'
                    f'  description = "Input for {name}"\n{sensitive}}}\n'
                )
                variables.add(name)
                repairs.append(
                    {
                        "file": f"{module}/variables.tf",
                        "kind": "missing_variable",
                        "name": name,
                    }
                )
            elif parts[0] == "data" and len(parts) == 3:
                kind, label = parts[1:]
                identity = f"{kind}.{label}"
                if kind in DATA_SOURCES and identity not in data_sources:
                    additions.append(
                        f'data "{kind}" "{label}" {{\n{DATA_SOURCES[kind]}}}\n'
                    )
                    data_sources.add(identity)
                    repairs.append(
                        {
                            "file": f"{module}/variables.tf",
                            "kind": "missing_data_source",
                            "name": identity,
                        }
                    )
        if additions:
            target = f"{module}/variables.tf"
            result[target] = result.get(target, "") + "\n\n" + "\n".join(additions)
    return result, repairs
