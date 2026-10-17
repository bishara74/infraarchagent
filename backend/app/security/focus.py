"""Bounded resource-focused findings with deterministic equal-severity rotation."""

from collections import defaultdict
from collections.abc import Sequence
from itertools import zip_longest

from app.domain.models import Violation

RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}


def focused_findings(
    findings: Sequence[Violation], resources: int, limit: int, iteration: int = 0
) -> list[Violation]:
    grouped: dict[str, list[Violation]] = defaultdict(list)
    for f in findings:
        grouped[f.resource].append(f)
    tiers: dict[int, list[str]] = defaultdict(list)
    for resource, entries in grouped.items():
        tiers[min(RANK[f.severity.value] for f in entries)].append(resource)
    chosen: list[str] = []
    for rank in sorted(tiers):
        names = sorted(tiers[rank])
        start = iteration * resources % len(names)
        chosen.extend(
            (names[start:] + names[:start])[: max(0, resources - len(chosen))]
        )
    ordered: list[Violation] = []
    for severity in range(5):
        streams = []
        for resource in chosen:
            entries = sorted(
                (f for f in grouped[resource] if RANK[f.severity.value] == severity),
                key=lambda f: (f.rule_id, f.file_path),
            )
            if entries:
                start = iteration * limit % len(entries)
                streams.append(entries[start:] + entries[:start])
        ordered.extend(f for row in zip_longest(*streams) for f in row if f is not None)
    return ordered[:limit]
