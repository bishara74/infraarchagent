"""FR-S-04/09, FR-V-01: missing-only, reproducible pod hardening."""

import copy
import shutil

import pytest
import yaml

from app.security.kubernetes import repair_pods

pytestmark = pytest.mark.req("FR-S-04", "FR-S-09", "FR-V-01", "NFR-01")


def workload(kind="Deployment", **container):
    return {
        "apiVersion": "apps/v1" if kind != "Job" else "batch/v1",
        "kind": kind,
        "metadata": {"name": "app"},
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {"name": "app", "image": "example/app:1.2", **container}
                    ]
                }
            }
        },
    }


def apply(doc):
    files = {"k8s/app.yaml": yaml.safe_dump(doc, sort_keys=False)}
    result, records = repair_pods(files)
    return (
        result,
        records,
        yaml.safe_load(result["k8s/app.yaml"])["spec"]["template"]["spec"],
    )


@pytest.mark.parametrize("kind", ["Deployment", "StatefulSet", "DaemonSet", "Job"])
def test_every_entry_and_idempotence(kind):
    files, records, pod = apply(workload(kind))
    c = pod["containers"][0]
    assert c["securityContext"] == {
        "runAsNonRoot": True,
        "runAsUser": 10001,
        "runAsGroup": 10001,
        "allowPrivilegeEscalation": False,
        "readOnlyRootFilesystem": True,
        "capabilities": {"drop": ["ALL"]},
        "seccompProfile": {"type": "RuntimeDefault"},
    }
    assert c["resources"] == {
        "requests": {"cpu": "100m", "memory": "128Mi"},
        "limits": {"cpu": "500m", "memory": "512Mi"},
    }
    assert c["volumeMounts"][0]["mountPath"] == "/tmp"
    assert pod["volumes"][0]["emptyDir"] == {}
    assert records[0]["runtime_compatibility"] == "unverified"
    assert repair_pods(files) == (files, [])


def test_explicit_settings_and_inherited_identity_survive():
    original = {
        "runAsUser": 0,
        "runAsNonRoot": False,
        "readOnlyRootFilesystem": False,
        "allowPrivilegeEscalation": True,
        "capabilities": {"add": ["SYS_ADMIN"]},
    }
    _, _, pod = apply(workload(securityContext=original))
    current = pod["containers"][0]["securityContext"]
    assert original.items() <= current.items()
    assert "runAsGroup" not in current
    doc = workload()
    doc["spec"]["template"]["spec"]["securityContext"] = {
        "runAsUser": 12345,
        "runAsGroup": 23456,
    }
    _, _, pod = apply(doc)
    assert "runAsUser" not in pod["containers"][0]["securityContext"]


def test_init_containers_and_partial_resource_consistency():
    doc = workload(
        resources={"requests": {"cpu": "800m"}, "limits": {"memory": "64Mi"}}
    )
    doc["spec"]["template"]["spec"]["initContainers"] = [
        {"name": "init", "image": "example/init:1"}
    ]
    _, _, pod = apply(doc)
    assert (
        pod["containers"][0]["resources"]
        == doc["spec"]["template"]["spec"]["containers"][0]["resources"]
    )
    assert pod["initContainers"][0]["securityContext"]["runAsUser"] == 10001


def test_comments_and_unrelated_content_preserved():
    source = yaml.safe_dump(workload(), sort_keys=False).replace(
        "image:", "# retain this comment\n        image:"
    )
    files = {"k8s/app.yaml": source, "README.md": "keep"}
    result, _ = repair_pods(files)
    assert "# retain this comment" in result["k8s/app.yaml"]
    assert result["README.md"] == "keep"


@pytest.mark.parametrize(
    "source", ["not: [yaml", "kind: Deployment\nkind: Job\n", "a: &x {b: *x}"]
)
def test_malformed_and_ambiguous_inputs(source):
    files = {"k8s/app.yaml": source}
    result, records = repair_pods(files)
    assert result == files
    assert all(r["outcome"] == "skipped" for r in records)


