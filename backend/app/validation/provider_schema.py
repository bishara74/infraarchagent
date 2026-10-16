"""Offline, version-bound provider schema queries. Never read application settings."""

import hashlib
import json
import logging
import re
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from app.validation.documents import PackageDocuments, mapping
from app.validation.tools import DEFAULT_MIRROR

logger = logging.getLogger(__name__)
DEFAULT_INDEX = DEFAULT_MIRROR.parent / "terraform-provider-schemas"
PINS = {
    "aws": ("5.100.0", "6.68.0"),
    "random": ("3.9.1",),
    "kubernetes": ("2.38.0",),
    "helm": ("2.17.0",),
    "tls": ("4.4.1",),
    "null": ("3.3.2",),
}


def compact_block(block: dict[str, Any]) -> dict[str, Any]:
    attrs = {}
    for name, value in block.get("attributes", {}).items():
        attrs[name] = {
            key: value[key]
            for key in ("type", "required", "optional", "computed", "sensitive")
            if key in value
        }
        if "nested_type" in value:
            nested = value["nested_type"]
            attrs[name]["nested_type"] = {
                "nesting_mode": nested["nesting_mode"],
                **compact_block(nested),
            }
    return {
        "attributes": attrs,
        "block_types": {
            name: {
                **{
                    key: value[key]
                    for key in ("nesting_mode", "min_items", "max_items")
                    if key in value
                },
                "block": compact_block(value["block"]),
            }
            for name, value in block.get("block_types", {}).items()
        },
    }


def matches_version(version: str, constraint: str) -> bool:
    """Terraform's numeric conjunctions; unknown syntax never guesses a version."""
    actual = tuple(int(n) for n in version.split("."))
    for clause in constraint.split(","):
        match = re.fullmatch(
            r"\s*(~>|>=|<=|!=|>|<|=)?\s*(\d+(?:\.\d+){0,2})\s*", clause
        )
        if not match:
            return False
        operator, raw = match.groups()
        parts = tuple(int(n) for n in raw.split("."))
        wanted = (*parts, *(0 for _ in range(3 - len(parts))))
        if operator == "~>":
            boundary = 0 if len(parts) < 3 else 1
            upper = list(wanted)
            upper[boundary] += 1
            upper[boundary + 1 :] = [0] * (2 - boundary)
            ok = wanted <= actual < tuple(upper)
        else:
            ok = {
                None: actual == wanted,
                "=": actual == wanted,
                ">=": actual >= wanted,
                "<=": actual <= wanted,
                ">": actual > wanted,
                "<": actual < wanted,
                "!=": actual != wanted,
            }[operator]
        if not ok:
            return False
    return True


def provider_requirements(
    documents: PackageDocuments, module: str
) -> dict[str, dict[str, str]]:
    result = {}
    for doc in documents.documents.values():
        if str(Path(doc.path).parent) != module or doc.parse_error:
            continue
        terraform = mapping(doc.data).get("terraform", [])
        for config in terraform if isinstance(terraform, list) else [terraform]:
            required = mapping(config).get("required_providers", [])
            for group in required if isinstance(required, list) else [required]:
                for name, body in mapping(group).items():
                    result[name] = {
                        "source": str(mapping(body).get("source", f"hashicorp/{name}")),
                        "version": str(mapping(body).get("version", "")),
                    }
    return result


class ProviderSchemaIndex:
    def __init__(
        self, provider: str, version: str, *, directory: Path = DEFAULT_INDEX
    ) -> None:
        self.provider, self.version = provider, version
        self.schemas: dict[str, Any] = {}
        self.available = False
        if provider not in PINS or version not in PINS[provider]:
            return
        try:
            manifest = json.loads((directory / "manifest.json").read_text())
            entry = manifest["providers"][f"{provider}/{version}"]
            raw = (directory / f"{provider}-{version}.json").read_bytes()
            if (
                manifest["format_version"] != 1
                or hashlib.sha256(raw).hexdigest() != entry["index_sha256"]
            ):
                raise ValueError("schema manifest mismatch")
            self.schemas = json.loads(raw)
            if not all(
                isinstance(self.schemas.get(key), dict)
                for key in ("resource_schemas", "data_source_schemas")
            ):
                raise ValueError("schema shape")
            self.available = True
        except (OSError, ValueError, KeyError, TypeError):
            self.schemas = {}
            logger.warning("provider schema index unavailable; grounding degraded")

    def resource_schema(
        self, name: str, *, data_source: bool = False
    ) -> dict[str, Any] | None:
        value = self.schemas.get(
            "data_source_schemas" if data_source else "resource_schemas", {}
        ).get(name)
        return value if isinstance(value, dict) else None

    def nearest_types(self, name: str, *, data_source: bool = False) -> list[str]:
        names = self.schemas.get(
            "data_source_schemas" if data_source else "resource_schemas", {}
        )
        return get_close_matches(name, sorted(names), n=3, cutoff=0.5)

    def nearest_arguments(self, name: str, argument: str) -> list[str]:
        schema = self.resource_schema(name) or {}
        return get_close_matches(
            argument,
            sorted(
                set(schema.get("attributes", {})) | set(schema.get("block_types", {}))
            ),
            n=3,
            cutoff=0.5,
        )

    def required_missing(self, name: str, given: dict[str, Any]) -> list[str]:
        schema = self.resource_schema(name) or {}
        return sorted(
            (
                {
                    key
                    for key, value in schema.get("attributes", {}).items()
                    if value.get("required")
                }
                | {
                    key
                    for key, value in schema.get("block_types", {}).items()
                    if value.get("min_items", 0) > 0
                }
            )
            - set(given)
        )


def select_version(provider: str, constraint: str) -> str | None:
    return next(
        (
            v
            for v in reversed(PINS.get(provider, ()))
            if not constraint or matches_version(v, constraint)
        ),
        None,
    )
