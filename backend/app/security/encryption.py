"""Conservative, resource-specific evidence for the cost AES256 exemption."""

import re
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

from app.domain.models import Violation
from app.validation.documents import PackageDocuments, blocks


def _objects(value: Any) -> list[dict[str, Any]]:
    entries = value if isinstance(value, list) else [value]
    return [entry for entry in entries if isinstance(entry, dict)]


def aes256_buckets(
    files: Mapping[str, str], *, documents: PackageDocuments | None = None
) -> set[tuple[str, str]]:
    """Prove a unique literal encryption configuration, never search source text."""
    documents = (
        documents
        if documents is not None
        else PackageDocuments.parse(
            {
                path: text
                for path, text in files.items()
                if path.startswith("terraform/") and path.endswith((".tf", ".tf.json"))
            }
        )
    )
    bad_modules = {
        str(PurePosixPath(doc.path).parent)
        for doc in documents.documents.values()
        if doc.parse_error
    }
    resources: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for doc in documents.documents.values():
        module = str(PurePosixPath(doc.path).parent)
        if module in bad_modules:
            continue
        for labels, body in blocks(doc.data, "resource"):
            resources.setdefault((module, ".".join(labels)), []).append(body)
    proven = set()
    for (module, address), buckets in resources.items():
        if not re.fullmatch(r"aws_s3_bucket\.[\w-]+", address) or len(buckets) != 1:
            continue
        bucket = buckets[0]
        if any(key in bucket for key in ("count", "for_each", "dynamic")):
            continue
        configs = _objects(bucket.get("server_side_encryption_configuration", []))
        for (scope, name), bodies in resources.items():
            if scope != module or not name.startswith(
                "aws_s3_bucket_server_side_encryption_configuration."
            ):
                continue
            for body in bodies:
                reference = body.get("bucket")
                if isinstance(reference, str) and reference in {
                    "${" + address + ".id}",
                    "${" + address + ".bucket}",
                }:
                    configs.append(body)
        if len(configs) != 1:
            continue
        config = configs[0]
        if any(key in config for key in ("count", "for_each", "dynamic")):
            continue
        rules = _objects(config.get("rule", []))
        if len(rules) != 1 or "dynamic" in rules[0]:
            continue
        defaults = _objects(rules[0].get("apply_server_side_encryption_by_default", []))
        if len(defaults) == 1 and defaults[0].get("sse_algorithm") == "AES256":
            proven.add((module, address))
    return proven


def bucket_is_aes256(violation: Violation, proven: set[tuple[str, str]]) -> bool:
    return (
        str(PurePosixPath(violation.file_path).parent),
        violation.resource,
    ) in proven
