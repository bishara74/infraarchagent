"""Bounded, version-correct schemas and symbol names; never include values."""

import json
import re
from copy import deepcopy
from dataclasses import dataclass
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


@dataclass(frozen=True)
class SchemaGuidance:
    text: str
    omitted_required: tuple[str, ...] = ()
    omitted_conditional: tuple[str, ...] = ()

    @property
    def overflow(self) -> bool:
        return bool(self.omitted_required or self.omitted_conditional)


def required_shape(shape: dict[str, Any], *, conditional: bool) -> dict[str, Any]:
    """Minimal recursive requirements; optional ancestors never become mandatory."""
    result: dict[str, Any] = {"required": shape.get("required", {}), "blocks": {}}
    for name, block in shape.get("blocks", {}).items():
        child = required_shape(block, conditional=conditional)
        mandatory = block.get("min", 0) > 0
        if mandatory or (conditional and (child["required"] or child["blocks"])):
            result["blocks"][name] = {
                **{key: block[key] for key in ("mode", "min", "max") if key in block},
                **({"if_used": True} if not mandatory else {}),
                **child,
            }
    return result


def _version_entry(name: str, profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    def shared(shapes: list[dict[str, Any]]) -> dict[str, Any]:
        common = {}
        for key, value in shapes[0].items():
            if not all(key in shape for shape in shapes):
                continue
            values = [shape[key] for shape in shapes]
            if all(isinstance(v, dict) for v in values):
                common[key] = shared(values)
            elif all(v == value for v in values):
                common[key] = value
        return common

    def difference(shape: dict[str, Any], common: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in shape.items():
            if key not in common:
                result[key] = value
            elif isinstance(value, dict):
                extra = difference(value, common[key])
                if extra:
                    result[key] = extra
        return result

    common = shared(list(profiles.values()))
    differences = {
        version: difference(shape, common) for version, shape in profiles.items()
    }
    entry: dict[str, Any] = {"type": name, "versions": list(profiles), "schema": common}
    if any(values for diff in differences.values() for values in diff.values()):
        entry["version_schema"] = {
            version: {section: values for section, values in diff.items() if values}
            for version, diff in differences.items()
            if any(diff.values())
        }
    return entry


def generator_schema_guidance(
    limit: int = 6000,
    directory: Path = DEFAULT_INDEX,
    *,
    resource_types: tuple[str, ...] | None = None,
) -> SchemaGuidance:
    names = (
        resource_types
        if resource_types is not None
        else (
            "aws_vpc",
            "aws_subnet",
            "aws_security_group",
            "aws_instance",
            "aws_s3_bucket",
            "aws_db_instance",
            "aws_lb",
            "aws_ecs_service",
        )
    )
    profiles_by_type: dict[str, dict[str, dict[str, Any]]] = {}
    for name in dict.fromkeys(names):
        profiles = {}
        for version in ("5.100.0", "6.68.0"):
            schema = index_for("aws", version, directory).resource_schema(name)
            if schema:
                profiles[version] = generation_shape(schema)
        if profiles:
            profiles_by_type[name] = profiles
    retained: list[dict[str, Any]] = []
    omitted_required, omitted_conditional = [], []

    def encoded() -> str:
        return json.dumps(retained, separators=(",", ":")) if retained else ""

    # A resource's required core is atomic, including every provider version.
    for name, profiles in profiles_by_type.items():
        core = _version_entry(
            name,
            {
                version: required_shape(shape, conditional=False)
                for version, shape in profiles.items()
            },
        )
        core["truncated"] = False
        retained.append(core)
        if len(encoded()) > limit:
            retained.pop()
            omitted_required.append(name)
    for index, entry in enumerate(retained):
        profiles = profiles_by_type[entry["type"]]
        candidate = _version_entry(
            entry["type"],
            {
                version: required_shape(shape, conditional=True)
                for version, shape in profiles.items()
            },
        )
        candidate["truncated"] = False
        retained[index] = candidate
        if len(encoded()) > limit:
            retained[index] = entry
            omitted_conditional.append(entry["type"])

    # Optional content is incremental and round-robin across types. Conditional
    # cores remain atomic; their optional ancestor labels survive enrichment.
    full_entries = {
        name: _version_entry(name, profiles)
        for name, profiles in profiles_by_type.items()
    }
    for entry in retained:
        fields = {
            version: {
                section: sorted(values)
                for section, values in diff.items()
                if section == "optional" and values
            }
            for version, diff in full_entries[entry["type"]]
            .get("version_schema", {})
            .items()
            if diff.get("optional")
        }
        if fields:
            entry["version_fields"] = fields
            if len(encoded()) > limit:
                del entry["version_fields"]

    def additions(
        full: dict[str, Any],
        present: dict[str, Any],
        section: str,
        path: tuple[str, ...] = (),
    ) -> list[tuple[tuple[str, ...], Any]]:
        result = []
        if section == "optional":
            for name, value in full.get("optional", {}).items():
                if name not in present.get("optional", {}):
                    result.append(((*path, "optional", name), value))
        for name, block in full.get("blocks", {}).items():
            existing = present.get("blocks", {}).get(name)
            if existing is not None:
                result.extend(
                    additions(block, existing, section, (*path, "blocks", name))
                )
            elif (
                section == "blocks"
                and not required_shape(block, conditional=True)["required"]
                and not required_shape(block, conditional=True)["blocks"]
            ):
                result.append(((*path, "blocks", name), block))
        return result

    def put(entry: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
        target = entry
        for key in path[:-1]:
            target = target.setdefault(key, {})
        target[path[-1]] = deepcopy(value)

    for section in ("optional", "blocks"):
        queues = []
        for entry in retained:
            # Project full profiles using the *retained* required-core partition.
            # This avoids losing common optional fields in version-specific blocks.
            profiles = profiles_by_type[entry["type"]]
            queue = []
            for version, shape in profiles.items():
                merged = deepcopy(entry["schema"])
                _merge(merged, entry.get("version_schema", {}).get(version, {}))
                for path, value in additions(shape, merged, section):
                    common = all(_at(p, path) == value for p in profiles.values())
                    prefix = (
                        ("schema",)
                        if common and _at(entry["schema"], path[:-2]) is not None
                        else ("version_schema", version)
                    )
                    queue.append(((*prefix, *path), value))
            queue.sort(
                key=lambda item: (
                    GUIDANCE_PRIORITY.index(item[0][-1])
                    if item[0][-1] in GUIDANCE_PRIORITY
                    else len(GUIDANCE_PRIORITY),
                    item[0],
                )
            )
            queues.append(
                (entry, list(dict((path, value) for path, value in queue).items()))
            )
        while any(queue for _, queue in queues):
            for entry, queue in queues:
                if not queue:
                    continue
                path, value = queue.pop(0)
                before = deepcopy(entry)
                put(entry, path, value)
                if len(encoded()) > limit:
                    entry.clear()
                    entry.update(before)
    for entry in retained:
        complete = True
        for version, shape in profiles_by_type[entry["type"]].items():
            merged = deepcopy(entry["schema"])
            _merge(merged, entry.get("version_schema", {}).get(version, {}))
            complete &= _contains(merged, shape)
        entry["truncated"] = not complete
    return SchemaGuidance(
        encoded(), tuple(omitted_required), tuple(omitted_conditional)
    )


def _at(shape: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = shape
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def _merge(target: dict[str, Any], extra: dict[str, Any]) -> None:
    for key, value in extra.items():
        if isinstance(value, dict):
            _merge(target.setdefault(key, {}), value)
        else:
            target[key] = deepcopy(value)


def _contains(actual: Any, wanted: Any) -> bool:
    if isinstance(wanted, dict):
        return isinstance(actual, dict) and all(
            (isinstance(value, dict) and not value)
            or (key in actual and _contains(actual[key], value))
            for key, value in wanted.items()
        )
    return bool(actual == wanted)


def generator_schema_context(
    limit: int = 6000,
    directory: Path = DEFAULT_INDEX,
    *,
    resource_types: tuple[str, ...] | None = None,
) -> str:
    return generator_schema_guidance(
        limit, directory, resource_types=resource_types
    ).text


GUIDANCE_PRIORITY = (
    "db_name",
    "backup_retention_period",
    "multi_az",
    "storage_encrypted",
    "internal",
    "load_balancer_type",
    "map_public_ip_on_launch",
    "subnet_id",
    "subnet_ids",
    "vpc_id",
    "security_groups",
    "network_configuration",
    "assign_public_ip",
    "cidr_block",
    "gateway_id",
    "port",
    "protocol",
    "certificate_arn",
    "ssl_policy",
    "drop_invalid_header_fields",
)


def generation_shape(schema: dict[str, Any], depth: int = 0) -> dict[str, Any]:
    def order(name: str) -> tuple[int, str]:
        return (
            GUIDANCE_PRIORITY.index(name)
            if name in GUIDANCE_PRIORITY
            else len(GUIDANCE_PRIORITY),
            name,
        )

    attrs = schema.get("attributes", {})
    return {
        "required": {
            n: a.get("type", a.get("nested_type"))
            for n, a in sorted(attrs.items())
            if a.get("required")
        },
        "optional": {
            n: attrs[n].get("type", attrs[n].get("nested_type"))
            for n in sorted(attrs, key=order)
            if attrs[n].get("optional")
        },
        "blocks": {
            n: {
                "mode": b["nesting_mode"],
                **({"min": b["min_items"]} if b.get("min_items") else {}),
                **({"max": b["max_items"]} if b.get("max_items") else {}),
                **generation_shape(b["block"], depth + 1),
            }
            for n, b in sorted(
                schema.get("block_types", {}).items(), key=lambda item: order(item[0])
            )
        },
    }
