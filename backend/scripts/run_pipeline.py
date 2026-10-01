"""Watch one live pipeline run through the public API only."""

import asyncio
import json
import os
import time
from typing import Any

import httpx


async def watch_pipeline(
    text: str, *, client: httpx.AsyncClient,
    api_url: str = "http://localhost:8000",
    config: dict[str, str] | None = None,
) -> tuple[str, dict[str, str]]:
    started = time.monotonic()
    body: dict[str, Any] = {"text": text}
    if config:
        body["config"] = config
    response = await client.post(f"{api_url}/api/pipeline/run", json=body)
    if response.status_code != 202:
        error = response.json()
        print(f"HTTP {response.status_code}: {error.get('message', 'request failed')}")
        raise RuntimeError("pipeline request rejected")
    accepted = response.json()
    run_id: str = accepted["run_id"]
    print(f"Run {run_id}")
    stream_url = f"{api_url}{accepted['stream_url']}"
    cursor: str | None = None
    statuses: dict[str, str] = {}
    run_status = "created"
    while True:
        headers = {"Last-Event-ID": cursor} if cursor is not None else {}
        try:
            async with client.stream("GET", stream_url, headers=headers) as stream:
                stream.raise_for_status()
                event_id: str | None = None
                data: str | None = None
                async for line in stream.aiter_lines():
                    if line.startswith("id: "):
                        event_id = line[4:]
                    elif line.startswith("data: "):
                        data = line[6:]
                    elif line == "" and data is not None:
                        item = json.loads(data)
                        cursor = event_id or str(item["seq"])
                        variant = item.get("variant")
                        if item["kind"] == "run_status":
                            run_status = item["status"]
                        elif item["kind"] == "package_status" and variant:
                            statuses[variant] = item["status"]
                        detail = f" package {variant}" if variant else ""
                        previous = item.get("previous_status")
                        change = (
                            f"{previous} → {item['status']}"
                            if previous else item["status"]
                        )
                        elapsed = time.monotonic() - started
                        print(
                            f"[+{elapsed:.1f}s] #{cursor} {item['agent']}{detail}: "
                            f"{change} — {item.get('message') or ''}"
                        )
                        event_id = data = None
        except (httpx.HTTPError, OSError):
            pass
        if run_status in {"success", "partial_success", "failed"}:
            break
        await asyncio.sleep(1)
    elapsed = time.monotonic() - started
    summary = ", ".join(f"{key}={value}" for key, value in sorted(statuses.items()))
    print(f"Final: {run_status}; {summary}; {elapsed:.1f}s")
    return run_status, statuses


async def main() -> None:
    text = os.environ.get("PIPELINE_TEXT", "")
    if not text:
        raise SystemExit("Set TEXT when calling make run-pipeline")
    config = {
        key: value
        for key, value in (
            ("provider", os.environ.get("CONFIG_PROVIDER")),
            ("model", os.environ.get("CONFIG_MODEL")),
        )
        if value
    }
    api_url = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
    async with httpx.AsyncClient(timeout=None) as client:
        await watch_pipeline(text, client=client, api_url=api_url, config=config)


if __name__ == "__main__":
    asyncio.run(main())
