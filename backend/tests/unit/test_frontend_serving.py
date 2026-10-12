from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.api.frontend import UI_HEADERS, register_frontend


@pytest.fixture
def dist(tmp_path: Path) -> Path:
    (tmp_path / "index.html").write_text('<html lang="en">UI</html>')
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/app.js").write_text("console.log('UI')")
    (tmp_path / "assets/app.css").write_text("html{color-scheme:dark}")
    return tmp_path


def client(dist: Path) -> httpx.AsyncClient:
    app = FastAPI()

    @app.get("/api/existing")
    async def api() -> dict[str, bool]:
        return {"ok": True}

    register_frontend(app, dist)
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    )


@pytest.mark.req("NFR-01", "FR-UI-01")
@pytest.mark.parametrize(
    "path", ["/", "/runs/x", "/runs/x/compare", "/runs/x/packages/cost"]
)
async def test_spa_routes_have_ui_headers(dist: Path, path: str) -> None:
    async with client(dist) as http:
        response = await http.get(path)
    assert response.status_code == 200
    assert response.text == '<html lang="en">UI</html>'
    for key, value in UI_HEADERS.items():
        assert response.headers[key] == value


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("path", ["/assets/app.js", "/assets/app.css"])
async def test_assets_have_ui_headers(dist: Path, path: str) -> None:
    async with client(dist) as http:
        response = await http.get(path)
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "text/html" not in response.headers["Content-Type"]


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "path",
    [
        "/assets/missing.js",
        "/missing.css",
        "/%2e%2e/private",
        "/assets/%2e%2e/%2e%2e/private",
    ],
)
async def test_missing_assets_and_traversal_never_fall_back(
    dist: Path, path: str
) -> None:
    async with client(dist) as http:
        response = await http.get(path)
    assert response.status_code == 404
    assert "UI</html>" not in response.text


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "path, status",
    [
        ("/api", 404),
        ("/api/missing", 404),
        ("/api/existing", 200),
        ("/docs", 200),
        ("/openapi.json", 200),
    ],
)
async def test_api_and_docs_remain_reserved(dist: Path, path: str, status: int) -> None:
    async with client(dist) as http:
        response = await http.get(path)
    assert response.status_code == status
    assert "Content-Security-Policy" not in response.headers
    if path == "/api/existing":
        assert response.json() == {"ok": True}


@pytest.mark.req("FR-UI-01")
async def test_missing_dist_needs_no_build(tmp_path: Path) -> None:
    async with client(tmp_path / "absent") as http:
        assert (await http.get("/")).status_code == 404
        assert (await http.get("/api/existing")).status_code == 200


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE"])
async def test_unknown_api_methods_preserve_404(dist: Path, method: str) -> None:
    async with client(dist) as http:
        response = await http.request(method, "/api/missing")
    assert response.status_code == 404
    assert "Content-Security-Policy" not in response.headers
