"""D-56: catalogue candidates use unchanged acceptance and historical evidence."""

import copy
import shutil

import pytest
import yaml

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.pipeline.demo_stub import DEMO_PLAN
from app.security.kubernetes import repair_pods
from app.security.kubernetes_render import repair_formats_and_pods, repair_kubernetes
from scripts.phase9i_kubernetes_replay import counts, historical_retained
from scripts.phase9i_replay import ROOT, inventory
from tests.unit.test_kubernetes_catalogue import workload
from tests.unit.test_phase9i_deterministic import Engine, Scanner, Verifier, report

pytestmark = pytest.mark.req("FR-S-04", "FR-S-09", "FR-V-01", "FR-V-03", "NFR-01")


@pytest.mark.parametrize(
    "mode,failed,reason",
    [
        ("clean", False, "improved"),
        ("clean", True, "no_improvement"),
        ("new_blocker", False, "new_blocking_findings"),
        ("unavailable", False, "verification_unavailable"),
    ],
)
async def test_async_candidate_retains_existing_guards(mode, failed, reason):
    from types import SimpleNamespace

    files = {"monitoring/grafana/app.json": '{"dashboard":{"panels":[]}}'}
    result, _, records = await checked_one(
        files,
        DeploymentPlan.model_validate(DEMO_PLAN),
        Variant.COST,
        report(True),
        Engine(failed),
        SimpleNamespace(scanner=Scanner(mode), terraform_verifier=Verifier()),
        AgentBudget(30),
        repair_formats_and_pods,
    )
    assert (result != files) is (reason == "improved")
    assert records[0]["reason"] == reason


async def test_expired_async_construction_is_bounded_and_audited():
    from types import SimpleNamespace

    now = [0.0]
    budget = AgentBudget(1, clock=lambda: now[0])
    now[0] = 2.0
    files = {"k8s/app.yaml": yaml.safe_dump(workload())}
    result, _, records = await checked_one(
        files,
        DeploymentPlan.model_validate(DEMO_PLAN),
        Variant.COST,
        report(True),
        Engine(False),
        SimpleNamespace(scanner=Scanner("clean"), terraform_verifier=Verifier()),
        budget,
        repair_kubernetes,
    )
    assert result == files
    assert records[0]["reason"] == "verification_unavailable"


@pytest.mark.skipif(
    not all((ROOT / f".cache/final-{n}-results").exists() for n in (1, 2)),
    reason="saved final snapshots unavailable",
)
def test_pinned_historical_reconstruction_matches_all_81_saved_packages():
    items, _ = inventory()
    assert len(items) == 81
    for item in items:
        historical_retained(item)


def test_multiple_documents_mounts_and_init_containers_preserve_intent():
    first = workload(volumeMounts=[{"name": "cache", "mountPath": "/cache"}])
    first["spec"]["template"]["spec"]["volumes"] = [{"name": "cache", "emptyDir": {}}]
    second = workload("Job")
    second["metadata"]["name"] = "job"
    source = yaml.safe_dump_all([first, second], sort_keys=False)
    result, records = repair_pods({"k8s/workloads.yaml": source})
    docs = list(yaml.safe_load_all(result["k8s/workloads.yaml"]))
    pod = docs[0]["spec"]["template"]["spec"]
    assert pod["containers"][0]["volumeMounts"][0] == {
        "name": "cache",
        "mountPath": "/cache",
    }
    assert len(pod["volumes"]) == 2
    assert len(records) == 4
    assert len(list(yaml.safe_load_all(source))) == len(docs)


def test_empty_maps_and_unresolved_quantity_preservation():
    doc = workload(securityContext={}, resources={"limits": {"cpu": "${CPU_LIMIT}"}})
    result, records = repair_pods(
        {"k8s/app.yaml": yaml.safe_dump(doc, sort_keys=False)}
    )
    container = yaml.safe_load(result["k8s/app.yaml"])["spec"]["template"]["spec"][
        "containers"
    ][0]
    assert container["securityContext"]["runAsNonRoot"] is True
    assert container["resources"]["limits"]["cpu"] == "${CPU_LIMIT}"
    assert "cpu" not in container["resources"]["requests"]
    assert any(
        "inconsistent_or_unresolved_resources" in r.get("skipped_reasons", [])
        for r in records
    )


