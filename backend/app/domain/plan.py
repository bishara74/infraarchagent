"""Validated AWS deployment plan shared by later generator agents."""

import json
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

SLUG = r"^[a-z][a-z0-9-]{0,39}$"
MAX_PLAN_BYTES = 32 * 1024


class _PlanModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class StorageKind(StrEnum):
    RELATIONAL_DB = "relational_db"
    NOSQL_DB = "nosql_db"
    OBJECT_STORAGE = "object_storage"
    BLOCK_VOLUME = "block_volume"
    CACHE = "cache"
    OTHER = "other"


class FileType(StrEnum):
    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    HELM = "helm"
    NGINX = "nginx"
    JENKINS = "jenkins"
    ANSIBLE = "ansible"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    DOCKERFILE = "dockerfile"


class Service(_PlanModel):
    name: str = Field(pattern=SLUG)
    aws_service: str = Field(min_length=1, max_length=64)
    purpose: str = Field(max_length=300)


class Dependency(_PlanModel):
    source: str
    target: str
    description: str = Field(max_length=200)


class Network(_PlanModel):
    public_services: list[str]
    private_services: list[str]
    ingress: list[Annotated[str, Field(max_length=200)]]
    notes: str = Field(max_length=500)


class Storage(_PlanModel):
    name: str = Field(pattern=SLUG)
    kind: StorageKind
    aws_service: str = Field(min_length=1, max_length=64)
    attached_to: list[str]


class Ambiguity(_PlanModel):
    topic: str = Field(max_length=100)
    detail: str = Field(max_length=300)
    assumption: str = Field(max_length=300)


def _record(item: object) -> dict[str, Any]:
    return item if isinstance(item, dict) else {}


def _records(data: object) -> list[dict[str, Any]]:
    return [_record(item) for item in data] if isinstance(data, list) else []


def _strings(data: object) -> list[str]:
    return (
        [item for item in data if isinstance(item, str)]
        if isinstance(data, list)
        else []
    )


def _label(value: str) -> str:
    return repr(value[:80] + ("…" if len(value) > 80 else ""))


def _unknown_dependency_message(
    index: int,
    field: str,
    name: str,
    storage_names: set[str],
) -> str:
    prefix = f"dependencies.{index}.{field}: {_label(name)}"
    if name in storage_names:
        return (
            f"{prefix} is a storage entry, not a service; link it with "
            "storage[].attached_to instead of dependencies"
        )
    if name in FileType._value2member_map_:
        return (
            f"{prefix} is a deployment tool / file type, not a service; "
            "remove it from dependencies"
        )
    return f"dependencies.{index}.{field}: unknown service {_label(name)}"


def _cycle_errors(edges: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    visited: set[str] = set()
    active: list[str] = []

    def visit(node: str) -> None:
        if node in active:
            cycle = active[active.index(node) :] + [node]
            message = "dependency cycle: " + " -> ".join(cycle)
            if message not in errors:
                errors.append(message)
            return
        if node in visited:
            return
        active.append(node)
        for target in edges.get(node, []):
            visit(target)
        active.pop()
        visited.add(node)

    for name in sorted(edges):
        visit(name)
    return errors


def _consistency_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    services = _records(data.get("services"))
    names = _strings([item.get("name") for item in services])
    service_names = set(names)
    for name in sorted({name for name in names if names.count(name) > 1}):
        errors.append(f"services: duplicate name {_label(name)}")
    storage_names = _strings(
        [item.get("name") for item in _records(data.get("storage"))]
    )
    for name in sorted(
        {name for name in storage_names if storage_names.count(name) > 1}
    ):
        errors.append(f"storage: duplicate name {_label(name)}")
    storage_name_set = set(storage_names)

    edges: dict[str, list[str]] = {name: [] for name in service_names}
    for index, dependency in enumerate(_records(data.get("dependencies"))):
        source, target = dependency.get("source"), dependency.get("target")
        if isinstance(source, str) and source not in service_names:
            errors.append(
                _unknown_dependency_message(index, "source", source, storage_name_set)
            )
        if isinstance(target, str) and target not in service_names:
            errors.append(
                _unknown_dependency_message(index, "target", target, storage_name_set)
            )
        if isinstance(source, str) and source == target:
            errors.append(f"dependencies.{index}: service cannot depend on itself")
        elif (
            isinstance(source, str)
            and isinstance(target, str)
            and source in edges
            and target in edges
        ):
            edges[source].append(target)
    errors.extend(_cycle_errors(edges))

    network = _record(data.get("network"))
    public = _strings(network.get("public_services"))
    private = _strings(network.get("private_services"))
    for field, values in (("public_services", public), ("private_services", private)):
        for name in values:
            if name not in service_names:
                errors.append(f"network.{field}: unknown service {_label(name)}")
    for name in sorted(set(public) & set(private)):
        errors.append(f"network: service {_label(name)} is both public and private")
    for index, storage in enumerate(_records(data.get("storage"))):
        for name in _strings(storage.get("attached_to")):
            if name not in service_names:
                errors.append(
                    f"storage.{index}.attached_to: unknown service {_label(name)}"
                )

    file_types = _strings(data.get("file_types"))
    for kind in sorted({kind for kind in file_types if file_types.count(kind) > 1}):
        errors.append(f"file_types: duplicate value {_label(kind)}")
    if (
        isinstance(data.get("file_types"), list)
        and FileType.TERRAFORM not in file_types
    ):
        errors.append("file_types: terraform is required")
    try:
        size = len(
            json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )
    except (TypeError, ValueError):
        pass
    else:
        if size > MAX_PLAN_BYTES:
            errors.append(f"plan: serialized JSON exceeds {MAX_PLAN_BYTES} bytes")
    return errors


class DeploymentPlan(_PlanModel):
    cloud_provider: Literal["aws"]
    services: list[Service] = Field(min_length=1)
    dependencies: list[Dependency]
    network: Network
    storage: list[Storage]
    file_types: list[FileType]
    ambiguities: list[Ambiguity]

    @model_validator(mode="after")
    def consistent(self) -> "DeploymentPlan":
        errors = _consistency_errors(self.model_dump(mode="json"))
        if errors:
            raise ValueError("\n".join(errors))
        return self


def plan_validation_errors(data: dict[str, Any]) -> list[str]:
    """Return safe field-path messages for every assessable plan problem."""
    schema_errors: list[str] = []
    try:
        DeploymentPlan.model_validate(data)
    except ValidationError as error:
        for detail in error.errors(include_input=False):
            if detail["loc"]:
                path = ".".join(str(part) for part in detail["loc"])
                schema_errors.append(f"{path}: {detail['msg']}")
    return list(dict.fromkeys(schema_errors + _consistency_errors(data)))
