"""Pure guard boundaries and offline provider key-info shapes."""

from decimal import Decimal

import httpx
import pytest
from pydantic import SecretStr

from scripts.phase9_budget import (
    BudgetGuard,
    CreditError,
    CreditReader,
    CreditSnapshot,
    affordability,
    measured_cost,
)

D = Decimal


@pytest.mark.req("NFR-01", "PR-03")
def test_exact_sequential_and_cohort_reserves_and_cap():
    guard = BudgetGuard(D(1), 14, highest=D(2))
    assert guard.threshold() == 4
    assert guard.threshold(3) == 9
    assert guard.reason(CreditSnapshot(remaining=D(4))) is None
    assert guard.reason(CreditSnapshot(remaining=D("3.99")))
    assert guard.reason(CreditSnapshot(remaining=D(9)), 3) is None
    assert guard.reason(CreditSnapshot(remaining=D("8.99")), 3)
    guard.submitted = 12
    assert guard.reason(CreditSnapshot(remaining=D(100)), 3)
    assert BudgetGuard(D(1)).reason(CreditSnapshot())
    assert BudgetGuard(D(1), 4).reason(CreditSnapshot()) is None


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "remaining,cost,schedule,expected",
    [
        ("12", "2", [1, 1, 3], 2),
        ("13", "2", [1, 1, 3], 5),
        ("1", "0", [1, 3], 4),
        ("0.99", "0", [1, 3], 0),
        (None, "1", [1, 3], None),
        ("10", None, [1, 3], None),
    ],
)
def test_advisory_schedule_and_zero_unknown(remaining, cost, schedule, expected):
    guard = BudgetGuard(D(1), 14, submitted=1)
    report = affordability(
        guard,
        CreditSnapshot(remaining=D(remaining) if remaining else None),
        D(cost) if cost is not None else None,
        schedule,
    )
    assert report["projected_further_runs"] == expected
    assert guard.submitted == 1 and guard.highest == 0
    guard.observe(D(5))
    assert guard.reason(CreditSnapshot(remaining=D(9)))


@pytest.mark.req("NFR-01")
async def test_key_info_effective_budget_lifetime_usage_and_canary():
    key = SecretStr("budget-canary-key")
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "data": {
                    "label": key.get_secret_value(),
                    "usage": 12.5,
                    "limit_remaining": 9,
                    "effective_budget": {
                        "remaining_usd": 3,
                        "budget_id": key.get_secret_value(),
                    },
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        snapshot = await CreditReader(
            client, "https://openrouter.ai/api/v1", key
        ).read()
    assert snapshot == CreditSnapshot(D("12.5"), D(3), True)
    assert key.get_secret_value() not in repr(snapshot)
    assert requests[0].headers["authorization"] == "Bearer " + key.get_secret_value()
    assert measured_cost(snapshot, CreditSnapshot(D(13), D(100), True)) == D(".5")
    assert measured_cost(snapshot, CreditSnapshot(D(1), D(100), True)) is None


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "status,body,error",
    [
        (404, {}, False),
        (401, {"error": "budget-canary-key"}, True),
        (500, {"error": "budget-canary-key"}, True),
        (200, {"data": {"usage": True}}, True),
        (200, {"data": {"usage": 1, "limit_remaining": "bad"}}, True),
        (200, {"data": {"usage": 1, "limit_remaining": None}}, False),
    ],
)
async def test_unknown_and_failed_credit_probe(status, body, error):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(status, json=body))
    ) as client:
        reader = CreditReader(client, "http://fake", SecretStr("budget-canary-key"))
        if error:
            with pytest.raises(CreditError) as caught:
                await reader.read()
            assert "budget-canary-key" not in str(caught.value)
        else:
            assert (await reader.read()).remaining is None
