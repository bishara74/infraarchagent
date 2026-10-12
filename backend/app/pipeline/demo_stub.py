"""Opt-in deterministic pipeline demo responses; ordinary stubs are untouched."""

import json
import re
from typing import Literal

from app.domain.enums import Variant
from app.domain.paths import validate_relative_path
from app.llm.base import LLMResponse, RetryPolicy
from app.llm.stub import StubAdapter

DEMO_PLAN = {
    "cloud_provider": "aws",
    "services": [
        {"name": "web", "aws_service": "EC2", "purpose": "Host a demo web service"}
    ],
    "dependencies": [],
    "network": {
        "public_services": ["web"],
        "private_services": [],
        "ingress": ["HTTPS 443"],
        "notes": "Demo only",
    },
    "storage": [],
    "file_types": ["terraform"],
    "ambiguities": [],
}

REVIEW_FAILURE = 'output "review_demo" {\n  value = local.review_demo\n}\n'
REVIEW_FIX = 'locals {\n  review_demo = "fixed"\n}\n'


def demo_file(variant: Variant, scenario: Literal["clean", "review"] = "clean") -> str:
    source = (
        f'terraform {{ required_version = ">= 1.0" }}\n# Demo {variant.value} variant\n'
    )
    if scenario == "review" and variant == Variant.SECURITY:
        source += REVIEW_FAILURE
    return source


class PipelineDemoStub(StubAdapter):
    def __init__(
        self,
        variant: Variant | None,
        policy: RetryPolicy,
        *,
        model: str = "stub",
        scenario: Literal["clean", "review"] = "clean",
    ) -> None:
        super().__init__(model, policy)
        self.variant = variant
        self.scenario = scenario

    async def send_prompt(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_output_tokens: int,
        timeout: float,
    ) -> LLMResponse:
        self.prompts.append(prompt)
        if self.variant is None:
            return LLMResponse(json.dumps(DEMO_PLAN), 10, 10, "end_turn")
        files = {"terraform/main.tf": demo_file(self.variant, self.scenario)}
        return LLMResponse(
            json.dumps({"files": files, "notes": "Deterministic demo package"}),
            10,
            10,
            "end_turn",
        )


class PipelineDemoFixStub(StubAdapter):
    """Return the real fixer shape; repair only the known demo validation target."""

    def __init__(self, policy: RetryPolicy, *, scenario: Literal["clean", "review"]):
        super().__init__("stub", policy)
        self.scenario = scenario

    async def send_prompt(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_output_tokens: int,
        timeout: float,
    ) -> LLMResponse:
        self.prompts.append(prompt)
        path = validate_relative_path(
            prompt.splitlines()[0].removeprefix("Requested file: ")
        )
        opening = re.search(r'<file_content id="([a-zA-Z0-9_-]+)">\n', prompt)
        if opening is None:
            raise ValueError("invalid demo fix prompt")
        marker = opening.group(1)
        content = prompt[opening.end() :].split(f'\n</file_content id="{marker}">', 1)[
            0
        ]
        failures_tag = f'<validation_failures id="{marker}">\n'
        failures = (
            json.loads(
                prompt.split(failures_tag, 1)[1].split(
                    f'\n</validation_failures id="{marker}">', 1
                )[0]
            )
            if failures_tag in prompt
            else []
        )
        repair = (
            self.scenario == "review"
            and path == "terraform/main.tf"
            and REVIEW_FAILURE in content
            and REVIEW_FIX not in content
            and any(
                item.get("check_id") == "terraform.local_ref"
                and item.get("file_path") == path
                for item in failures
            )
        )
        if repair:
            content += REVIEW_FIX
        return LLMResponse(
            json.dumps(
                {
                    "file": {"path": path, "content": content},
                    "new_files": {},
                    "fixes": [
                        {
                            "rule_id": "terraform.local_ref",
                            "resource": "review_demo",
                            "summary": "Declare the missing demo local.",
                        }
                    ]
                    if repair
                    else [],
                }
            ),
            10,
            10,
            "end_turn",
        )
