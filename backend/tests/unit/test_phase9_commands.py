"""The suite preserves one guard, exact order, and stops dependent work."""

import pytest

from scripts.run_phase9_benchmarks import execute, schedule


@pytest.mark.req("PR-01", "PR-03", "PR-04", "NFR-01")
@pytest.mark.parametrize(
    "mode,stop", [("stub", False), ("real", False), ("stub", True)]
)
async def test_shared_harness_sequence_and_guard_stop(mode, stop):
    calls = []

    class FakeHarness:
        output = None
        stop_reason = None

        async def pr01(self, runs, **kwargs):
            calls.append(("pr01", runs, kwargs["following"]))
            if stop:
                self.stop_reason = "guard stop"

        async def pr03(self):
            calls.append(("pr03",))

        async def pr04(self, run_id, repeat):
            calls.append(("pr04", run_id, repeat))

        def flush(self):
            calls.append(("flush",))

    harness = FakeHarness()
    harness.mode = mode

    async def seed():
        calls.append(("seed",))
        return {"run_id": "synthetic"}

    await execute(harness, seeder=seed)
    assert calls[0] == ("pr01", 10, [1, 3])
    if stop:
        assert calls == [("pr01", 10, [1, 3]), ("flush",)]
    elif mode == "stub":
        assert calls[1:] == [
            ("pr03",),
            ("seed",),
            ("pr04", "synthetic", 10),
            ("flush",),
        ]
    else:
        assert calls[1:] == [("pr03",), ("flush",)]
    assert sum(schedule()) == 14 and schedule()[-1] == 3
