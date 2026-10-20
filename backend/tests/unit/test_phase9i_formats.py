"""FR-V-01/04: only lossless envelopes and standard undefined helpers."""

import json

import pytest

from app.validation.formats import repair_formats

pytestmark = pytest.mark.req("FR-V-01", "FR-V-04", "NFR-01")


def test_grafana_envelope_preserves_dashboard_and_is_idempotent():
    dashboard = {
        "title": "App",
        "uid": "stable",
        "panels": [{"type": "graph", "targets": [{"expr": "rate(x[5m])"}]}],
    }
    for metadata in ({"overwrite": True}, {"meta": {"type": "dashboard"}}):
        files = {
            "monitoring/grafana/dashboard.json": json.dumps(
                {"dashboard": dashboard, **metadata}
            )
        }
        result, records = repair_formats(files)
        assert json.loads(result["monitoring/grafana/dashboard.json"]) == dashboard
        assert len(records) == 1
        assert repair_formats(result) == (result, [])


def test_ambiguous_grafana_and_custom_helpers_are_untouched():
    files = {
        "monitoring/grafana/dashboard.json": '{"dashboard":{"panels":[]},"custom":"keep"}',
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.0.0\n",
        "helm/app/templates/deployment.yaml": '{{ include "other.fullname" . }}\n{{ include "app.custom" . }}',
    }
    assert repair_formats(files) == (files, [])


def test_helper_dependencies_are_added_without_overwriting_existing_definition():
    existing = '{{- define "app.name" -}}keep-this-name{{- end }}\n'
    files = {
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.0.0\n",
        "helm/app/templates/_helpers.tpl": existing,
        "helm/app/templates/deployment.yaml": '{{ include "app.fullname" . }}\n{{ include "app.labels" . }}',
    }
    result, records = repair_formats(files)
    helper = result["helm/app/templates/_helpers.tpl"]
    assert helper.startswith(existing)
    assert helper.count('define "app.name"') == 1
    for suffix in ("fullname", "chart", "labels", "selectorLabels"):
        assert f'define "app.{suffix}"' in helper
    assert records and repair_formats(result) == (result, [])


def test_helm_diagnostics_retain_only_safe_identifier_and_package_location(tmp_path):
    from app.scanners.runner import ToolResult
    from app.validation.documents import PackageDocuments
    from app.validation.linters import linter_targets, parse_lint

    files = {
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.0.0\n",
        "helm/app/templates/workloads.yaml": '{{ include "app.fullname" . }}',
    }
    target = next(
        t for t in linter_targets(PackageDocuments.parse(files)) if t.tool == "helm"
    )
    output = '[ERROR] templates/: app/templates/workloads.yaml:4:11\n template: no template "app.fullname" associated with template "gotpl" PRIVATE_CANARY\n'
    checks = parse_lint(target, ToolResult(output, "", 1, 0), tmp_path, set(files))
    assert checks[0].template_name == "app.fullname"
    assert checks[0].file_path == "helm/app/templates/workloads.yaml"
    assert checks[0].line_start == 4
    assert "PRIVATE_CANARY" not in str(checks)
