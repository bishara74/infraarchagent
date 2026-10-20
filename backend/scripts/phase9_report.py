"""Offline report rendering: measured values only, unknowns remain unknown."""

import csv
import math
import statistics
import sys
from pathlib import Path
from typing import Any


def statistics_for(values: list[float]) -> dict[str, float | int | None]:
    selected = sorted(value for value in values if math.isfinite(value) and value >= 0)
    return {
        "count": len(selected),
        "median": statistics.median(selected) if selected else None,
        "p90": selected[math.ceil(0.9 * len(selected)) - 1] if selected else None,
        "max": max(selected) if selected else None,
    }


def write_csv(
    path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None
) -> None:
    columns = fields or list(dict.fromkeys(key for row in rows for key in row))
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def summary(path: Path, title: str, status: str, lines: list[str]) -> None:
    path.write_text(
        f"# {title}\n\nStatus: **{status}**\n\n" + "\n\n".join(lines) + "\n"
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    """Historical telemetry cells exceed the stdlib's default 128 KiB limit."""
    previous = csv.field_size_limit()
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            break
        except OverflowError:
            limit //= 10
    try:
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))
    finally:
        csv.field_size_limit(previous)
