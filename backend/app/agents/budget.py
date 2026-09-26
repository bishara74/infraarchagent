"""One monotonic time budget shared by an agent's LLM calls."""

import math
import time
from collections.abc import Callable


class AgentBudget:
    def __init__(
        self, total_seconds: float, *, clock: Callable[[], float] = time.monotonic
    ) -> None:
        if not math.isfinite(total_seconds) or total_seconds <= 0:
            raise ValueError("agent budget must be a finite positive number of seconds")
        self.total_seconds = total_seconds
        self._clock = clock
        self._started = clock()

    def elapsed(self) -> float:
        return max(0.0, self._clock() - self._started)

    def remaining(self) -> float:
        return max(0.0, self.total_seconds - self.elapsed())

    def expired(self) -> bool:
        return self.remaining() <= 0