def test_windows_and_existing_mount_are_preserved():
    doc = workload()
    doc["spec"]["template"]["spec"]["os"] = {"name": "windows"}
    files = {"k8s/app.yaml": yaml.safe_dump(doc)}
    assert repair_pods(files) == (files, [])
    _, _, pod = apply(workload(volumeMounts=[{"name": "tmp", "mountPath": "/tmp"}]))
    assert pod["containers"][0]["volumeMounts"] == [
        {"name": "tmp", "mountPath": "/tmp"}
    ]


def test_readiness_uses_only_current_retained_records():
    from app.domain.archive import runtime_defaults_notes

    files, records, _ = apply(workload())
    record = records[0]
    assert runtime_defaults_notes(files, {"records": records}) == []
    record["outcome"] = "rejected"
    assert runtime_defaults_notes(files, {"records": records}) == []
    record["outcome"] = "accepted"
    assert (
        "runtime compatibility unverified"
        in runtime_defaults_notes(files, {"records": records})[0]
    )
    assert (
        runtime_defaults_notes({"k8s/app.yaml": "changed"}, {"records": records}) == []
    )
    assert runtime_defaults_notes(files, None, {}) == []


@pytest.mark.asyncio
@pytest.mark.skipif(shutil.which("helm") is None, reason="offline Helm unavailable")
async def test_actual_helm_render_and_values_overrides():
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from app.scanners.runner import ProcessToolRunner
    from app.security.kubernetes_render import repair_kubernetes

    doc = workload()
    files = {
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.0.0\n",
        "helm/app/values.yaml": "# original values\nreplicas: 2\n",
        "helm/app/templates/app.yaml": yaml.safe_dump(doc, sort_keys=False),
    }
    result, records = await repair_kubernetes(files)
    assert records
    values = yaml.safe_load(result["helm/app/values.yaml"])
    wid = next(iter(values["infraarchSecurity"]))
    values["infraarchSecurity"][wid]["c0"]["securityContext"][
        "readOnlyRootFilesystem"
    ] = False
    values["infraarchSecurity"][wid]["c0"]["writablePaths"] = []
    values["infraarchSecurity"][wid]["c0"]["securityContext"]["runAsUser"] = 22222
    values["infraarchSecurity"][wid]["c0"]["securityContext"]["runAsGroup"] = 33333
    with TemporaryDirectory() as directory:
        root = Path(directory)
        for path, source in result.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source)
        (root / "override.yaml").write_text(yaml.safe_dump(values))
        output = await ProcessToolRunner().run_command(
            "helm", ["helm", "template", "app", "helm/app", "-f", "override.yaml"], root
        )
        assert output.exit_code == 0, output.stderr
        rendered = list(yaml.safe_load_all(output.stdout))[0]
        pod = rendered["spec"]["template"]["spec"]
        assert (
            pod["containers"][0]["securityContext"]["readOnlyRootFilesystem"] is False
        )
        assert pod["containers"][0]["securityContext"]["runAsUser"] == 22222
        assert pod["containers"][0]["securityContext"]["runAsGroup"] == 33333
        assert not pod.get("volumes")
        assert not pod["containers"][0].get("volumeMounts")
    assert await repair_kubernetes(result) == (result, [])


def test_helm_requires_real_render_evidence_and_skips_control_flow():
    files = {"helm/app/templates/app.yaml": yaml.safe_dump(workload(), sort_keys=False)}
    assert repair_pods(files) == (files, [])
    source = copy.deepcopy(files)
    source["helm/app/templates/app.yaml"] = (
        "{{ range .Values.items }}\n" + next(iter(files.values())) + "{{ end }}\n"
    )
    result, records = repair_pods(source, {"helm/app/templates/app.yaml": [workload()]})
    assert result == source
    assert records[0]["outcome"] == "skipped"
