import pytest

from app.validation.documents import PackageDocuments
from app.validation.structure import structural_checks
from tests.unit.test_generators import plan


def run(files, *types):
    return structural_checks(
        PackageDocuments.parse({"terraform/main.tf": "locals {}", **files}),
        plan(*types),
    )


@pytest.mark.req("FR-V-04")
def test_grafana_rows_remain_valid_and_api_wrappers_remain_rejected():
    dashboard = '{"panels":[{"type":"row","panels":[{"type":"timeseries"}]}]}'
    path = "monitoring/grafana/dashboard.json"
    assert not [c for c in run({path: dashboard}, "grafana") if c.status == "failed"]
    wrapped = '{"dashboard":' + dashboard + ',"overwrite":true}'
    assert any(
        c.check_id == "grafana.panels" and c.status == "failed"
        for c in run({path: wrapped}, "grafana")
    )


@pytest.mark.req("FR-V-03", "FR-V-04")
@pytest.mark.parametrize(
    "kind,path,valid,invalid",
    [
        (
            "kubernetes",
            "k8s/app.yaml",
            (
                "apiVersion: apps/v1\nkind: Deployment\nmetadata"
                ": {name: web}\nspec:\n  template:\n    spec:\n   "
                "   containers: [{name: web, image: nginx}]\n"
            ),
            "apiVersion: v1\nkind: Deployment\nmetadata: {name: web}\nspec: {}",
        ),
        (
            "dockerfile",
            "docker/Dockerfile",
            "FROM alpine\nRUN echo hello\n",
            "RUN echo hello\nFROG unknown\n",
        ),
        (
            "jenkins",
            "jenkins/Jenkinsfile",
            "pipeline { agent any stages { stage('build') { steps { echo '}' } } } }",
            "pipeline { agent any stages { stage('build') { echo 'missing steps' } } }",
        ),
        (
            "ansible",
            "ansible/playbook.yaml",
            (
                "- hosts: all\n  tasks:\n    - name: test\n      "
                "ansible.builtin.debug: {msg: test}\n"
            ),
            "- tasks: [{name: empty}]",
        ),
        (
            "nginx",
            "nginx/site.conf",
            "server { location / { return 200; } }",
            "upstream web { server 127.0.0.1; }",
        ),
        (
            "prometheus",
            "monitoring/prometheus/prometheus.yaml",
            "scrape_configs: [{job_name: web}]",
            "scrape_configs: [{}]",
        ),
        (
            "grafana",
            "monitoring/grafana/dashboard.json",
            '{"panels":[{"type":"timeseries"}]}',
            '{"title":"No panels"}',
        ),
    ],
)
def test_artifact_pass_and_fail(kind, path, valid, invalid):
    assert not [c for c in run({path: valid}, kind) if c.status == "failed"]
    failures = [c for c in run({path: invalid}, kind) if c.status == "failed"]
    assert failures
    assert all(c.file_path == path and c.line_start >= 1 for c in failures)


@pytest.mark.req("FR-V-04")
def test_helm_chart_values_and_templates_support_distinction():
    files = {
        "helm/web/Chart.yaml": "apiVersion: v2\nname: web\nversion: 1.0.0",
        "helm/web/values.yaml": "image: nginx",
        "helm/web/templates/deployment.yaml": "name: {{ .Release.Name }}",
    }
    assert not [c for c in run(files, "helm") if c.status == "failed"]
    files["helm/web/Chart.yaml"] = "name: web"
    del files["helm/web/templates/deployment.yaml"]
    ids = {c.check_id for c in run(files, "helm") if c.status == "failed"}
    assert ids == {"helm.chart", "helm.templates"}
    files["helm/web/values.yaml"] = "image: ["
    assert any(
        c.check_id == "document.parse" and c.file_path.endswith("values.yaml")
        for c in run(files, "helm")
    )


@pytest.mark.req("FR-V-04")
def test_supporting_ansible_tasks_and_prometheus_rules():
    files = {
        ("ansible/roles/web/tasks/main.yaml"): (
            "- name: do\n  ansible.builtin.debug: {msg: hello}"
        ),
        "ansible/roles/web/defaults/main.yaml": "image: nginx",
        "monitoring/prometheus/rules.yaml": "groups: [{name: web, rules: []}]",
    }
    checks = run(files, "ansible", "prometheus")
    assert not [c for c in checks if c.status == "failed"]
    assert not any(c.check_id == "ansible.playbook" for c in checks)
    assert not any(c.check_id == "prometheus.scrape_configs" for c in checks)


@pytest.mark.req("FR-V-04", "NFR-01")
@pytest.mark.parametrize(
    "path,source,kind",
    [
        ("k8s/app.yaml", "name: [", "kubernetes"),
        ("terraform/main.tf", "resource {", "terraform"),
        ("monitoring/grafana/dashboard.json", '{"panels":', "grafana"),
        ("ansible/playbook.yaml", "- hosts: [", "ansible"),
    ],
)
def test_parser_errors_are_safe_and_located(path, source, kind):
    checks = run({path: source}, *([kind] if kind != "terraform" else []))
    failure = next(c for c in checks if c.check_id == "document.parse")
    assert failure.file_path == path and failure.line_start >= 1
    assert source not in failure.message


@pytest.mark.req("FR-V-04")
def test_duplicate_kubernetes_identity_is_namespace_scoped():
    source = "apiVersion: v1\nkind: Service\nmetadata: {name: web, namespace: one}"
    assert not [
        c
        for c in run(
            {"k8s/a.yaml": source, "k8s/b.yaml": source.replace("one", "two")},
            "kubernetes",
        )
        if c.status == "failed"
    ]
    assert any(
        c.check_id == "k8s.duplicate" and c.status == "failed"
        for c in run({"k8s/a.yaml": source, "k8s/b.yaml": source}, "kubernetes")
    )


