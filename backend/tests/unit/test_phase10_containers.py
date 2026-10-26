"""NFR-01/04: container configuration contracts, without building images."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.req("NFR-01", "NFR-04", "FR-P-04")


def test_backend_runtime_is_nonroot_and_downloads_are_verified():
    source = (ROOT / "backend/Dockerfile").read_text()
    assert "USER 10001:10001" in source
    assert "trivy/releases/download/v0.69.3/" in source
    assert source.index("sha256sum -c trivy.sha256") < source.index("tar -xzf trivy_")
    assert "checkov==3.3.21" in source and "1.16.4" in source
    assert "-c requirements.lock -e ." in source
    assert "ARG API_KEY" not in source and "ARG CREDENTIAL" not in source


def test_compose_keeps_owner_out_of_backend_and_mirror_readonly():
    services = yaml.safe_load((ROOT / "docker-compose.full.yml").read_text())[
        "services"
    ]
    assert (
        "infraarch_owner"
        not in services["backend"]["environment"]["MIGRATION_DATABASE_URL"]
    )
    assert (
        "infraarch_owner"
        in services["migrate"]["environment"]["MIGRATION_DATABASE_URL"]
    )
    assert all(value.endswith(":ro") for value in services["backend"]["volumes"])
    assert services["frontend"]["ports"] == ["127.0.0.1:8080:8080"]
    assert "ports" not in services["postgres"] and "ports" not in services["backend"]


def test_frontend_preserves_sse_and_build_context_excludes_secrets():
    proxy = (ROOT / "docker/frontend/default.conf").read_text()
    assert (
        "proxy_buffering off" in proxy and "proxy_set_header Host $http_host" in proxy
    )
    dockerfile = (ROOT / "frontend/Dockerfile").read_text()
    assert "npm ci --ignore-scripts" in dockerfile and "USER 101:101" in dockerfile
    ignored = (ROOT / ".dockerignore").read_text().splitlines()
    assert "**" in ignored and "**/.env*" in ignored
    assert not any(
        value.startswith("!") and (".cache" in value or ".env" in value)
        for value in ignored
    )
