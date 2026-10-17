"""Bounded, version-correct schemas and symbol names; never include values."""

import json
import re
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path
from typing import Any

import hcl2
from lark.exceptions import LarkError

from app.validation.documents import PackageDocuments, blocks
from app.validation.provider_schema import (
    DEFAULT_INDEX,
    ProviderSchemaIndex,
    provider_requirements,
    select_version,
)
from app.validation.workspace import current_workspace


@lru_cache(maxsize=32)
def _cached_index(
    provider: str, version: str, directory: Path, stamp: tuple[int, ...]
) -> ProviderSchemaIndex:
    return ProviderSchemaIndex(provider, version, directory=directory)


def index_for(provider: str, version: str, directory: Path) -> ProviderSchemaIndex:
    stamp: list[int] = []
    for path in (directory / "manifest.json", directory / f"{provider}-{version}.json"):
        try:
            stat = path.stat()
            stamp.extend((stat.st_mtime_ns, stat.st_size))
        except OSError:
            stamp.extend((0, 0))
    return _cached_index(provider, version, directory, tuple(stamp))


def declarations(documents: PackageDocuments, module: str) -> list[dict[str, Any]]:
    result = []
    for doc in documents.documents.values():
        if str(Path(doc.path).parent) != module or doc.parse_error:
            continue
        spans = {}
        if doc.path.endswith(".tf"):
            try:
                for node in hcl2.parses_to_tree(doc.source).find_data("block"):
                    match = re.match(
                        r'(resource|data)\s+"([\w-]+)"\s+"([\w-]+)"',
                        doc.source[node.meta.start_pos : node.meta.end_pos],
                    )
                    if match:
                        spans[match.groups()] = (node.meta.line, node.meta.end_line)
            except LarkError:
                pass
        for kind in ("resource", "data"):
            for labels, body in blocks(doc.data, kind):
                entries = (
                    [(labels[1], body)] if kind == "resource" else list(body.items())
                )
                for name, attributes in entries:
                    if not isinstance(attributes, dict):
                        continue
                    result.append(
                        {
                            "kind": kind,
                            "type": labels[0],
                            "name": name,
                            "attributes": sorted(attributes),
                            "file": doc.path,
                            "lines": spans.get((kind, labels[0], name)),
                        }
                    )
        for kind in ("variable", "module"):
            for labels, body in blocks(doc.data, kind):
                result.append(
                    {
                        "kind": kind,
                        "name": labels[0],
                        "attributes": sorted(body) if kind == "module" else [],
                        "file": doc.path,
                    }
                )
        groups = doc.data.get("locals", []) if isinstance(doc.data, dict) else []
        for group in groups if isinstance(groups, list) else [groups]:
            if isinstance(group, dict):
                result.extend(
                    {"kind": "local", "name": name, "file": doc.path, "attributes": []}
                    for name in sorted(group)
                )
    return result


def brief_schema(schema: dict[str, Any]) -> dict[str, Any]:
    attributes = schema.get("attributes", {})
    return {
        "required": {
            n: a.get("type", a.get("nested_type"))
            for n, a in attributes.items()
            if a.get("required")
        },
        "optional": {
            n: a.get("type", a.get("nested_type"))
            for n, a in attributes.items()
            if a.get("optional")
        },
        "computed_only": {
            n: a.get("type", a.get("nested_type"))
            for n, a in attributes.items()
            if a.get("computed") and not a.get("optional") and not a.get("required")
        },
        "blocks": {
            n: {
                **{
                    k: v[k]
                    for k in ("nesting_mode", "min_items", "max_items")
                    if k in v
                },
                "required": {
                    a: b.get("type", b.get("nested_type"))
                    for a, b in v["block"].get("attributes", {}).items()
                    if b.get("required")
                },
                "arguments": sorted(v["block"].get("attributes", {})),
                "blocks": sorted(v["block"].get("block_types", {})),
            }
            for n, v in schema.get("block_types", {}).items()
        },
    }


def bounded_entries(entries: list[dict[str, Any]], limit: int) -> str:
    retained: list[dict[str, Any]] = []
    for entry in entries:
        text = json.dumps([*retained, entry], sort_keys=True, separators=(",", ":"))
        if len(text) <= limit:
            retained.append(entry)
        elif "schema" in entry:
            schema = entry["schema"]
            small = {
                **entry,
                "schema": {
                    "required": schema.get("required", {}),
                    "optional": sorted(schema.get("optional", {})),
                    "blocks": sorted(schema.get("blocks", {})),
                },
                "truncated": True,
            }
            if (
                len(
                    json.dumps(
                        [*retained, small], sort_keys=True, separators=(",", ":")
                    )
                )
                <= limit
            ):
                retained.append(small)
    return (
        json.dumps(retained, sort_keys=True, separators=(",", ":")) if retained else ""
    )


def nested_context(source: str, line: int, schema: dict[str, Any]) -> dict[str, Any]:
    """Find containing nested blocks without retaining raw diagnostic detail."""
    try:
        tree = hcl2.parses_to_tree(source)
        enclosing = sorted(
            (
                n
                for n in tree.find_data("block")
                if n.meta.line <= line <= n.meta.end_line
            ),
            key=lambda n: -(n.meta.end_pos - n.meta.start_pos),
        )
        path = []
        current = schema
        for node in enclosing:
            match = re.match(
                r"([A-Za-z_][\w-]*)\s*\{",
                source[node.meta.start_pos : node.meta.end_pos],
            )
            if match and match[1] in current.get("block_types", {}):
                path.append(match[1])
                current = current["block_types"][match[1]]["block"]
        token = re.match(
            r"\s*([A-Za-z_][\w-]*)\s*(?:=|\{)", source.splitlines()[line - 1]
        )
        names = sorted(
            set(current.get("attributes", {})) | set(current.get("block_types", {}))
        )
        return {
            "block_path": path,
            "schema": brief_schema(current),
            "nearest_arguments": get_close_matches(token[1], names, n=3, cutoff=0.5)
            if token
            else [],
        }
    except (LarkError, ValueError, TypeError, IndexError):
        return {}


