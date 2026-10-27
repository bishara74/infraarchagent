"""D-65: compare unavailable evaluations without evaluating refused expressions."""

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any

from app.domain.validation import ValidationCheck
from app.validation.documents import PackageDocuments, blocks, walk

FILE_FUNCTION = re.compile(
    r"\b(?:file|filebase64|templatefile|fileset|fileexists|filemd5|filesha1|"
    r"filesha256|filesha512|filebase64sha256|filebase64sha512)\s*\("
)
REFERENCE = re.compile(
    r"\b(?:var\.[\w-]+|local\.[\w-]+|data\.[\w]+\.[\w-]+|"
    r"module\.[\w-]+|aws_[\w]+\.[\w-]+)"
)


def unavailable_signature(
    files: dict[str, str], checks: list[ValidationCheck]
) -> str | None:
    """Private fingerprint: complete inputs and symbolic dependencies, never values.

    A first-refusal diagnostic alone is insufficient: a second changed file call
    could otherwise hide behind it. No path is opened and no variable is resolved.
    """
    skipped = [
        c
        for c in checks
        if c.status == "skipped"
        or (c.check_id == "terraform.file_input" and c.status == "failed")
    ]
    if not skipped or any(c.status == "skipped" and not c.skip_reason for c in skipped):
        return None
    selected = {
        p: s
        for p, s in files.items()
        if p.startswith("terraform/") and p.endswith((".tf", ".tf.json", ".tfvars"))
    }
    documents = PackageDocuments.parse(selected)
    if any(d.parse_error for d in documents.documents.values()):
        return None
    modules = sorted({str(PurePosixPath(p).parent) for p in selected})
    reasons = sorted(
        (
            c.check_id,
            c.category,
            c.tool,
            c.skip_reason or "file_input_outside_package",
            str(PurePosixPath(c.file_path).parent)
            if c.file_path
            else "|".join(modules),
        )
        for c in skipped
    )
    definitions: dict[tuple[str, str], list[Any]] = {}
    configuration: list[Any] = []
    inputs = []
    for doc in documents.documents.values():
        module = str(PurePosixPath(doc.path).parent)
        if doc.path.endswith(".tfvars"):
            configuration.append((doc.path, doc.source))
        for kind in ("terraform", "provider", "module"):
            if isinstance(doc.data, dict) and kind in doc.data:
                configuration.append((module, kind, doc.data[kind]))
        for kind in ("variable", "resource", "module"):
            for labels, body in blocks(doc.data, kind):
                name = (
                    "var." + labels[0]
                    if kind == "variable"
                    else ".".join((kind, *labels))
                    if kind in {"data", "module"}
                    else ".".join(labels)
                )
                definitions.setdefault((module, name), []).append(body)
        for labels, named in blocks(doc.data, "data"):
            for name, body in named.items():
                definitions.setdefault(
                    (module, "data." + labels[0] + "." + name), []
                ).append(body)
        local_bodies = doc.data.get("locals", []) if isinstance(doc.data, dict) else []
        for body in local_bodies if isinstance(local_bodies, list) else [local_bodies]:
            if isinstance(body, dict):
                for name, value in body.items():
                    definitions.setdefault((module, "local." + name), []).append(value)
        for _, value in walk(doc.data):
            if (
                isinstance(value, str)
                and re.search(r"(?<!\$)\$\{", value)
                and FILE_FUNCTION.search(value)
            ):
                inputs.append((module, value))
    if any(c.skip_reason == "uninspectable_file_input" for c in skipped) and not inputs:
        return None
    dependencies: dict[tuple[str, str], list[Any]] = {}
    pending = [
        (module, ref) for module, value in inputs for ref in REFERENCE.findall(value)
    ]
    while pending:
        module, name = pending.pop()
        key = (module, name)
        if key in dependencies:
            continue
        if len(dependencies) >= 1024:
            return None
        values = definitions.get(key, [])
        dependencies[key] = values
        pending.extend((module, ref) for ref in REFERENCE.findall(json.dumps(values)))
    payload = {
        "reasons": reasons,
        "modules": modules,
        "configuration": sorted(
            configuration, key=lambda v: json.dumps(v, sort_keys=True)
        ),
        "inputs": sorted(inputs),
        "dependencies": sorted(
            (module, name, body) for (module, name), body in dependencies.items()
        ),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def same_unavailability(
    before: dict[str, str],
    candidate: dict[str, str],
    baseline: list[ValidationCheck],
    proposed: list[ValidationCheck],
) -> bool:
    original = unavailable_signature(before, baseline)
    return original is not None and original == unavailable_signature(
        candidate, proposed
    )
