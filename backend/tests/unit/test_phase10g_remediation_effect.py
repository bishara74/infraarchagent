"""FR-S-02/03/07: retained metrics, unknowns and visibility stay evidence-bound."""

import csv
import io
import json
from copy import deepcopy

import pytest

from scripts import phase10g_remediation_effect as effect

pytestmark = pytest.mark.req("FR-S-02", "FR-S-03", "FR-S-07", "NFR-01")


def finding(rule="CKV_AWS_19", tool="checkov", severity="HIGH"):
    return {"tool": tool, "severity": severity, "rule_id": rule}


def scan(blocking=None, advisory=None):
    blocking = [finding()] if blocking is None else blocking
    advisory = [] if advisory is None else advisory
    counts = {}
    for row in [*blocking, *advisory]:
        counts[row["severity"]] = counts.get(row["severity"], 0) + 1
    return {
        "blocking": blocking,
        "advisory_count": len(advisory),
        "advisory_sample": advisory[:20],
        "advisory_omitted_count": max(0, len(advisory) - 20),
        "counts_by_severity": counts,
        "tool_status": {"checkov": "ok", "trivy": "ok", "terraform": "ok"},
    }


def package():
    return {
        "variant": "cost",
        "status": "pending_review",
        "files": {"terraform/main.tf": "synthetic retained"},
        "original_files": {"terraform/main.tf": "synthetic original"},
        "review_reasons": ["unresolved_security_findings"],
        "review_available": True,
        "validation_report": {"summary": {"result": "valid"}},
        "security_report": {
            "sessions": [
                {
                    "kind": "automated",
                    "iterations": [
                        {
                            "index": 0,
                            "scan": scan(),
                            "verification": {
                                "outcome": "rolled_back",
                                "after_failed": 999,
                                "retained_failed": 500,
                                "reasons": ["new_blocking_findings"],
                            },
                        }
                    ],
                    "final": {
                        "reason": "iteration limit",
                        "first_scan_checkov_high_or_critical": 1,
                        "first_scan_trivy_high_or_critical": 0,
                    },
                }
            ],
            "final": {"remaining_blocking": [finding()]},
            "final_verification": scan(),
        },
    }


def quality():
    return {
        "status": "pending_review",
        "validation_result": "valid",
        "remaining_findings": {"CKV_AWS_19": 1},
        "review_reasons": ["unresolved_security_findings"],
        "counts": {"remaining_findings": 1},
    }


def row(p=None, q=None):
    return effect.package_row(
        "10e_final",
        {"run_id": "synthetic-run", "complexity": 1},
        "cost",
        quality() if q is None else q,
        package() if p is None else p,
    )


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        (3, 1, "reduced"),
        (2, 2, "unchanged_nonzero"),
        (0, 0, "already_zero"),
        (0, 1, "increased"),
        (2, 3, "increased"),
        (None, 0, "unknown"),
        (1, None, "unknown"),
        (True, 0, "unknown"),
        (-1, 0, "unknown"),
    ],
)
def test_classification(before, after, expected):
    assert effect.classify(before, after) == expected


def test_sessions_override_aliases_and_candidates_never_supply_final_counts():
    p = package()
    p["security_report"]["iterations"] = [{"scan": scan([])}]
    p["security_report"]["sessions"].append(
        {"kind": "review_retry", "iterations": [{"scan": scan([])}]}
    )
    r = row(p)
    assert r["blocking_first"] == r["blocking_final"] == 1
    assert r["blocking_class"] == "unchanged_nonzero"
    assert r["reason_evidence"][0]["outcome"] == "rolled_back"
    assert "new_blocking_findings" in r["reasons"]


def test_omitted_original_session_and_missing_final_verification_stay_unknown():
    p = package()
    p["security_report"]["omitted_session_count"] = 1
    assert row(p)["blocking_class"] == "unknown"
    p = package()
    del p["security_report"]["final_verification"]
    r = row(p)
    assert r["all_class"] == r["high_critical_class"] == "unknown"
    assert r["blocking_class"] == "unknown"
    # Committed final blocker counts alone cannot establish a before/after pair.
    assert r["blocking_final"] == 1


def test_cross_tool_duplicates_count_and_terraform_is_excluded_from_high():
    s = scan(
        [
            finding(),
            finding("AWS-0010", "trivy"),
            finding("TERRAFORM_FILE_INPUT_BLOCKED", "terraform", "CRITICAL"),
        ]
    )
    assert effect.scan_counts(s) == {"blocking": 3, "high_critical": 2, "all": 3}
    p = package()
    initial = p["security_report"]["sessions"][0]["final"]
    initial["first_scan_combined_high_or_critical"] = 99
    assert row(p)["high_critical_first"] == 1


def test_truncated_advisory_samples_keep_totals_without_inventing_attribution():
    advisory = [finding("CKV_OTHER", severity="UNKNOWN") for _ in range(30)]
    s = scan([], advisory)
    assert effect.scan_counts(s) == {"blocking": 0, "high_critical": 0, "all": 30}
    s["counts_by_severity"] = {"UNKNOWN": 29, "HIGH": 1}
    assert effect.scan_counts(s)["high_critical"] is None
    s["counts_by_severity"] = {"UNKNOWN": 100}
    assert set(effect.scan_counts(s).values()) == {None}


def test_observed_new_rules_require_complete_samples_and_preserve_multiplicity():
    first = scan([], [finding("CKV_OTHER", severity="UNKNOWN")])
    final = scan([], [finding("CKV_OTHER", severity="UNKNOWN")] * 2)
    assert effect.observed_delta(first, final) == ["CKV_OTHER"]
    first["advisory_count"] = 21
    assert effect.observed_delta(first, final) is None