def test_counts_never_treat_invalid_zero_blockers_as_checks_passed():
    item = {
        "validation": "invalid",
        "scan_outcome": "clean",
        "blockers": [],
        "findings": [],
        "profiles": {
            p: {"checks_passed": False, "remaining_blocking": 0}
            for p in ("strict", "contextual-v1", "contextual-v2")
        },
    }
    summary = counts([item, copy.deepcopy(item)])
    assert summary["valid"] == 0
    assert summary["checks_passed"] == {
        "strict": 0,
        "contextual-v1": 0,
        "contextual-v2": 0,
    }


def test_duplicate_values_and_explicit_namespaces_are_not_modified():
    doc = workload()
    path = "helm/app/templates/app.yaml"
    for values in ("replicas: 1\nreplicas: 2\n", "infraarchSecurity: {custom: keep}\n"):
        files = {
            path: yaml.safe_dump(doc, sort_keys=False),
            "helm/app/values.yaml": values,
        }
        result, _ = repair_pods(files, {path: [doc]})
        assert result == files


def test_volume_collision_preserves_existing_volume_and_records_skip():
    import hashlib

    doc = workload()
    identifier = hashlib.sha256(b"k8s/app.yaml:0:Deployment").hexdigest()[:12]
    volume = {"name": "infraarch-tmp-" + identifier + "-c0", "emptyDir": {}}
    doc["spec"]["template"]["spec"]["volumes"] = [volume]
    result, records = repair_pods(
        {"k8s/app.yaml": yaml.safe_dump(doc, sort_keys=False)}
    )
    pod = yaml.safe_load(result["k8s/app.yaml"])["spec"]["template"]["spec"]
    assert pod["volumes"] == [volume]
    assert not pod["containers"][0].get("volumeMounts")
    assert any("volume_name_collision" in r.get("skipped_reasons", []) for r in records)


@pytest.mark.skipif(shutil.which("helm") is None, reason="offline Helm unavailable")
async def test_real_helper_names_and_outer_condition_preserve_disabled_render():
    from app.security.kubernetes_render import render_charts

    path = "helm/app/templates/app.yaml"
    source = yaml.safe_dump(workload(), sort_keys=False).replace(
        "name: app", 'name: {{ include "app.name" . }}'
    )
    files = {
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.0.0\n",
        "helm/app/values.yaml": "enabled: true\n",
        path: "{{- if .Values.enabled }}\n" + source + "{{- end }}\n",
    }
    result, records = await repair_formats_and_pods(files)
    assert any(
        r["kind"] == "kubernetes_pod_defaults" and r.get("outcome") != "skipped"
        for r in records
    )
    rendered = await render_charts(result)
    pod = rendered[path][0]["spec"]["template"]["spec"]
    assert pod["containers"][0]["securityContext"]["runAsUser"] == 10001
    assert pod["securityContext"]["runAsNonRoot"] is True
    result["helm/app/values.yaml"] = result["helm/app/values.yaml"].replace(
        "enabled: true", "enabled: false"
    )
    assert await render_charts(result) == {}


def test_empty_nested_controls_fill_missing_leaves_and_privileged_conflicts_skip():
    for security, expected in (
        (
            {"capabilities": {}, "seccompProfile": {}},
            {
                "capabilities": {"drop": ["ALL"]},
                "seccompProfile": {"type": "RuntimeDefault"},
            },
        ),
        (
            {"privileged": True, "capabilities": {"add": ["SYS_ADMIN"]}},
            {"privileged": True, "capabilities": {"add": ["SYS_ADMIN"]}},
        ),
    ):
        result, _ = repair_pods(
            {
                "k8s/app.yaml": yaml.safe_dump(
                    workload(securityContext=security), sort_keys=False
                )
            }
        )
        current = yaml.safe_load(result["k8s/app.yaml"])["spec"]["template"]["spec"][
            "containers"
        ][0]["securityContext"]
        assert expected.items() <= current.items()
        if security.get("privileged"):
            assert "allowPrivilegeEscalation" not in current
            assert "seccompProfile" not in current


def test_historical_equivalents_do_not_invoke_new_live_migrations(monkeypatch):
    from app.validation import equivalents
    from scripts.phase9i_kubernetes_replay import pinned_equivalents

    def unexpected(_):
        pytest.fail("Historical reconstruction invoked the new live migration hook")

    monkeypatch.setattr(equivalents, "repair_v6_equivalents", unexpected)
    files = {
        "terraform/main.tf": 'resource "aws_eip" "nat" { vpc = true }\n'
        'resource "aws_db_instance" "db" { name = var.database }\n'
    }
    candidate, records = pinned_equivalents()(files)
    assert "vpc = true" in candidate["terraform/main.tf"]
    assert "db_name = var.database" in candidate["terraform/main.tf"]
    assert [r["kind"] for r in records] == ["db_name"]
