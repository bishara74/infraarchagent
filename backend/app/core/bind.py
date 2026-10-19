"""Open mode requires a bind validated by the supported server launcher."""

validated_open_bind: str | None = None


def check_open_bind(api_key: object) -> None:
    if api_key is None and validated_open_bind != "127.0.0.1":
        raise RuntimeError(
            "API_KEY is unset: open mode requires a verified 127.0.0.1 bind. "
            "Use python -m app.server --host 127.0.0.1, or configure API_KEY."
        )
