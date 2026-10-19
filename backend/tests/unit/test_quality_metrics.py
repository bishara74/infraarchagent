"""FR-V-04/NFR-01: quality evidence never exports code, diffs or feedback."""

import json
from uuid import uuid4

import pytest

from app.core.logging import RedactingFilter
from scripts.phase9d_quality import quality_snapshot, quality_table, recompute_quality

pytestmark = pytest.mark.req("FR-V-04", "NFR-01")
CANARY = "sk-ant-api03-CANARY-7f3c9e2a1b4d5e6f"


def package():
    return {
        "variant": "cost",
        "status": "pending_review",
        "iteration_count": 3,
        "review_reasons": ["validation_failed", "unresolved_security_findings"],
        "files": {"terraform/main.tf": "DO-NOT-EXPORT-CODE"},
        "original_files": {"x": CANARY},
        "review_feedback": "DO-NOT-EXPORT-FEEDBACK",
        "security_report": {
            "diff": "DO-NOT-EXPORT-DIFF",
            "final": {
                "remaining_blocking": [
                    {"rule_id": "AWS-0086", "message": "DO-NOT-EXPORT-FINDING"},
                    {"rule_id": "AWS-0086"},
                ]
            },
        },
        "validation_report": {
            "checks": [
                {
                    "status": "failed",
                    "check_id": "terraform.validate",
                    "message": "Unsupported argument " + CANARY,
                    "file_path": "terraform/main.tf",
                    "line_start": 2,
                    "line_end": 4,
                    "snippet": "DO-NOT-EXPORT-SNIPPET",
                },
                {"status": "passed", "check_id": "pass", "message": "not retained"},
            ],
            "remediation": {
                "deterministic_repairs": [{"file": "x", "name": CANARY}],
                "rounds": [{"outcome": "accepted", "diff": CANARY}],
            },
        },
    }


def test_strict_projection_redacts_allowed_text_and_counts_findings():
    snapshot = quality_snapshot(package(), RedactingFilter())
    serialized = json.dumps(snapshot)
    assert "DO-NOT-EXPORT" not in serialized and CANARY not in serialized
    assert "[REDACTED]" in snapshot["failed_checks"][0]["message"]
    assert set(snapshot) == {
        "status",
        "legacy_label_mapped",
        "profile_assessments",
        "review_reasons",
        "failed_checks",
        "remaining_findings",
        "counts",
        "phase9e",
        "phase9f",
        "fixer_attempts",
        "validation_result",
    }
    assert set(snapshot["failed_checks"][0]) == {
        "check_id",
        "message",
        "file_path",
        "line_start",
        "line_end",
        "origin",
    }
    assert snapshot["remaining_findings"] == {"AWS-0086": 2}
    assert snapshot["counts"]["deterministic_repairs"] == 1
    assert snapshot["counts"]["validation_repair_rounds"] == 1
    metrics, table = quality_table(
        [snapshot, quality_snapshot({"status": "checks_passed"}, RedactingFilter())],
        missing=1,
    )
    assert metrics["checks_passed_rate"] == 0.5
    assert metrics["remaining_finding_counts"] == {"AWS-0086": 2}
    assert metrics["counts"]["missing_variants"] == 1
    assert "50.00%" in table


def test_offline_recompute_preserves_inputs_and_accepts_compact_snapshots(tmp_path):
    source = tmp_path / "baseline"
    source.mkdir()
    snapshots = tmp_path / "saved"
    snapshots.mkdir()
    run_id = str(uuid4())
    (source / "results.json").write_text(
        json.dumps({"runs": [{"run_id": run_id, "measurement": "pr01"}]})
    )
    (snapshots / f"{run_id}.json").write_text(
        json.dumps(
            {"packages": [package()], "missing_variants": ["performance", "security"]}
        )
    )
    original = {
        p: p.read_bytes() for folder in (source, snapshots) for p in folder.iterdir()
    }
    output = tmp_path / "quality-output"
    recompute_quality(source, snapshots, output)
    assert all(p.read_bytes() == content for p, content in original.items())
    for path in output.rglob("*"):
        if path.is_file():
            assert (
                "DO-NOT-EXPORT" not in path.read_text()
                and CANARY not in path.read_text()
            )
    report = json.loads((output / "quality.json").read_text())
    assert report["counts"] == {
        "packages": 1,
        "missing_variants": 2,
        "unavailable_runs": 0,
        "checks_passed": 0,
    }
    again = tmp_path / "again"
    recompute_quality(source, output / "quality", again)
    assert json.loads((again / "quality.json").read_text()) == report
    with pytest.raises(ValueError):
        recompute_quality(source, snapshots, source / "new")


def test_missing_historical_snapshots_are_unknown(tmp_path):
    source = tmp_path / "baseline"
    source.mkdir()
    (source / "results.json").write_text(
        json.dumps({"runs": [{"run_id": str(uuid4()), "measurement": "pr01"}]})
    )
    output = tmp_path / "quality"
    recompute_quality(source, source / "absent", output)
    report = json.loads((output / "quality.json").read_text())
    assert report["checks_passed_rate"] is None
    assert report["counts"]["unavailable_runs"] == 1


def test_phase9e_totals_and_contexts_are_allowlisted():
    raw = package()
    raw["validation_report"]["remediation"].update(
        initialization={
            "init_runs": 2,
            "init_reused": 4,
            "reinitializations": 1,
            "secret": CANARY,
        },
        generator_schema_context_chars=5800,
        gate={
            "outcome": "deadline",
            "failed_checks": [
                {
                    "check_id": "terraform.validate",
                    "message": "Missing required argument",
                    "source": CANARY,
                }
            ],
        },
    )
    compact = quality_snapshot(raw, RedactingFilter())
    report, table = quality_table([compact])
    assert report["gate_outcomes"] == {"deadline": 1}
    assert report["package_initialization"]["init_reused"] == 4
    assert report["schema_context_chars"]["generator"]["max"] == 5800
    assert CANARY not in json.dumps(report) + json.dumps(compact) + table


@pytest.mark.req("FR-S-08", "FR-S-10")
def test_historical_manual_approval_remains_manual_even_when_checks_are_clean():
    raw = {
        "status": "production_ready",
        "review_decision": {"action": "approve"},
        "security_report": {"final": {"outcome": "clean", "remaining_blocking": []}},
        "validation_report": {"summary": {"result": "valid"}},
    }
    value = quality_snapshot(raw, RedactingFilter())
    assert value["status"] == "engineer_approved"
    assert value["legacy_label_mapped"] is True
    assert value["profile_assessments"]["strict"]["checks_passed"] is True
