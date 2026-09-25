"""Deterministic scripted provider for offline tests and timing format checks."""

import asyncio
import random
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from app.llm.base import LLMAdapter, LLMResponse, RetryPolicy, extract_json_object
from app.llm.errors import LLMPermanentError

StubReply = str | LLMResponse
StubStep = StubReply | BaseException | tuple[float, StubReply]


class StubAdapter(LLMAdapter):
    provider = "stub"

    def __init__(
        self,
        model: str = "stub",
        policy: RetryPolicy | None = None,
        *,
        script: Sequence[StubStep] | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(
            model,
            policy or RetryPolicy(30, 3, 150, 1, 16000),
            sleep=sleep,
            clock=clock,
            rng=rng,
        )
        self._script = list(script) if script is not None else None
        self.prompts: list[str] = []

    async def send_prompt(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_output_tokens: int,
        timeout: float,
    ) -> LLMResponse:
        self.prompts.append(prompt)
        if self._script is None:
            return LLMResponse('{"files":{"stub.txt":"ok"}}', 10, 10, "end_turn")
        if not self._script:
            raise LLMPermanentError("stub_script_exhausted")
        step = self._script.pop(0)
        if isinstance(step, BaseException):
            raise step
        if isinstance(step, tuple):
            delay, step = step
            await self._sleep(delay)
        return step if isinstance(step, LLMResponse) else LLMResponse(step)

    def parse_response(self, response: LLMResponse) -> dict[str, Any]:
        return extract_json_object(response.text)
