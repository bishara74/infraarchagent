"""PR-01/NFR-01: compact exports and legacy telemetry CSV interoperability."""

import csv
import json

import httpx
import pytest

from scripts.benchmark import Harness, compact_csv_rows, load_reference
from scripts.phase9_report import read_csv, write_csv

pytestmark = pytest.mark.req("PR-01", "NFR-01")


def test_legacy_oversized_csv_and_json_references_match(tmp_path):
    row = {"complete": True, "seconds": 123.5, "telemetry": "x" * 262535}
    json_path = tmp_path / "results.json"
    json_path.write_text(json.dumps({"runs": [row]}))
    csv_path = tmp_path / "results.csv"
    write_csv(csv_path, [row])
    before = csv.field_size_limit()
    assert load_reference(csv_path) == load_reference(json_path)
    assert csv.field_size_limit() == before
    bad = tmp_path / "bad.csv"
    write_csv(bad, [{"complete": "True", "seconds": "bad"}])
    with pytest.raises(ValueError):
        load_reference(bad)
    assert csv.field_size_limit() == before


async def test_compact_harness_export_keeps_full_json_telemetry(tmp_path):
    row = {
        "measurement": "pr01",
        "run_id": "fixture",
        "complete": True,
        "seconds": 1.0,
        "run_status": "partial_success",
        "telemetry": [{"blob": "x" * 262535}],
        "generator_attempt_details": [{"blob": "x" * 140000}],
        "generator_attempts_by_format_reason": {"none": 3},
    }
    async with httpx.AsyncClient() as client:
        harness = Harness(client, output=tmp_path)
        harness.rows = [row]
        harness.flush()
    assert b"\r\n" not in (tmp_path / "results.csv").read_bytes()
    result = read_csv(tmp_path / "results.csv")[0]
    assert "telemetry" not in result and "generator_attempt_details" not in result
    assert json.loads(result["generator_attempts_by_format_reason"]) == {"none": 3}
    assert max(map(len, result.values())) < 128000
    assert result["details_json"] == "results.json#runs/0"
    assert json.loads((tmp_path / "results.json").read_text())["runs"][0] == row
    assert (
        compact_csv_rows(
            [{**row, "generator_attempts_by_format_reason": {"x": "y" * 20000}}]
        )[0]["generator_attempts_by_format_reason"]
        is None
    )
