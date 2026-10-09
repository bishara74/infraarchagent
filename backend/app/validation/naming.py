"""Explainable naming warnings; no fuzzy scoring or inferred release names."""

import ipaddress
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from app.domain.plan import DeploymentPlan, FileType, Service
from app.domain.validation import ValidationCheck
from app.validation.documents import (
    Document,
    PackageDocuments,
    blocks,
    code_text,
    mapping,
    normalize_name,
)
from app.validation.references import inventory_groups
from app.validation.structure import finding

SUFFIXES = {
    "service",
    "services",
    "server",
    "servers",
    "svc",
    "deployment",
    "upstream",
    "job",
}
INFRA_NAMES = {
    "all",
    "ungrouped",
    "localhost",
    "kubernetes",
    "kube-system",
    "node",
    "node-exporter",
    "kube-state-metrics",
    "alertmanager",
    "blackbox",
    "aws",
    "default",
}
COMPUTE = {"ecs", "ec2", "eks", "lambda", "kubernetes", "elasticbeanstalk", "fargate"}
TF_APPLICATION_PREFIXES = {
    "aws_instance",
    "aws_ecs_service",
    "aws_ecs_task_definition",
    "aws_lambda_function",
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_s3_bucket",
    "aws_dynamodb_table",
    "aws_elasticache_cluster",
    "helm_release",
    "kubernetes_deployment",
    "kubernetes_service",
}
TF_NAMES = {
    "name",
    "name_prefix",
    "bucket",
    "db_name",
    "identifier",
    "cluster_identifier",
    "function_name",
}


def embeds(name: str, expected: str) -> bool:
    normalized = normalize_name(name)
    wanted = normalize_name(expected)
    return (
        normalized == wanted
        or re.search(r"(?:^|-)" + re.escape(wanted) + r"(?:-|$)", normalized)
        is not None
    )


def base_name(name: str) -> str:
    tokens = normalize_name(name).split("-")
    while tokens and tokens[-1] in SUFFIXES:
        tokens.pop()
    return "-".join(tokens)


def application_services(plan: DeploymentPlan) -> list[Service]:
    return [
        service
        for service in plan.services
        if service.aws_service.lower() in COMPUTE
        and not re.search(
            r"control[ -]?plane|managed kubernetes control|cluster$",
            service.purpose + " " + service.name,
            re.IGNORECASE,
        )
    ]


@dataclass(frozen=True)
class Entity:
    name: str
    document: Document
    artifact: FileType
    service_like: bool = True
    workload: bool = False


