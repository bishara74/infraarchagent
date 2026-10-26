"""Allowlisted review history projections and downloadable exports."""

import csv
import io
import json
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.safety import PublicDataSafety
from app.db.repositories.review_history import ReviewHistoryRepository
from app.domain.review_categories import CATEGORIES

FIELDS = (
    "run_id",
    "variant",
    "label_before",
    "label_after",
    "decision",
    "category",
    "reason",
    "reviewer",
    "timestamp",
)


class ReviewHistoryService:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], safety: PublicDataSafety
    ):
        self.sessions, self.safety = sessions, safety

    async def read(
        self,
        filters: dict[str, Any],
        page: int | None = None,
        *,
        include_ids: bool = True,
    ) -> dict[str, Any]:
        async with self.sessions() as session:
            rows, total = await ReviewHistoryRepository(session).read(
                filters, page=page
            )
        decisions = []
        for row in rows:
            details = row["details"] if isinstance(row["details"], dict) else {}
            category = details.get("category")
            decisions.append(
                self.safety.value(
                    {
                        **(
                            {"decision_id": str(row["event_id"])} if include_ids else {}
                        ),
                        "run_id": str(row["run_id"]),
                        "variant": row["variant"],
                        "label_before": row["previous_state"],
                        "label_after": row["new_state"],
                        "decision": row["decision"],
                        "category": category if category in CATEGORIES else None,
                        "reason": details.get("reason"),
                        "reviewer": details.get("reviewer_name"),
                        "timestamp": row["timestamp"].isoformat(),
                    }
                )
            )
        return {
            "items": decisions,
            "total": total,
            "page": page,
            "page_size": 25,
            "filters": filters,
        }

    async def export(self, filters: dict[str, Any], format: str) -> str:
        history = await self.read(filters, include_ids=False)
        metadata = {
            "schema_version": 1,
            "exported_at": datetime.now(UTC).isoformat(),
            "filters": filters,
            "count": history["total"],
        }
        if format == "json":
            return json.dumps(
                {"metadata": metadata, "decisions": history["items"]},
                ensure_ascii=False,
            )
        output = io.StringIO(newline="")
        for key, value in metadata.items():
            output.write(f"# {key}: {json.dumps(value, ensure_ascii=False)}\r\n")
        writer = csv.writer(output)
        writer.writerow(FIELDS)
        for item in history["items"]:
            # Quoting alone does not prevent spreadsheet formula execution.
            cells = [item.get(field) for field in FIELDS]
            writer.writerow(
                [
                    "'" + value
                    if isinstance(value, str)
                    and value.lstrip().startswith(
                        ("=", "+", "-", "@", "\t", "\r", "\n")
                    )
                    else value
                    for value in cells
                ]
            )
        return output.getvalue()

    async def insights(self, filters: dict[str, Any]) -> dict[str, Any]:
        async with self.sessions() as session:
            rows, total = await ReviewHistoryRepository(session).read(filters)
        categories: Counter[str] = Counter()
        variants: Counter[str] = Counter()
        decisions: Counter[str] = Counter()
        rules: Counter[str] = Counter()
        accepted_rules: Counter[str] = Counter()
        accepted_risk_total = 0
        rejected = available = 0
        for row in rows:
            details = row["details"] if isinstance(row["details"], dict) else {}
            category = details.get("category")
            categories[category if category in CATEGORIES else "not_recorded"] += 1
            variant = row["variant"]
            variants[
                variant
                if variant in {"cost", "performance", "security"}
                else "not_recorded"
            ] += 1
            decisions[row["decision"]] += 1
            if row["decision"] == "approve" and category == "accepted_risk":
                accepted_risk_total += 1
                blocking = details.get("remaining_blocking_rules")
                if isinstance(blocking, list) and all(
                    isinstance(rule, str) for rule in blocking
                ):
                    accepted_rules.update(set(blocking))
            if row["decision"] == "reject":
                rejected += 1
                blocking = details.get("remaining_blocking_rules")
                if isinstance(blocking, list) and all(
                    isinstance(rule, str) for rule in blocking
                ):
                    available += 1
                    rules.update(set(blocking))

        def groups(counts: Counter[str], key: str) -> list[dict[str, Any]]:
            return [
                {"value": value, "count": count, "filters": {**filters, key: value}}
                for value, count in sorted(
                    counts.items(), key=lambda pair: (-pair[1], pair[0])
                )
            ]

        result: dict[str, Any] = self.safety.value(
            {
                "total": total,
                "filters": filters,
                "by_category": groups(categories, "category"),
                "by_variant": groups(variants, "variant"),
                "by_decision": groups(decisions, "decision"),
                "blocking_rules": [
                    {
                        "rule_id": rule,
                        "count": count,
                        "filters": {
                            **filters,
                            "decision": "reject",
                            "blocking_rule": rule,
                        },
                    }
                    for rule, count in sorted(
                        rules.items(), key=lambda pair: (-pair[1], pair[0])
                    )
                ],
                "accepted_risk_total": accepted_risk_total,
                "accepted_risk_rules": [
                    {
                        "rule_id": rule,
                        "count": count,
                        "filters": {
                            **filters,
                            "decision": "approve",
                            "category": "accepted_risk",
                            "blocking_rule": rule,
                        },
                    }
                    for rule, count in sorted(
                        accepted_rules.items(), key=lambda pair: (-pair[1], pair[0])
                    )
                ],
                "rejected_total": rejected,
                "blocking_snapshot_available": available,
                "blocking_snapshot_unavailable": rejected - available,
            }
        )
        return result