def schema_context(
    path: str,
    files: dict[str, str],
    *,
    failures: list[dict[str, Any]] | None = None,
    findings: list[Any] | None = None,
    limit: int = 16000,
    directory: Path = DEFAULT_INDEX,
) -> str:
    module = str(Path(path).parent)
    documents = PackageDocuments.parse(files)
    requirements = provider_requirements(documents, module)
    workspace = current_workspace()
    declared = declarations(documents, module)
    targets = [d for d in declared if d.get("type") and d["file"] == path]
    # Finding-linked schemas take priority over other resources in the file.
    addresses = {str(getattr(f, "resource", "")) for f in findings or []}
    if addresses and any(f"{d['type']}.{d['name']}" in addresses for d in targets):
        targets = [d for d in targets if f"{d['type']}.{d['name']}" in addresses]
    targets.sort(
        key=lambda d: (
            f"{d['type']}.{d['name']}" not in addresses,
            d["type"],
            d["name"],
        )
    )
    linked_lines = [
        f["line_start"]
        for f in failures or []
        if f.get("file_path") == path and isinstance(f.get("line_start"), int)
    ]
    if linked_lines:
        targets.sort(
            key=lambda d: (
                not (
                    d.get("lines")
                    and any(
                        d["lines"][0] <= line <= d["lines"][1] for line in linked_lines
                    )
                )
            )
        )
    if any(getattr(f, "rule_id", "") == "CKV2_AWS_12" for f in findings or []):
        targets.insert(
            0,
            {
                "kind": "resource",
                "type": "aws_default_security_group",
                "name": "schema_guidance",
            },
        )
    if any(getattr(f, "rule_id", "") in {"CKV_AWS_144"} for f in findings or []):
        targets.insert(
            0,
            {
                "kind": "resource",
                "type": "aws_s3_bucket_replication_configuration",
                "name": "schema_guidance",
            },
        )
    entries: list[dict[str, Any]] = []
    seen = set()
    for target in targets:
        resource_type = target["type"]
        provider = resource_type.split("_")[0]
        requirement = requirements.get(provider, {})
        source = requirement.get("source", f"hashicorp/{provider}")
        if source not in {
            f"hashicorp/{provider}",
            f"registry.terraform.io/hashicorp/{provider}",
        }:
            continue
        version = (
            workspace.resolved.get(module, {}).get(provider) if workspace else None
        ) or select_version(provider, requirement.get("version", ""))
        if version is None or (resource_type, version, target["kind"]) in seen:
            continue
        seen.add((resource_type, version, target["kind"]))
        index = index_for(provider, version, directory)
        schema = index.resource_schema(
            resource_type, data_source=target["kind"] == "data"
        )
        entry: dict[str, Any] = {
            "provider": provider,
            "version": version,
            "kind": target["kind"],
            "type": resource_type,
        }
        if schema is not None:
            entry["schema"] = brief_schema(schema)
            if target.get("attributes") is not None:
                entry["required_missing"] = index.required_missing(
                    resource_type, dict.fromkeys(target["attributes"])
                )
            for failure in failures or []:
                if target.get("lines") and not (
                    target["lines"][0]
                    <= (failure.get("line_start") or 0)
                    <= target["lines"][1]
                ):
                    continue
                if failure.get("file_path") == path and isinstance(
                    failure.get("line_start"), int
                ):
                    detail = nested_context(files[path], failure["line_start"], schema)
                    if detail:
                        entry["diagnostic_context"] = detail
        else:
            entry["nearest_types"] = index.nearest_types(
                resource_type, data_source=target["kind"] == "data"
            )
            if index.resource_schema(resource_type, data_source=True):
                entry["exists_as_data_source"] = True
        entries.append(entry)
    if failures and any(
        "reference" in str(f.get("message", "")).lower()
        or "undeclared" in str(f.get("message", "")).lower()
        for f in failures
    ):
        entries.extend({"declared_symbol": d} for d in declared)
    else:
        entries.extend({"declared_symbol": d} for d in declared)
    return bounded_entries(entries, limit)


def generator_schema_context(
    limit: int = 6000,
    directory: Path = DEFAULT_INDEX,
    *,
    resource_types: tuple[str, ...] | None = None,
) -> str:
    entries: list[dict[str, Any]] = []
    names = (
        "aws_vpc",
        "aws_subnet",
        "aws_security_group",
        "aws_instance",
        "aws_s3_bucket",
        "aws_db_instance",
        "aws_lb",
        "aws_ecs_service",
    )
    for name in resource_types if resource_types is not None else names:
        profiles: dict[str, list[str]] = {}
        for version in ("5.100.0", "6.68.0"):
            index = index_for("aws", version, directory)
            schema = index.resource_schema(name)
            if schema:
                summary = brief_schema(schema)
                small = {
                    "required": summary["required"],
                    "blocks": {
                        n: {
                            k: v
                            for k, v in b.items()
                            if k in {"nesting_mode", "min_items", "max_items"}
                        }
                        for n, b in summary["blocks"].items()
                    },
                }
                profiles.setdefault(json.dumps(small, sort_keys=True), []).append(
                    version
                )
        entries.extend(
            {"type": name, "versions": versions, "schema": json.loads(raw)}
            for raw, versions in profiles.items()
        )
    return bounded_entries(entries, limit)