def test_introduced_candidate_rules_are_separate_from_retained_delta():
    p = package()
    verification = p["security_report"]["sessions"][0]["iterations"][0]["verification"]
    verification["templates"] = [
        {
            "template": "access_logs",
            "status": "rejected",
            "reason": "new_blocking_findings",
            "introduced_findings": [{"rule_id": "CKV_CANDIDATE"}],
        }
    ]
    r = row(p)
    assert r["new_observed_rule_ids"] == []
    record = next(e for e in r["reason_evidence"] if e["stage"] == "templates")
    assert record["introduced_rule_ids"] == ["CKV_CANDIDATE"]
    assert record["outcome"] == "rejected"


def test_failed_scanner_is_unknown_and_syntax_limited_remains_observed():
    s = scan()
    s["tool_status"]["checkov"] = "error"
    assert set(effect.scan_counts(s).values()) == {None}
    s["tool_status"]["checkov"] = "ok"
    s["tool_status"]["terraform"] = "syntax_limited"
    assert effect.scan_counts(s)["blocking"] == 1


def test_failed_endpoint_cannot_turn_partial_zero_into_a_reduction():
    p = package()
    p["security_report"]["final_verification"]["tool_status"]["checkov"] = "error"
    q = quality()
    q.update(remaining_findings={}, counts={"remaining_findings": 0})
    assert row(p, q)["blocking_class"] == "unknown"
    p = package()
    p["security_report"]["sessions"][0]["iterations"][0]["scan"]["tool_status"][
        "checkov"
    ] = "error"
    assert row(p)["high_critical_class"] == "unknown"


def test_projection_verifies_content_and_final_quality_fields():
    p = package()
    snapshot = {"plan": {"services": []}}
    hashes = {
        "plan_sha256": effect.digest(snapshot["plan"]),
        "original_files_sha256": effect.digest(p["original_files"]),
        "retained_files_sha256": effect.digest(p["files"]),
    }
    assert effect.verify_package(snapshot, p, quality(), hashes) == []
    hashes["retained_files_sha256"] = "incorrect"
    assert effect.verify_package(snapshot, p, quality(), hashes) == [
        "retained_files_sha256_mismatch"
    ]
    p["status"] = "checks_passed"
    assert "quality_status_mismatch" in effect.verify_package(
        snapshot, p, quality(), hashes
    )


@pytest.mark.parametrize(
    ("status", "count", "present", "expected"),
    [
        ("pending_review", 1, True, "pending_review_findings_visible"),
        ("checks_passed", 1, True, "exception_status"),
        ("pending_review", 1, False, "pending_review_visibility_unverified"),
        ("checks_passed", 0, True, "no_recorded_blockers"),
        ("pending_review", None, True, "unknown"),
    ],
)
def test_visibility(status, count, present, expected):
    assert effect.visibility(status, count, package() if present else None) == expected


def test_missing_review_affordance_and_advisory_only_success_are_disclosed():
    p = package()
    p["review_available"] = False
    assert row(p)["visibility"] == "exception_visibility"
    p = package()
    p["status"] = "checks_passed"
    p["security_report"]["final_verification"] = scan([], [finding(severity="LOW")])
    q = quality()
    q.update(
        status="checks_passed", remaining_findings={}, counts={"remaining_findings": 0}
    )
    r = row(p, q)
    r["provenance"] = "content_projection"
    assert r["advisory_only"] is True
    report = effect.render([r], [], "synthetic")
    assert "Advisory-only packages outside pending_review" in report
    assert "synthetic-run / cost: checks_passed" in report


def test_unknowns_are_excluded_only_from_comparable_denominator():
    rows = [{"blocking_class": c} for c in effect.CLASSES]
    s = effect.summary(rows, "blocking")
    assert s["packages"] == 5 and s["comparable"] == 4
    assert s["not_increased"] == 3
    assert s["reduced_fraction_of_comparable"] == 0.25
    assert s["not_increased_fraction_of_comparable"] == 0.75
    assert (
        effect.summary([], "blocking")["not_increased_fraction_of_comparable"] is None
    )


def test_mismatching_pinned_export_becomes_unknown_without_losing_committed_final(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(effect, "COHORTS", (("synthetic", "sample", "exports"),))
    monkeypatch.setattr(
        effect, "pinned_exports", lambda _: {".cache/exports/run.json": "incorrect"}
    )
    folder = "docs/evals/phase9-bench-sample"
    qpath = folder + "/quality/run/cost.json"
    values = {folder + "/results.json": {"runs": [{"run_id": "run"}]}, qpath: quality()}

    class Evidence:
        paths = set(values)

        def json(self, path):
            return deepcopy(values[path])

    (tmp_path / "exports").mkdir()
    (tmp_path / "exports/run.json").write_text(
        json.dumps({"run": {"id": "run"}, "packages": [package()]})
    )
    rows, exports = effect.inventory(Evidence(), tmp_path)
    assert exports[0]["verification"] == "unverified"
    assert rows[0]["blocking_class"] == "unknown"
    assert rows[0]["blocking_final"] == 1
    assert rows[0]["visibility"] == "pending_review_visibility_unverified"


def test_csv_reason_metadata_roundtrips_without_source_bodies():
    r = row()
    safe = json.dumps(r)
    assert "synthetic retained" not in safe and "synthetic original" not in safe
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(r), lineterminator="\n")
    writer.writeheader()
    writer.writerow(
        {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in r.items()}
    )
    stream.seek(0)
    reread = next(csv.DictReader(stream))
    assert json.loads(reread["reason_evidence"]) == r["reason_evidence"]
