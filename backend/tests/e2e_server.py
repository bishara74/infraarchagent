"""Isolated browser server with mocked provider HTTP; never a production entrypoint."""

import asyncio
import json

import httpx
import httpx2
import openai
import uvicorn
from sqlalchemy import text

from app.core import bind
from app.core.config import get_settings
from app.db.session import make_owner_engine
from app.domain.enums import Variant
from app.llm.base import RetryPolicy
from app.pipeline.demo_stub import DEMO_PLAN, PipelineDemoFixStub, demo_file


async def prepare() -> None:
    settings = get_settings()
    # Explicitly refuse anything except the test database, without printing URLs.
    from tests.database_safety import assert_test_database_settings

    assert_test_database_settings(settings)
    engine = make_owner_engine(settings, test=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "TRUNCATE users, auth_sessions, provider_credentials, "
                    "llm_settings, "
                    "pipeline_runs, generated_packages, agent_events, "
                    "user_preferences, user_recent_runs RESTART IDENTITY CASCADE"
                )
            )
    finally:
        await engine.dispose()


async def completion(request: httpx2.Request) -> httpx2.Response:
    body = json.loads(request.content)
    schema = body.get("response_format", {}).get("json_schema", {}).get("name")
    if schema == "generator_package":
        system = str(body["messages"][0]["content"])
        variant = (
            Variant.SECURITY
            if "Optimise for security." in system
            else Variant.PERFORMANCE
            if "Optimise for performance." in system
            else Variant.COST
        )
        output = {
            "files": [
                {"path": "terraform/main.tf", "content": demo_file(variant, "review")}
            ],
            "notes": "Mocked provider HTTP demo",
        }
    elif schema == "fix_patch":
        prompt = body["messages"][-1]["content"]
        result = await PipelineDemoFixStub(
            RetryPolicy(1, 1, 10, 0, 1000), scenario="clean"
        ).send_prompt(prompt, max_output_tokens=1000, timeout=1)
        output = json.loads(result.text)
        output["new_files"] = []
        output["edits"] = []
        output.setdefault("fixes", [])
    else:
        output = DEMO_PLAN
    return httpx2.Response(
        200,
        json={
            "id": "e2e-mock",
            "object": "chat.completion",
            "created": 1,
            "model": body["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": json.dumps(output)},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        },
    )


def catalog(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/models"):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "committee/model",
                        "name": "Committee model (mock)",
                        "context_length": 32768,
                        "pricing": {"prompt": "0.000001", "completion": "0.000002"},
                        "supported_parameters": ["reasoning", "structured_outputs"],
                    }
                ]
            },
        )
    return httpx.Response(
        200,
        json={
            "data": {
                "limit_remaining": 10,
                "usage": 0,
                "total_credits": 10,
                "total_usage": 0,
            }
        },
    )


def main() -> None:
    asyncio.run(prepare())
    original = openai.AsyncOpenAI

    def mocked(*args, **kwargs):
        kwargs["http_client"] = httpx2.AsyncClient(
            transport=httpx2.MockTransport(completion)
        )
        return original(*args, **kwargs)

    openai.AsyncOpenAI = mocked
    bind.validated_open_bind = "127.0.0.1"
    from app.main import app

    app.state.provider_http = httpx.AsyncClient(transport=httpx.MockTransport(catalog))
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
