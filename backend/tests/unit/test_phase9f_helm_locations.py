"""FR-S-03/FR-V-03/NFR-01: corrective guard regressions."""

import json
from pathlib import Path

import pytest

from app.domain.enums import Variant
from app.scanners.checkov_parser import CheckovPathError, parse_checkov
from app.scanners.runner import ToolFailure, ToolResult
from app.scanners.scan import Scanner
from tests.unit.test_scanners import files, recorded

pytestmark = pytest.mark.req("FR-S-03", "FR-V-03", "NFR-01")


def test_checkov_chart_name_maps_to_exact_source(tmp_path: Path):
    chart = tmp_path / "helm/eks/Chart.yaml"
    chart.parent.mkdir(parents=True)
    chart.write_text("apiVersion: v2\nname: eks-workloads\n")
    files = {"helm/eks/Chart.yaml", "helm/eks/templates/workloads.yaml"}
    data = {
        "check_type": "helm",
        "results": {
            "failed_checks": [
                {
                    "check_id": "CKV_K8S_21",
                    "check_name": "test",
                    "resource": "Deployment.api",
                    "file_path": "/helm/eks/eks-workloads/templates/workloads.yaml",
                    "file_line_range": [3, 15],
                }
            ]
        },
    }
    findings = parse_checkov(json.dumps(data), tmp_path, files)
    assert len(findings) == 1
    assert findings[0].file_path == "helm/eks/templates/workloads.yaml"
    assert findings[0].line_start is None
    data["results"]["failed_checks"][0]["file_path"] = (
        "/helm/eks/eks-workloads/templates/../../escape.yaml"
    )
    with pytest.raises(CheckovPathError):
        parse_checkov(json.dumps(data), tmp_path, files)


def test_nested_chart_metadata_cannot_choose_an_ambiguous_source(tmp_path: Path):
    sources = {
        "helm/a/Chart.yaml": "name: b\n",
        "helm/a/b/templates/Chart.yaml": "name: c\n",
        "helm/a/templates/c/templates/workloads.yaml": "kind: Deployment\n",
        "helm/a/b/templates/templates/workloads.yaml": "kind: Deployment\n",
    }
    for path, content in sources.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    report = {
        "check_type": "helm",
        "results": {
            "failed_checks": [
                {
                    "check_id": "CKV_K8S_21",
                    "file_path": "/helm/a/b/templates/c/templates/workloads.yaml",
                }
            ]
        },
    }
    with pytest.raises(CheckovPathError):
        parse_checkov(json.dumps(report), tmp_path, set(sources))


@pytest.mark.parametrize("malformed", [False, True])
async def test_mapping_failure_is_distinct_from_malformed_json(malformed):
    runner = recorded("fixed", repeat=2)
    report = {
        "check_type": "helm",
        "results": {
            "failed_checks": [
                {"check_id": "CKV_K8S_21", "file_path": "/missing/templates/x.yaml"}
            ]
        },
    }
    output = "{broken" if malformed else json.dumps(report)
    runner.results["checkov"] = [ToolResult(output, "", 1, 0)] * 2
    with pytest.raises(ToolFailure) as caught:
        await Scanner(runner).scan(files("fixed"), Variant.SECURITY)
    assert caught.value.category == ("invalid_json" if malformed else "path_mapping")
