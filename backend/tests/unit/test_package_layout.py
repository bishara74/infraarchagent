import pytest

from app.domain.package_layout import (
    LAYOUT,
    classify_path,
    layout_guidance,
    package_structure_errors,
    required_types_missing,
)
from app.domain.plan import FileType


@pytest.mark.req("FR-G-02")
def test_table_covers_all_file_types_and_drives_prompt() -> None:
    assert set(LAYOUT) == set(FileType)
    guidance = layout_guidance()
    for kind, rule in LAYOUT.items():
        assert kind.value in guidance
        assert all(pattern in guidance for pattern in rule.required)


@pytest.mark.req("FR-G-02")
@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("terraform/main.tf", FileType.TERRAFORM),
        ("terraform/modules/web/main.tf", FileType.TERRAFORM),
        ("terraform/vars.tfvars", FileType.TERRAFORM),
        ("terraform/generated.tf.json", FileType.TERRAFORM),
        ("k8s/service.yaml", FileType.KUBERNETES),
        ("k8s/apps/service.yml", FileType.KUBERNETES),
        ("helm/web/Chart.yaml", FileType.HELM),
        ("helm/web/templates/deploy.yaml", FileType.HELM),
        ("docker/Dockerfile", FileType.DOCKERFILE),
        ("docker/web/Dockerfile", FileType.DOCKERFILE),
        ("jenkins/Jenkinsfile", FileType.JENKINS),
        ("nginx/site.conf", FileType.NGINX),
        ("ansible/playbook.yml", FileType.ANSIBLE),
        ("monitoring/prometheus/scrape.yaml", FileType.PROMETHEUS),
        ("monitoring/grafana/dashboard.json", FileType.GRAFANA),
    ],
)
def test_classification(path: str, kind: FileType) -> None:
    assert classify_path(path) is kind


@pytest.mark.req("FR-G-02")
def test_required_marker_is_distinct_from_allowed_supporting_files() -> None:
    assert required_types_missing(
        {"terraform/vars.tfvars": "x", "helm/web/values.yaml": "x"},
        [FileType.TERRAFORM, FileType.HELM],
    ) == [FileType.TERRAFORM, FileType.HELM]
    assert not required_types_missing(
        {"terraform/main.tf": "x", "helm/web/Chart.yaml": "x"},
        [FileType.TERRAFORM, FileType.HELM],
    )


@pytest.mark.req("FR-G-02")
def test_collects_unplanned_outside_empty_unsafe_and_missing() -> None:
    errors = package_structure_errors(
        {
            "terraform/main.tf": "",
            "k8s/web.yaml": "apiVersion: v1",
            "other.txt": "x",
            "../unsafe.tf": "x",
        },
        [FileType.TERRAFORM, FileType.HELM],
    )
    assert any("empty" in error for error in errors)
    assert any("kubernetes is not in plan" in error for error in errors)
    assert any("outside" in error for error in errors)
    assert any("unsafe" in error for error in errors)
    assert any("helm/<chart>/Chart.yaml" in error for error in errors)


@pytest.mark.req("FR-G-02")
def test_byte_and_count_limits_and_readme_exception() -> None:
    files = {f"terraform/f{i}.tf": "x" for i in range(81)}
    files["README.md"] = "readme"
    errors = package_structure_errors(files, [FileType.TERRAFORM])
    assert any("too many files" in error for error in errors)
    assert not any("README.md" in error for error in errors)
    errors = package_structure_errors(
        {"terraform/main.tf": "é" * 103000}, [FileType.TERRAFORM]
    )
    assert any("file limit" in error for error in errors)
    many = {f"terraform/f{i}.tf": "x" * 150000 for i in range(15)}
    errors = package_structure_errors(many, [FileType.TERRAFORM])
    assert any("package" in error and "limit" in error for error in errors)
