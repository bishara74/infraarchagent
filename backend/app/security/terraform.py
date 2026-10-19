"""Module-local Terraform resources and source-preserving security edits."""

import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

import hcl2
from lark import Tree

from app.validation.documents import PackageDocuments, blocks
from app.validation.provider_schema import (
    DEFAULT_INDEX,
    provider_requirements,
    select_version,
)
from app.validation.schema_context import index_for
from app.validation.workspace import current_workspace


@dataclass(frozen=True)
class Resource:
    path: str
    type: str
    name: str
    body: dict[str, Any]

    @property
    def module(self) -> str:
        return str(PurePosixPath(self.path).parent)

    @property
    def address(self) -> str:
        return f"{self.type}.{self.name}"


def objects(value: Any) -> list[dict[str, Any]]:
    return [
        v
        for v in (value if isinstance(value, list) else [value])
        if isinstance(v, dict)
    ]


def reference(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"\$\{(aws_[\w]+\.[\w-]+)\.(?:id|arn|name|bucket)\}", value)
    return match[1] if match else None


class TerraformPackage:
    def __init__(self, files: dict[str, str]) -> None:
        self.files = files
        self.documents = PackageDocuments.parse(
            {
                p: s
                for p, s in files.items()
                if p.startswith("terraform/") and p.endswith((".tf", ".tf.json"))
            }
        )
        self.resources = [
            Resource(doc.path, labels[0], labels[1], body)
            for doc in self.documents.documents.values()
            if not doc.parse_error
            for labels, body in blocks(doc.data, "resource")
        ]

    def module_safe(self, module: str) -> bool:
        return not any(
            d.parse_error or not isinstance(d.data, dict)
            for d in self.documents.documents.values()
            if str(PurePosixPath(d.path).parent) == module
        )

    def get(self, module: str, address: str) -> Resource | None:
        found = [
            r for r in self.resources if r.module == module and r.address == address
        ]
        return found[0] if len(found) == 1 and self.module_safe(module) else None

    def resolve(self, module: str, value: Any) -> Resource | None:
        address = reference(value)
        return self.get(module, address) if address else None

    def version(self, module: str) -> str | None:
        requirement = provider_requirements(self.documents, module).get("aws", {})
        if requirement.get("source", "hashicorp/aws") not in {
            "hashicorp/aws",
            "registry.terraform.io/hashicorp/aws",
        }:
            return None
        workspace = current_workspace()
        return (
            workspace.resolved.get(module, {}).get("aws") if workspace else None
        ) or (select_version("aws", requirement.get("version", "")))

    def schema(self, resource: Resource) -> dict[str, Any] | None:
        version = self.version(resource.module)
        return (
            index_for("aws", version, DEFAULT_INDEX).resource_schema(resource.type)
            if version
            else None
        )


def render_fields(
    body: dict[str, Any], schema: dict[str, Any], indent: str = "  "
) -> str:
    result = []
    for name, value in body.items():
        if name == "depends_on":
            result.append(f"{indent}depends_on = [" + ", ".join(value) + "]\n")
            continue
        if name in schema.get("block_types", {}):
            nested = schema["block_types"][name]["block"]
            for item in objects(value):
                result.append(
                    f"{indent}{name} {{\n"
                    + render_fields(item, nested, indent + "  ")
                    + f"{indent}}}\n"
                )
        else:
            result.append(
                f"{indent}{name} = " + json.dumps(value, ensure_ascii=True) + "\n"
            )
    return "".join(result)


def fields_supported(body: dict[str, Any], schema: dict[str, Any]) -> bool:
    """Check emitted fields recursively; provider validation remains authoritative."""
    for name, value in body.items():
        if (
            name == "depends_on"
            and isinstance(value, list)
            and all(
                isinstance(v, str) and re.fullmatch(r"aws_[\w]+\.[\w-]+", v)
                for v in value
            )
        ):
            continue
        if name in schema.get("attributes", {}):
            attr = schema["attributes"][name]
            if not (attr.get("optional") or attr.get("required")):
                return False
        elif name in schema.get("block_types", {}):
            if not objects(value) or not all(
                fields_supported(v, schema["block_types"][name]["block"])
                for v in objects(value)
            ):
                return False
        else:
            return False
    return True


