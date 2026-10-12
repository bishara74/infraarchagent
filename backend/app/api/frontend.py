"""Optional local UI delivery, registered after the API routes."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Match
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

UI_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self'; font-src 'self'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}
DEFAULT_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"


def _missing() -> JSONResponse:
    return JSONResponse({"detail": "Not Found"}, status_code=404, headers=UI_HEADERS)


class _UIAssets(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code == 404:
                return _missing()
            raise
        response.headers.update(UI_HEADERS)
        return response


class _SPARoute(APIRoute):
    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        path = scope.get("path", "")
        if path == "/api" or path.startswith("/api/"):
            return Match.NONE, {}
        return super().matches(scope)


def register_frontend(app: FastAPI, dist: Path) -> None:
    """A missing build adds no routes; tests may supply a temporary dist."""
    root = dist.resolve()
    if not (root / "index.html").is_file():
        return
    if (root / "assets").is_dir():
        app.mount("/assets", _UIAssets(directory=root / "assets"), name="ui-assets")

    async def ui(path: str) -> Response:
        if path == "api" or path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        if any(part.startswith(".") for part in path.split("/") if part):
            return _missing()
        candidate = (root / path).resolve()
        if not candidate.is_relative_to(root):
            return _missing()
        if candidate.is_file():
            return FileResponse(candidate, headers=UI_HEADERS)
        if Path(path).suffix or path == "assets" or path.startswith("assets/"):
            return _missing()
        return FileResponse(root / "index.html", headers=UI_HEADERS)

    app.router.routes.append(
        _SPARoute("/{path:path}", ui, methods=["GET"], include_in_schema=False)
    )