@pytest.mark.req("FR-V-01", "FR-V-04")
@pytest.mark.parametrize(
    "target,extra,expected",
    [
        ("http://WEB:8080/api", {}, "passed"),
        (
            "http://app_service:80/",
            {
                ("nginx/upstream.conf"): (
                    "upstream app-service { server 127.0.0.1; }\nserver {}"
                )
            },
            "passed",
        ),
        (
            "http://app_service:80/",
            {
                ("k8s/service.yaml"): (
                    "apiVersion: v1\nkind: Service\nmetadata: {name: app-service}"
                )
            },
            "passed",
        ),
        (
            "http://my_release/",
            {
                ("terraform/helm.tf"): (
                    'resource "helm_release" "example" { name = "my-release" }'
                )
            },
            "passed",
        ),
        ("http://10.0.0.1:8080/path", {}, "passed"),
        ("http://[::1]:8080/path", {}, "passed"),
        ("https://example.com:443/path", {}, "passed"),
        (
            "http://external_host/",
            {"nginx/declaration.conf": "# external-host: external-host\nserver {}"},
            "passed",
        ),
        ("http://$host:8080/", {}, "warning"),
        ("http://missing:80/path", {}, "failed"),
        (
            "http://release/",
            {"helm/web/templates/service.yaml": "{{ .Release.Name }}"},
            "failed",
        ),
    ],
)
def test_approved_nginx_resolution_rule(target, extra, expected):
    files = {
        "nginx/site.conf": f"# comment\nserver {{\n  proxy_pass {target};\n}}",
        **extra,
    }
    checks = run(
        files,
        "nginx",
        *(["kubernetes"] if any(p.startswith("k8s/") for p in extra) else []),
    )
    check = next(
        c
        for c in checks
        if c.check_id == "nginx.proxy_pass" and c.file_path == "nginx/site.conf"
    )
    assert check.status == expected
    assert check.line_start == 3
    if expected == "failed":
        assert "nginx/site.conf:3" in check.message


@pytest.mark.req("FR-V-04")
def test_comments_and_strings_do_not_create_structure():
    source = '# server { fake }\nserver { set $value "{"; }'
    assert not [
        c for c in run({"nginx/site.conf": source}, "nginx") if c.status == "failed"
    ]
    source = "// pipeline { agent any stages {} }\necho 'pipeline { agent stages }'"
    assert any(
        c.check_id == "jenkins.pipeline" and c.status == "failed"
        for c in run({"jenkins/Jenkinsfile": source}, "jenkins")
    )


@pytest.mark.req("FR-V-04")
def test_shared_index_preserves_yaml_positions_and_rejects_recursive_aliases():
    parsed = PackageDocuments.parse(
        {"k8s/service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: web\n"}
    )
    doc = parsed.documents["k8s/service.yaml"].yaml_documents[0]
    assert doc.positions[("metadata", "name")] == 4
    parsed = PackageDocuments.parse({"ansible/playbook.yaml": "value: &alias [*alias]"})
    assert parsed.documents["ansible/playbook.yaml"].parse_error


@pytest.mark.req("FR-V-04")
@pytest.mark.parametrize(
    ("path,source,kind,check_id"),
    [
        (
            ("monitoring/grafana/dashboard.json"),
            ('{"panels":[{}]}'),
            ("grafana"),
            ("grafana.panel_type"),
        ),
        (("nginx/site.conf"), ("server {"), ("nginx"), ("nginx.braces")),
        (
            ("jenkins/Jenkinsfile"),
            ("pipeline { agent any stages {"),
            ("jenkins"),
            ("jenkins.braces"),
        ),
        (
            ("k8s/app.yaml"),
            (
                "apiVersion: apps/v1\nkind: Deployment\nmetadata"
                ": {name: web}\nspec: wrong"
            ),
            ("kubernetes"),
            ("k8s.containers"),
        ),
    ],
)
def test_specific_missing_fields_and_malformed_shapes(path, source, kind, check_id):
    assert any(
        c.check_id == check_id and c.status == ("failed")
        for c in run({path: source}, kind)
    )


@pytest.mark.req("FR-V-01")
def test_quoted_nginx_text_does_not_create_targets_or_external_declarations():
    source = 'server { set $value "proxy_pass http://missing;"; }'
    assert not any(
        c.check_id == ("nginx.proxy_pass")
        for c in run({("nginx/site.conf"): source}, ("nginx"))
    )
    source = (
        'server { set $value "# external-host: missing"; proxy_pass http://missing; }'
    )
    assert any(
        c.check_id == ("nginx.proxy_pass") and c.status == ("failed")
        for c in run({("nginx/site.conf"): source}, ("nginx"))
    )


@pytest.mark.req("FR-V-01")
def test_quoted_text_cannot_define_nginx_upstream():
    source = (
        'server { set $value "upstream fake { server 1'
        '27.0.0.1; }"; proxy_pass http://fake; }'
    )
    assert any(
        c.check_id == ("nginx.proxy_pass") and c.status == ("failed")
        for c in run({("nginx/site.conf"): source}, ("nginx"))
    )


@pytest.mark.req("FR-V-04")
def test_ansible_inventory_alias_and_task_metadata():
    files = {
        ("ansible/hosts.yaml"): ("all: {children: {web: {}}}"),
        ("ansible/roles/web/tasks/main.yaml"): (
            "- name: Missing module\n  args: {foo: bar}\n  listen: event"
        ),
    }
    checks = run(files, "ansible")
    assert not any(c.check_id == "ansible.playbook" for c in checks)
    assert any(
        c.check_id == "ansible.task_module" and c.status == "failed" for c in checks
    )
