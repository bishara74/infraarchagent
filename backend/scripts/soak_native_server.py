# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Private Uvicorn entrypoint for the offline native soak workload."""

import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import uvicorn

from app.core import bind
from app.core.config import get_settings
from app.core.diagnostics import enable_fault_diagnostics
from app.domain.enums import LLMProvider
from app.pipeline.demo_stub import PipelineDemoFixStub, PipelineDemoStub
from tests.database_safety import assert_test_database_settings

FIXTURES = Path(__file__).resolve().parents[1] / "tests/fixtures/security"
DEPLOYMENT = "k8s/deployment.yaml"


def configure_fixtures() -> None:
    vulnerable = (
        (FIXTURES / "vulnerable" / DEPLOYMENT)
        .read_text()
        .replace(": vulnerable", ": web")
    )
    fixed = (FIXTURES / "fixed" / DEPLOYMENT).read_text().replace(": fixed", ": web")
    send_demo = PipelineDemoStub.send_prompt
    send_fix = PipelineDemoFixStub.send_prompt

    async def demo(self, prompt, **kwargs):
        result = await send_demo(self, prompt, **kwargs)
        data = json.loads(result.text)
        if self.variant is None:
            data["file_types"].append("kubernetes")
        else:
            data["files"][DEPLOYMENT] = vulnerable
        return replace(result, text=json.dumps(data))

    async def fix(self, prompt, **kwargs):
        result = await send_fix(self, prompt, **kwargs)
        data = json.loads(result.text)
        if data["file"]["path"] != DEPLOYMENT:
            return result
        data["file"]["content"] = fixed
        return replace(result, text=json.dumps(data))

    PipelineDemoStub.send_prompt = demo
    PipelineDemoFixStub.send_prompt = fix


def main() -> None:
    enable_fault_diagnostics()
    if os.environ.get("INFRAARCH_TEST_BOOTSTRAP") != "1":
        raise SystemExit("The soak server requires the dotenv-disabled test bootstrap.")
    settings = get_settings()
    assert_test_database_settings(settings)
    if settings.llm_provider != LLMProvider.STUB:
        raise SystemExit("The soak server requires the stub provider.")
    if settings.api_key is None:
        raise SystemExit("The soak server requires a per-soak API key.")

    configure_fixtures()
    bind.validated_open_bind = "127.0.0.1"
    from app.main import app

    uvicorn.run(app, fd=int(sys.argv[1]), workers=1)


if __name__ == "__main__":
    main()
