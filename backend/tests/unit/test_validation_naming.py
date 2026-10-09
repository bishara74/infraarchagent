import json

import pytest

from app.domain.plan import Service
from app.validation.documents import PackageDocuments
from app.validation.naming import (
    application_services,
    embeds,
    named_entities,
    naming_checks,
)
from tests.unit.test_generators import plan


@pytest.mark.req("FR-V-02")
@pytest.mark.parametrize(
    ("name,expected,match"),
    [
        (("WEB_service"), ("web"), True),
        (("prefix.web-deployment"), ("web"), True),
        (("webserver"), ("web"), False),
        (("web-servers"), ("web"), True),
        (("app-service-10"), ("app-service-1"), False),
        (("APP_SERVICE_1.server"), ("app-service-1"), True),
    ],
)
def test_normalization_and_token_boundaries(name, expected, match):
    assert embeds(name, expected) == match


@pytest.mark.req("FR-V-02", "FR-V-04")
def test_terraform_ansible_mismatch_names_both_files_and_only_warns():
    files = {
        ("terraform/app.tf"): (
            'resource "aws_instance" "app" { tags = { Name = "app-service-1" } }'
        ),
        ("ansible/playbook.yaml"): ("- hosts: web-servers"),
    }
    deployment = plan("ansible").model_copy(
        update={
            ("services"): [
                Service(name=("app-service-1"), aws_service=("ec2"), purpose=("App"))
            ]
        }
    )
    checks = naming_checks(PackageDocuments.parse(files), deployment)
    check = next(
        c
        for c in checks
        if c.check_id == ("naming.unknown_service")
        and c.file_path == ("ansible/playbook.yaml")
    )
    assert ("terraform/app.tf") in check.message and (
        "ansible/playbook.yaml"
    ) in check.message
    assert all(c.status == "warning" for c in checks)


@pytest.mark.req("FR-V-02")
def test_missing_application_workload_and_infrastructure_exclusion():
    deployment = plan("kubernetes").model_copy(
        update={
            ("services"): [
                Service(
                    name=("eks-cluster"),
                    aws_service=("eks"),
                    purpose=("Managed Kubernetes control plane"),
                ),
                Service(
                    name=("web"),
                    aws_service=("eks"),
                    purpose=("Application microservice"),
                ),
            ]
        }
    )
    assert [s.name for s in application_services(deployment)] == ["web"]
    files = {
        ("terraform/main.tf"): (
            'resource "aws_eks_cluster" "cluster" { name = "eks-cluster" }'
        ),
        ("k8s/service.yaml"): ("apiVersion: v1\nkind: Service\nmetadata: {name: web}"),
    }
    checks = naming_checks(PackageDocuments.parse(files), deployment)
    missing = [
        c
        for c in checks
        if c.check_id == ("naming.missing_service") and c.file_path.startswith("k8s/")
    ]
    assert len(missing) == 1 and "'web'" in missing[0].message
    assert not any("eks-cluster" in c.message for c in missing)


@pytest.mark.req("FR-V-02")
def test_normalized_workload_matches_and_unknown_service_warns():
    files = {
        ("terraform/main.tf"): (
            'resource "aws_ecs_service" "web" { name = "WEB_service" }'
        ),
        ("k8s/deployment.yaml"): (
            "apiVersion: apps/v1\nkind: Deployment\nmetadata: {name: WEB_service}"
        ),
    }
    assert not naming_checks(PackageDocuments.parse(files), plan("kubernetes"))
    files[("k8s/deployment.yaml")] = files[("k8s/deployment.yaml")].replace(
        ("WEB_service"), ("wrong")
    )
    checks = naming_checks(PackageDocuments.parse(files), plan("kubernetes"))
    assert {("naming.unknown_service"), ("naming.missing_service")} <= {
        c.check_id for c in checks
    }


@pytest.mark.req("FR-V-02")
def test_collect_all_named_entity_categories_and_literal_release_only():
    files = {
        ("terraform/main.tf"): (
            'resource "helm_release" "literal" { name = "w'
            'eb-release" }\nresource "helm_release" "dynami'
            'c" { name = var.release }\nresource "aws_insta'
            'nce" "app" { tags = { Name = "web" } }'
        ),
        ("k8s/deployment.yaml"): (
            "apiVersion: apps/v1\nkind: StatefulSet\nmetadata: {name: web}"
        ),
        "helm/web/Chart.yaml": "name: web",
        "helm/web/templates/file.yaml": "{{ .Release.Name }}",
        "ansible/inventory.yaml": "all: {children: {web: {hosts: {host: {}}}}}",
        "nginx/site.conf": "upstream web { server 127.0.0.1; }\nserver {}",
        ("monitoring/prometheus/prometheus.yaml"): json.dumps(
            {
                ("scrape_configs"): [
                    {
                        ("job_name"): ("web"),
                        ("static_configs"): [
                            {("targets"): [("web.internal:80"), ("127.0.0.1:80")]}
                        ],
                    }
                ]
            }
        ),
    }
    entities = named_entities(PackageDocuments.parse(files), plan())
    assert {
        ("terraform"),
        ("kubernetes"),
        ("helm"),
        ("ansible"),
        ("nginx"),
        ("prometheus"),
    } == {entity.artifact.value for entity in entities}
    assert any(e.name == "web-release" for e in entities)
    assert not any(
        (".Release.Name") in e.name
        or ("${var.release}") in e.name
        or e.name.startswith("127.")
        for e in entities
    )
    assert any(e.artifact.value == "prometheus" and e.name == "web" for e in entities)


@pytest.mark.req("FR-V-02")
def test_shared_suffix_names_and_conservative_ansible_applicability():
    files = {
        ("terraform/main.tf"): (
            'resource "aws_instance" "app" { name = "app-server" }'
        ),
        ("ansible/playbook.yaml"): ("- hosts: app-servers"),
    }
    checks = naming_checks(PackageDocuments.parse(files), plan("ansible"))
    assert not any(c.check_id == "naming.unknown_service" for c in checks)
    assert not any(
        c.check_id == ("naming.missing_service") and c.file_path.startswith("ansible/")
        for c in checks
    )


@pytest.mark.req("FR-V-02")
def test_infrastructure_resources_and_jobs_do_not_create_unknown_warnings():
    files = {
        ("terraform/main.tf"): (
            'resource "aws_vpc" "main" { tags = { Name = "infra-vpc" } }'
        ),
        ("monitoring/prometheus/prometheus.yaml"): (
            "scrape_configs: [{job_name: node-exporter}]"
        ),
    }
    checks = naming_checks(PackageDocuments.parse(files), plan("prometheus"))
    assert not any(c.check_id == "naming.unknown_service" for c in checks)


@pytest.mark.req("FR-V-02")
def test_storage_names_and_literal_unknown_release_warn():
    from app.domain.plan import Storage

    deployment = plan().model_copy(
        update={
            ("storage"): [
                Storage(
                    name=("data"),
                    kind=("object_storage"),
                    aws_service=("s3"),
                    attached_to=[("web")],
                )
            ]
        }
    )
    files = {
        ("terraform/main.tf"): (
            'resource "aws_s3_bucket" "data" { bucket = "p'
            'roduction-data" }\nresource "helm_release" "ot'
            'her" { name = "unknown-release" }'
        )
    }
    checks = naming_checks(PackageDocuments.parse(files), deployment)
    assert not any(
        c.check_id == ("naming.missing_service") and ("'data'") in c.message
        for c in checks
    )
    assert any(c.check_id == "naming.unknown_service" for c in checks)
