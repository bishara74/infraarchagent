"""Opt-in deterministic pipeline demo responses; ordinary stubs are untouched."""

import json

from app.domain.enums import Variant
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


class PipelineDemoStub(StubAdapter):
    def __init__(self, variant: Variant | None, policy: RetryPolicy) -> None:
        super().__init__("stub", policy)
        self.variant = variant

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
        files = {
            "terraform/main.tf": (
                'terraform { required_version = ">= 1.0" }\n'
                f"# Demo {self.variant.value} variant\n"
            )
        }
        return LLMResponse(
            json.dumps({"files": files, "notes": "Deterministic demo package"}),
            10,
            10,
            "end_turn",
        )
