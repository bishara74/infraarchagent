"""Validated local server entrypoint. Key-authenticated direct Uvicorn is unchanged."""

import argparse

import uvicorn

from app.core import bind
from app.core.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    settings = get_settings()
    bind.validated_open_bind = args.host
    bind.check_open_bind(settings.api_key)
    uvicorn.run("app.main:app", host=args.host, port=args.port, workers=1)


if __name__ == "__main__":
    main()
