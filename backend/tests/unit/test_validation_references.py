import json

import pytest

from app.validation.documents import PackageDocuments
from app.validation.references import reference_checks


def checks(files):
    return reference_checks(PackageDocuments.parse(files))


@pytest.mark.req("FR-V-01", "FR-V-04")
@pytest.mark.parametrize(
    ("source,check_id"),
    [
        (('output "demo" { value = var.missing }'), ("terraform.var_ref")),
        (('output "demo" { value = local.missing }'), ("terraform.local_ref")),
        (('output "demo" { value = module.missing.output }'), ("terraform.module_ref")),
        (('module "missing" { source = "./missing" }'), ("terraform.local_module")),
    ],
)
def test_broken_terraform_reference_has_file_and_line(source, check_id):
    found = checks({"terraform/main.tf": "# source comment\n" + source})
    check = next(c for c in found if c.check_id == check_id)
    assert check.status == "failed"
    assert check.file_path == "terraform/main.tf" and check.line_start == 2


@pytest.mark.req("FR-V-01")
def test_terraform_scope_declarations_outputs_and_json():
    files = {
        ("terraform/main.tf.json"): json.dumps(
            {
                ("variable"): {("input"): {("default"): ("value")}},
                ("locals"): {("x"): ("${var.input}")},
                ("module"): {("child"): {("source"): ("./child")}},
                ("output"): {("x"): {("value"): ("${module.child.result}")}},
            }
        ),
        ("terraform/child/main.tf"): ('output "result" { value = local.undeclared }'),
    }
    found = checks(files)
    assert not [
        c
        for c in found
        if c.status == ("failed") and c.file_path == ("terraform/main.tf.json")
    ]
    assert any(
        c.status == ("failed") and c.file_path == ("terraform/child/main.tf")
        for c in found
    )
    files["terraform/child/main.tf"] = 'output "other" { value = 1 }'
    assert any(
        c.check_id == ("terraform.module_output") and c.status == ("failed")
        for c in checks(files)
    )


@pytest.mark.req("FR-V-01", "NFR-01")
def test_terraform_comments_literals_and_escaped_interpolation_are_not_references():
    source = (
        '# var.missing\nlocals { text = "var.missing"\n '
        'escaped = "$${var.missing}"\n nested = "${form'
        'at("var.missing")}"\n}'
    )
    assert not [
        c
        for c in checks({("terraform/main.tf"): source})
        if c.check_id.endswith("_ref")
    ]


@pytest.mark.req("FR-V-01")
@pytest.mark.parametrize("source", ["../../escape", "/etc/config", "C:/config"])
def test_local_module_path_escape_is_failure(source):
    # Absolute module sources cannot be verified as package-local.
    found = checks({"terraform/main.tf": f'module "test" {{ source = "./{source}" }}'})
    assert any(
        c.check_id == ("terraform.local_module") and c.status == ("failed")
        for c in found
    )


def manifest(kind, name, **fields):
    return {"apiVersion": "v1", "kind": kind, "metadata": {"name": name}, **fields}


def k8s(objects):
    return {f"k8s/{index}.yaml": json.dumps(item) for index, item in enumerate(objects)}


@pytest.mark.req("FR-V-01")
@pytest.mark.parametrize(
    ("key,target_kind,warning"),
    [
        (("configMapRef"), ("ConfigMap"), False),
        (("configMapKeyRef"), ("ConfigMap"), False),
        (("configMap"), ("ConfigMap"), False),
        (("secretRef"), ("Secret"), True),
        (("secretKeyRef"), ("Secret"), True),
    ],
)
def test_configmap_and_secret_reference_families(key, target_kind, warning):
    if key == "configMap":
        spec = {"volumes": [{key: {"name": "settings"}}]}
    else:
        spec = {"containers": [{"envFrom": [{key: {"name": "settings"}}]}]}
    pod = manifest("Pod", "web", spec=spec)
    found = checks(k8s([pod]))
    assert found[0].status == ("warning" if warning else "failed")
    assert found[0].file_path == "k8s/0.yaml"
    found = checks(k8s([pod, manifest(target_kind, "settings")]))
    assert found[0].status == "passed"


@pytest.mark.req("FR-V-01")
def test_pvc_reference_and_namespace_scoping():
    pod = manifest(
        ("Pod"),
        ("web"),
        spec={("volumes"): [{("persistentVolumeClaim"): {("claimName"): ("data")}}]},
    )
    assert checks(k8s([pod]))[0].status == "failed"
    pvc = manifest("PersistentVolumeClaim", "data")
    assert checks(k8s([pod, pvc]))[0].status == "passed"
    pvc["metadata"]["namespace"] = "other"
    assert checks(k8s([pod, pvc]))[0].status == "failed"


@pytest.mark.req("FR-V-01")
def test_service_selector_matches_workload_labels():
    service = manifest("Service", "web", spec={"selector": {"app": "web"}})
    deployment = manifest(
        ("Deployment"),
        ("web"),
        spec={("template"): {("metadata"): {("labels"): {("app"): ("web")}}}},
    )
    assert checks(k8s([service]))[0].status == "failed"
    assert checks(k8s([service, deployment]))[0].status == "passed"
    deployment["spec"]["template"]["metadata"]["labels"] = {"app": "other"}
    assert checks(k8s([service, deployment]))[0].status == "failed"


