"""Measured-credit guard and an informational first-cost schedule projection."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import httpx
from pydantic import SecretStr


class CreditError(RuntimeError):
    """Fixed text only: never expose a provider response or request."""


@dataclass(frozen=True)
class CreditSnapshot:
    usage: Decimal | None = None
    remaining: Decimal | None = None
    supported: bool = False
    key_remaining: Decimal | None = field(default=None, compare=False)
    account_remaining: Decimal | None = field(default=None, compare=False)


def numeric(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    number = Decimal(str(value))
    return number if number.is_finite() else None


class CreditReader:
    def __init__(self, client: httpx.AsyncClient, base_url: str, key: SecretStr):
        self.client, self.base_url, self.key = client, base_url.rstrip("/"), key

    async def account_balance(self) -> Decimal | None:
        try:
            response = await self.client.get(
                self.base_url + "/credits",
                headers={"Authorization": "Bearer " + self.key.get_secret_value()},
            )
            if response.status_code != 200:
                return None
            body = response.json()
            data = body.get("data") if isinstance(body, dict) else None
            if not isinstance(data, dict):
                return None
            credits, usage = (
                numeric(data.get("total_credits")),
                numeric(data.get("total_usage")),
            )
            if credits is None or usage is None or credits < 0 or usage < 0:
                return None
            return max(Decimal(0), credits - usage)
        except (httpx.HTTPError, ValueError):
            return None

    async def read(self) -> CreditSnapshot:
        try:
            response = await self.client.get(
                self.base_url + "/key",
                headers={"Authorization": "Bearer " + self.key.get_secret_value()},
            )
            if response.status_code in {404, 405}:
                account = await self.account_balance()
                return CreditSnapshot(
                    remaining=account,
                    supported=account is not None,
                    account_remaining=account,
                )
            if response.status_code != 200:
                raise CreditError("Key-info probe failed; no further runs submitted.")
            body = response.json()
            data = body.get("data") if isinstance(body, dict) else None
            if not isinstance(data, dict):
                raise CreditError("Key-info response is unusable; stopping.")
            usage = numeric(data.get("usage"))
            remaining = numeric(data.get("limit_remaining"))
            effective = data.get("effective_budget")
            effective_remaining = (
                numeric(effective.get("remaining_usd"))
                if isinstance(effective, dict)
                else None
            )
            if (
                usage is None
                or usage < 0
                or (data.get("limit_remaining") is not None and remaining is None)
                or (
                    isinstance(effective, dict)
                    and effective.get("remaining_usd") is not None
                    and effective_remaining is None
                )
            ):
                raise CreditError("Key-info response is unusable; stopping.")
            account = await self.account_balance()
            values = [
                value
                for value in (remaining, effective_remaining, account)
                if value is not None
            ]
            return CreditSnapshot(
                usage,
                min(values) if values else None,
                True,
                key_remaining=remaining,
                account_remaining=account,
            )
        except (httpx.HTTPError, ValueError):
            raise CreditError(
                "Key-info probe failed; no further runs submitted."
            ) from None


def measured_cost(before: CreditSnapshot, after: CreditSnapshot) -> Decimal | None:
    if before.usage is None or after.usage is None or after.usage < before.usage:
        return None
    return after.usage - before.usage


@dataclass
class BudgetGuard:
    reserve: Decimal
    max_runs: int | None = None
    highest: Decimal = Decimal(0)
    submitted: int = 0

    def threshold(self, size: int = 1) -> Decimal:
        return max(
            self.reserve,
            2 * self.highest,
            Decimal("4.5") * self.highest if size == 3 else Decimal(0),
        )

    def reason(self, snapshot: CreditSnapshot, size: int = 1) -> str | None:
        if self.max_runs is not None and self.submitted + size > self.max_runs:
            return "Run cap reached; no partial concurrent cohort will be launched."
        if snapshot.remaining is None:
            return (
                "Remaining credit unknown; explicit --max-runs is required."
                if self.max_runs is None
                else None
            )
        if snapshot.remaining < self.threshold(size):
            return (
                "Remaining credit below the guard reserve; stopping before submission."
            )
        return None

    def observe(self, cost: Decimal | None) -> None:
        if cost is not None:
            self.highest = max(self.highest, cost)


def affordability(
    guard: BudgetGuard,
    snapshot: CreditSnapshot,
    cost: Decimal | None,
    schedule: list[int],
) -> dict:
    result = {
        "measured_first_run_cost_usd": float(cost) if cost is not None else None,
        "remaining_credit_usd": float(snapshot.remaining)
        if snapshot.remaining is not None
        else None,
        "planned_runs_remaining": sum(schedule),
        "run_cap_remaining": max(0, guard.max_runs - guard.submitted)
        if guard.max_runs is not None
        else None,
        "projected_further_runs": None,
        "assumption": "Projection at first measured cost; fresh guard checks decide.",
    }
    if cost is None or snapshot.remaining is None:
        return result
    simulation = BudgetGuard(
        guard.reserve, guard.max_runs, max(guard.highest, cost), guard.submitted
    )
    remaining = snapshot.remaining
    count = 0
    for size in schedule:
        if simulation.reason(CreditSnapshot(remaining=remaining, supported=True), size):
            break
        count += size
        simulation.submitted += size
        remaining -= cost * size
    result["projected_further_runs"] = count
    return result