def named_entities(package: PackageDocuments, plan: DeploymentPlan) -> list[Entity]:
    entities = []
    plan_names = [service.name for service in plan.services] + [
        storage.name for storage in plan.storage
    ]

    def add(
        name: object,
        doc: Document,
        kind: FileType,
        *,
        service_like: bool = True,
        workload: bool = False,
    ) -> None:
        if not isinstance(name, str) or not name or len(name) > 200:
            return
        if "${" in name and not any(embeds(name, wanted) for wanted in plan_names):
            return
        entities.append(Entity(name, doc, kind, service_like, workload))

    for doc in package.documents.values():
        if doc.parse_error:
            continue
        kind = doc.kind
        if kind == FileType.KUBERNETES:
            for item in doc.yaml_documents:
                data = mapping(item.data)
                if data.get("kind") in {"Deployment", "StatefulSet", "Service"}:
                    add(
                        mapping(data.get("metadata")).get("name"),
                        doc,
                        kind,
                        workload=data.get("kind") in {"Deployment", "StatefulSet"},
                    )
        elif kind == FileType.HELM and PurePosixPath(doc.path).name == "Chart.yaml":
            add(mapping(doc.data).get("name"), doc, kind)
        elif kind == FileType.TERRAFORM:
            for labels, body in blocks(doc.data, "resource"):
                resource = labels[0]
                for key in TF_NAMES:
                    if key in body:
                        add(
                            body[key],
                            doc,
                            FileType.HELM
                            if resource == "helm_release" and key == "name"
                            else kind,
                            service_like=resource in TF_APPLICATION_PREFIXES,
                        )
                tags = body.get("tags", {})
                for tag in tags if isinstance(tags, list) else [tags]:
                    for key, value in mapping(tag).items():
                        if str(key).lower() in {"name", "application", "service"}:
                            add(
                                value,
                                doc,
                                kind,
                                service_like=resource in TF_APPLICATION_PREFIXES,
                            )
        elif kind == FileType.ANSIBLE:
            groups, present = inventory_groups(
                PackageDocuments({doc.path: doc.source}, {doc.path: doc})
            )
            if present:
                for name in sorted(groups - {"all", "ungrouped"}):
                    add(name, doc, kind)
            elif isinstance(doc.data, list):
                for play in doc.data:
                    hosts = mapping(play).get("hosts")
                    if isinstance(hosts, str) and not any(
                        char in hosts for char in "{{*~"
                    ):
                        for name in re.split(r"[:,&!\s]+", hosts):
                            add(name, doc, kind)
        elif kind == FileType.NGINX:
            text = code_text(doc.source, hash_comments=True, slash_comments=False)
            for name in re.findall(r"\bupstream\s+([\w.-]+)\s*\{", text):
                add(name, doc, kind)
        elif kind == FileType.PROMETHEUS:
            configs = mapping(doc.data).get("scrape_configs", [])
            for config in configs if isinstance(configs, list) else []:
                add(mapping(config).get("job_name"), doc, kind)
                static = mapping(config).get("static_configs", [])
                for group in static if isinstance(static, list) else []:
                    targets = mapping(group).get("targets", [])
                    for target in targets if isinstance(targets, list) else []:
                        if not isinstance(target, str):
                            continue
                        host = None
                        try:
                            host = urlsplit("//" + target).hostname
                            if host:
                                ipaddress.ip_address(host)
                            continue
                        except ValueError:
                            pass
                        if host:
                            add(host.split(".")[0], doc, kind)
    return sorted(
        entities,
        key=lambda entity: (entity.artifact.value, entity.document.path, entity.name),
    )


def naming_checks(
    package: PackageDocuments, plan: DeploymentPlan
) -> list[ValidationCheck]:
    entities = named_entities(package, plan)
    names = [service.name for service in plan.services] + [
        storage.name for storage in plan.storage
    ]
    checks = []
    for entity in entities:
        if not entity.service_like or normalize_name(entity.name) in INFRA_NAMES:
            continue
        if any(embeds(entity.name, name) for name in names):
            continue
        peers = [
            other
            for other in entities
            if other.artifact != entity.artifact
            and other.service_like
            and normalize_name(other.name) not in INFRA_NAMES
        ]
        if any(base_name(entity.name) == base_name(other.name) for other in peers):
            continue
        peer = next(
            (other for other in peers if other.artifact == FileType.TERRAFORM), None
        )
        message = f"Unknown service-like name in {entity.document.path}"
        if peer is not None and entity.artifact == FileType.ANSIBLE:
            message = (
                f"Service naming mismatch between {entity.document.path} "
                f"and {peer.document.path}"
            )
        checks.append(
            finding(
                entity.document,
                "naming.unknown_service",
                True,
                message,
                token=entity.name,
                status="warning",
                category="naming",
            )
        )
    expected = application_services(plan)
    # Kubernetes workloads, Nginx routes and Prometheus jobs/targets can statically
    # represent application services. A Helm chart may aggregate several services;
    # Ansible applies only to EC2 hosts; Terraform covers services and storage.
    for kind in (
        FileType.TERRAFORM,
        FileType.KUBERNETES,
        FileType.NGINX,
        FileType.PROMETHEUS,
        FileType.ANSIBLE,
    ):
        docs = package.of_kind(kind)
        if kind not in plan.file_types or not docs:
            continue
        candidates = [
            entity
            for entity in entities
            if entity.artifact == kind
            and (kind != FileType.KUBERNETES or entity.workload)
        ]
        wanted = (
            names
            if kind == FileType.TERRAFORM
            else [
                service.name
                for service in expected
                if kind != FileType.ANSIBLE or service.aws_service.lower() == "ec2"
            ]
        )
        for name in wanted:
            if not any(embeds(entity.name, name) for entity in candidates):
                checks.append(
                    finding(
                        docs[0],
                        "naming.missing_service",
                        True,
                        f"Expected plan entity '{name}' absent from {kind.value} names",
                        status="warning",
                        category="naming",
                    )
                )
    return checks