@pytest.mark.req("FR-V-01")
def test_ingress_service_and_port_and_hpa_targets():
    ingress = manifest(
        ("Ingress"),
        ("web"),
        spec={
            ("rules"): [
                {
                    ("http"): {
                        ("paths"): [
                            {
                                ("backend"): {
                                    ("service"): {
                                        ("name"): ("web"),
                                        ("port"): {("name"): ("http")},
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        },
    )
    service = manifest("Service", "web", spec={"ports": [{"name": "http", "port": 80}]})
    assert any(
        c.check_id == ("k8s.ingress_service") and c.status == ("failed")
        for c in checks(k8s([ingress]))
    )
    assert not [c for c in checks(k8s([ingress, service])) if c.status == "failed"]
    service["spec"]["ports"] = [{"port": 81}]
    assert any(
        c.check_id == ("k8s.ingress_port") and c.status == ("failed")
        for c in checks(k8s([ingress, service]))
    )
    hpa = manifest(
        ("HorizontalPodAutoscaler"),
        ("web"),
        spec={("scaleTargetRef"): {("kind"): ("Deployment"), ("name"): ("web")}},
    )
    assert checks(k8s([hpa]))[0].status == "failed"
    assert checks(k8s([hpa, manifest("Deployment", "web")]))[0].status == "passed"


@pytest.mark.req("FR-V-01")
@pytest.mark.parametrize(
    ("repository,expected"),
    [
        ((), ("failed")),
        (("https://charts.example.com"), ("warning")),
        (("oci://charts.example.com"), ("warning")),
    ],
)
def test_helm_dependencies_and_values(repository, expected):
    files = {
        ("helm/web/Chart.yaml"): json.dumps(
            {("dependencies"): [{("name"): ("child"), ("repository"): repository}]}
        ),
        ("helm/web/values.yaml"): ("image: {repository: nginx}"),
        ("helm/web/templates/deployment.yaml"): (
            "image: {{ .Values.image.repository }}\nreplica"
            "s: {{ .Values.replicas | default 1 }}"
        ),
    }
    found = checks(files)
    assert next(c for c in found if c.check_id == "helm.dependency").status == expected
    assert [c.status for c in found if c.check_id == ("helm.values_ref")] == [
        ("passed"),
        ("warning"),
    ]
    files["helm/web/charts/child/Chart.yaml"] = "name: child"
    assert next(
        c for c in checks(files) if c.check_id == ("helm.dependency")
    ).status == ("passed")


@pytest.mark.req("FR-V-01")
@pytest.mark.parametrize(
    ("inventory"),
    [("all:\n  children:\n    web:\n      hosts: {host1: {}}"), ("[web]\nhost1")],
)
def test_ansible_inventory_groups_and_roles(inventory):
    suffix = "yaml" if inventory.startswith("all:") else "ini"
    files = {
        f"ansible/inventory.{suffix}": inventory,
        ("ansible/playbook.yaml"): ("- hosts: web\n  roles: [web]"),
    }
    found = checks(files)
    assert next(
        c for c in found if c.check_id == ("ansible.inventory_group")
    ).status == ("passed")
    assert next(c for c in found if c.check_id == "ansible.role_ref").status == "failed"
    files["ansible/roles/web/tasks/main.yaml"] = "- debug: {msg: hi}"
    assert not [c for c in checks(files) if c.status == "failed"]
    files[("ansible/playbook.yaml")] = (
        "- hosts: missing\n  tasks:\n    - include_role: {name: missing}"
    )
    assert {c.check_id for c in checks(files) if c.status == ("failed")} == {
        ("ansible.inventory_group"),
        ("ansible.role_ref"),
    }


@pytest.mark.req("FR-V-01")
def test_ansible_absent_inventory_and_symbolic_hosts():
    assert not checks({"ansible/playbook.yaml": "- hosts: missing"})
    files = {
        ("ansible/inventory.yaml"): ("all: {}"),
        ("ansible/playbook.yaml"): ('- hosts: "{{ host_group }}"'),
    }
    assert checks(files)[0].status == "warning"


@pytest.mark.req("FR-V-01", "NFR-01")
@pytest.mark.parametrize(
    ("rule,expected"),
    [
        (("rules/*.yaml"), ("passed")),
        (("rules/**/*.yaml"), ("passed")),
        (("missing.yaml"), ("failed")),
        (("../../../outside.yaml"), ("failed")),
        (("/etc/secret.yaml"), ("failed")),
    ],
)
def test_prometheus_rule_globs_paths_and_single_finding(rule, expected):
    files = {
        ("monitoring/prometheus/prometheus.yaml"): json.dumps(
            {("scrape_configs"): [], ("rule_files"): [rule, rule]}
        ),
        ("monitoring/prometheus/rules/web.yaml"): ("groups: []"),
    }
    found = checks(files)
    assert len(found) == 1
    assert found[0].status == expected
    assert found[0].file_path == "monitoring/prometheus/prometheus.yaml"


@pytest.mark.req("FR-V-01")
def test_helm_values_comments_and_literals_are_not_references():
    files = {
        ("helm/web/Chart.yaml"): ("name: web"),
        ("helm/web/values.yaml"): ("image: nginx"),
        ("helm/web/templates/file.yaml"): (
            '{{/* .Values.missing */}}\n{{ printf ".Values.'
            'missing" }}\nplain: .Values.missing'
        ),
    }
    assert not [c for c in checks(files) if c.check_id == "helm.values_ref"]