def edit_resource(
    files: dict[str, str],
    resource: Resource,
    updates: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, str]:
    """Replace only requested fields; preserve unrelated source and comments."""
    if not fields_supported(updates, schema):
        return files
    source = files[resource.path]
    if resource.path.endswith(".tf.json"):
        data = json.loads(source)
        data["resource"][resource.type][resource.name].update(updates)
        return {**files, resource.path: json.dumps(data, indent=2) + "\n"}
    tree = hcl2.parses_to_tree(source)
    for node in tree.find_data("block"):
        header = re.match(
            r'resource\s+"([\w-]+)"\s+"([\w-]+)"\s*\{',
            source[node.meta.start_pos : node.meta.end_pos],
        )
        if not header or header.groups() != (resource.type, resource.name):
            continue
        body = next(
            (c for c in node.children if isinstance(c, Tree) and c.data == "body"), None
        )
        if body is None:
            return files
        edits = []
        # Expanding a formerly single-line resource requires the first argument
        # to start on a new line too (Terraform rejects a mixed single-line body).
        if node.meta.line == node.meta.end_line:
            opening = node.meta.start_pos + header.end()
            edits.append((opening, opening, "\n"))
        for child in body.children:
            if not isinstance(child, Tree) or child.data not in {"attribute", "block"}:
                continue
            start, end = child.meta.start_pos, child.meta.end_pos
            field = re.match(r"([\w-]+)", source[start:end])
            if field and field[1] in updates:
                edits.append((start, end, ""))
        # Insert before the resource's closing brace, including empty bodies.
        edits.append(
            (
                node.meta.end_pos - 1,
                node.meta.end_pos - 1,
                "\n" + render_fields(updates, schema),
            )
        )
        for start, end, replacement in sorted(edits, reverse=True):
            source = source[:start] + replacement + source[end:]
        return {**files, resource.path: source}
    return files


def subnet_intent(package: TerraformPackage, subnet: Resource) -> str:
    """Classify proven routing; absence of association is never private evidence."""
    module = subnet.module
    tables = []
    uncertain_association = False
    for r in package.resources:
        if r.module != module or r.type != "aws_route_table_association":
            continue
        if reference(r.body.get("subnet_id")) == subnet.address:
            tables.append(
                None
                if any(k in r.body for k in ("count", "for_each"))
                else package.resolve(module, r.body.get("route_table_id"))
            )
        elif "subnet_id" in r.body and not reference(r.body["subnet_id"]):
            uncertain_association = True
    if uncertain_association:
        return "unresolvable"
    if not tables:
        vpc = reference(subnet.body.get("vpc_id"))
        if not vpc:
            return "unresolvable"
        for r in package.resources:
            if r.module != module:
                continue
            if (
                r.type == "aws_main_route_table_association"
                and reference(r.body.get("vpc_id")) == vpc
            ):
                tables.append(package.resolve(module, r.body.get("route_table_id")))
            if (
                r.type == "aws_default_route_table"
                and r.body.get("default_route_table_id")
                == "${" + vpc + ".default_route_table_id}"
            ):
                tables.append(r)
    if len(tables) != 1 or tables[0] is None:
        return "unresolvable"
    table = tables[0]
    if table.type not in {"aws_route_table", "aws_default_route_table"} or any(
        k in table.body or k in subnet.body for k in ("count", "for_each", "dynamic")
    ):
        return "unresolvable"
    raw_routes = table.body.get("route", [])
    if not isinstance(raw_routes, (list, dict)):
        return "unresolvable"
    if any(
        r.module == module
        and r.type == "aws_route"
        and (
            not reference(r.body.get("route_table_id"))
            or any(k in r.body for k in ("count", "for_each"))
        )
        for r in package.resources
    ):
        return "unresolvable"
    routes = objects(raw_routes)
    routes.extend(
        r.body
        for r in package.resources
        if r.module == module
        and r.type == "aws_route"
        and reference(r.body.get("route_table_id")) == table.address
    )
    unresolved = False
    for route in routes:
        if "gateway_id" in route:
            gateway = package.resolve(module, route["gateway_id"])
            if gateway and gateway.type == "aws_internet_gateway":
                return "public"
            if gateway is None:
                unresolved = True
        elif "nat_gateway_id" in route:
            nat = package.resolve(module, route["nat_gateway_id"])
            unresolved |= nat is None or nat.type != "aws_nat_gateway"
        elif not any(
            k in route
            for k in (
                "local_gateway_id",
                "transit_gateway_id",
                "vpc_peering_connection_id",
                "network_interface_id",
                "egress_only_gateway_id",
            )
        ):
            unresolved = True
    return "unresolvable" if unresolved else "private"
