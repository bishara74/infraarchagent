"""FR-S-04, NFR-01: image parameterisation never invents provenance."""

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from app.scanners.runner import ProcessToolRunner
from app.security.kubernetes_images import image_parts, repair_image_values
from app.security.kubernetes_render import render_charts

pytestmark = pytest.mark.req("FR-S-04", "FR-V-01", "NFR-01")


@pytest.mark.parametrize(
    "image",
    [
        "nginx:alpine",
        "nginx:latest",
        "nginx",
        "localhost:5000/team/app:v1",
        "example/app@sha256:abc123",
        "example/app:v1@sha256:abc123",
    ],
)
@pytest.mark.skipif(shutil.which("helm") is None, reason="offline Helm unavailable")
async def test_actual_render_identity_preservation_and_idempotence(image):
    source = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
        - name: app
          image: {image}
"""
    files = {
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.0.0\n",
        "helm/app/templates/app.yaml": source,
    }
    result, records = repair_image_values(files, await render_charts(files))
    assert records and records[0]["reason"] == "identity_preserved_no_trust_claim"
    observed = await render_charts(result)
    assert (
        observed["helm/app/templates/app.yaml"][0]["spec"]["template"]["spec"][
            "containers"
        ][0]["image"]
        == image
    )
    assert repair_image_values(result, observed) == (result, [])
    assert image in source


@pytest.mark.parametrize(
    "image",
    ["", "{{ .Values.image }}", "example/app:", "example/app@", "example/app bad"],
)
def test_unsupported_images(image):
    assert image_parts(image) is None


async def test_plain_manifests_unchanged_and_existing_bindings_preserved():
    files = {"k8s/app.yaml": "image: nginx:latest\n"}
    assert repair_image_values(files, {}) == (files, [])


@pytest.mark.skipif(shutil.which("helm") is None, reason="offline Helm unavailable")
async def test_image_overrides_remain_useful():
    files = {
        "helm/app/Chart.yaml": "apiVersion: v2\nname: app\nversion: 1.0.0\n",
        "helm/app/templates/app.yaml": (
            "apiVersion: batch/v1\nkind: Job\nmetadata:\n  name: app\n"
            "spec:\n  template:\n    spec:\n      containers:\n"
            "        - name: app\n          image: nginx:latest\n"
        ),
    }
    result, _ = repair_image_values(files, await render_charts(files))
    values = yaml.safe_load(result["helm/app/values.yaml"])
    image = next(iter(values["infraarchImages"].values()))
    image["tag"] = "alpine"
    result["helm/app/values.yaml"] = yaml.safe_dump(values)
    with TemporaryDirectory() as directory:
        root = Path(directory)
        for path, content in result.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        output = await ProcessToolRunner().run_command(
            "helm", ["helm", "template", "app", "helm/app"], root
        )
        assert output.exit_code == 0
        assert 'image: "nginx:alpine"' in output.stdout
