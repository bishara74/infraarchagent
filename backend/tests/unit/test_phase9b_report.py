"""PR-01/03/05 and NFR-01: offline evaluation statistics and provenance."""

import json
import subprocess

import pytest

from app.core.logging import RedactingFilter
from scripts.phase9b_report import Evidence, breakdown, run_rate
from scripts.phase9b_stats import fisher, wilson
from scripts.phase9b_supplement import project
from scripts.phase9d_quality import compact_snapshot

pytestmark = pytest.mark.req("PR-01", "PR-03", "PR-05", "NFR-01")


@pytest.mark.parametrize(
    "a,n,b,m,expected",
    [
        (15, 81, 1, 36, 0.021210302919095),
        (15, 81, 1, 29, 0.064478343178997),
        (7, 40, 8, 41, 1.0),
        (8, 28, 1, 14, 0.230173615433753),
        (1, 10, 11, 14, 0.002759456185220083),
        (0, 0, 0, 0, 1.0),
    ],
)
def test_fisher_known_tables_and_symmetry(a, n, b, m, expected):
    assert fisher(a, n, b, m) == pytest.approx(expected)
    assert fisher(b, m, a, n) == pytest.approx(expected)
    assert fisher(n - a, n, m - b, m) == pytest.approx(expected)


def test_wilson_known_value_boundaries_and_invalid_counts():
    assert wilson(15, 81) == pytest.approx((0.11556290005906689, 0.28331589447245376))
    assert wilson(0, 0) == (None, None)
    assert wilson(0, 10)[0] == 0
    assert wilson(10, 10)[1] == 1
    with pytest.raises(ValueError):
        wilson(2, 1)
    with pytest.raises(ValueError):
        fisher(2, 1, 0, 1)


def test_subgroups_use_exact_prompt_and_run_level_includes_complete_failures():
    rows = [
        {
            "run_id": "a",
            "measurement": "pr01",
            "complete": True,
            "prompt": "same text",
            "prompt_index": 0,
        },
        {"run_id": "b", "measurement": "pr03", "complete": True, "prompt": "same text"},
        {
            "run_id": "c",
            "measurement": "pr01",
            "complete": True,
            "prompt": "other",
            "run_status": "failed",
        },
        {"run_id": "d", "measurement": "pr01", "complete": False, "prompt": "other"},
        {"run_id": "download", "measurement": "pr04", "complete": True},
    ]
    packages = [
        {"run_id": "a", "variant": "cost", "status": "checks_passed"},
        {"run_id": "a", "variant": "security", "status": "checks_passed"},
        {"run_id": "b", "variant": "cost", "status": "pending_review"},
    ]
    assert run_rate(rows, packages) == (1, 3)
    rates = breakdown("set", rows, packages)
    prompt = next(r for r in rates if r["group"] == "same text")
    assert (prompt["passed"], prompt["total"], prompt["missing_variants"]) == (2, 3, 3)
    for dimension in ("variant", "prompt"):
        selected = [r for r in rates if r["dimension"] == dimension]
        assert sum(r["passed"] for r in selected) == 2
        assert sum(r["total"] for r in selected) == 3
    assert next(r for r in rates if r["group"] == "performance")["rate"] is None


def test_git_evidence_ignores_dirty_and_untracked_inputs(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args])

    git("init", "-q")
    path = tmp_path / "docs/evals/example/results.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"committed":true}')
    git("add", "docs")
    git(
        "-c",
        "user.name=Evaluation Test",
        "-c",
        "user.email=evaluation@example.invalid",
        "commit",
        "-qm",
        "fixture",
    )
    path.write_text("dirty")
    evidence = Evidence(tmp_path)
    assert evidence.json("docs/evals/example/results.json") == {"committed": True}
    assert len(evidence.used["docs/evals/example/results.json"]) == 64
    with pytest.raises(ValueError):
        evidence.read("docs/evals/example/untracked.json")
    with pytest.raises(ValueError):
        evidence.read(".env")


def test_supplement_only_exports_counts_identifiers_and_hashes(tmp_path):
    from uuid import uuid4

    path = tmp_path / (str(uuid4()) + ".json")
    raw = {
        "packages": [
            {
                "variant": "cost",
                "files": {"main.tf": "DO-NOT-EXPORT"},
                "security_report": {
                    "iterations": [
                        {
                            "fixes": [
                                {"accepted": True, "diff": "DO-NOT-EXPORT"},
                                {"accepted": False},
                                {"accepted": False, "call_attempted": False},
                            ]
                        }
                    ]
                },
            }
        ]
    }
    path.write_text(json.dumps(raw))
    before = path.read_bytes()
    rows = project(tmp_path, "A3")
    assert set(rows[0]) == {
        "benchmark",
        "source_file",
        "source_directory",
        "source_sha256",
        "run_id",
        "variant",
        "proposals",
        "accepted",
    }
    assert rows[0]["accepted"] == 1 and rows[0]["proposals"] == 2
    assert "DO-NOT-EXPORT" not in json.dumps(rows)
    assert path.read_bytes() == before


def test_compact_loader_preserves_profiles_and_catalogue_without_extra_source():
    raw = {
        "status": "checks_passed",
        "validation_result": "valid",
        "remaining_findings": {},
        "profile_assessments": {
            "strict": {"checks_passed": True, "remaining_blocking": 0, "excepted": []},
            "contextual-v1": {
                "checks_passed": True,
                "remaining_blocking": 0,
                "excepted": [],
            },
        },
        "phase9f": {
            "measured": True,
            "catalogue": [
                {
                    "control": "kms",
                    "resource": "aws_s3_bucket.x",
                    "status": "retained",
                    "rules": ["CKV_AWS_145"],
                    "files": "DO-NOT-EXPORT",
                }
            ],
            "templates": [],
            "partial_groups": {"kept": 1},
            "generation_syntax": {"path": "unchanged"},
            "fixer_calls": [],
            "fixer_configurations": [],
            "iteration_timings": [],
            "deadline_phases": [],
            "existing_file_proposals": {"normalized": 0, "retained": 0},
        },
    }
    clean = compact_snapshot(raw, RedactingFilter())
    assert clean["profile_assessments"] == raw["profile_assessments"]
    assert clean["phase9f"]["catalogue"][0]["rules"] == ["CKV_AWS_145"]
    assert "DO-NOT-EXPORT" not in json.dumps(clean)
    assert compact_snapshot(clean, RedactingFilter()) == clean


def test_traceability_distinguishes_links_and_manual_gaps():
    from scripts.phase9b_traceability import render
    from scripts.traceability import build_report

    report = build_report(
        {"UC-01", "NFR-02", "NFR-04"},
        [
            {
                "framework": "pytest",
                "node_id": "tests/test_swap.py::test_swap",
                "file": "backend/tests/test_swap.py",
                "ids": ["NFR-02"],
            }
        ],
        {"groups": {}},
    )
    output = render(report, {})
    assert "../../../backend/tests/test_swap.py" in output
    assert "| UC-01 | UNLINKED" in output
    assert "NFR-04 remains unlinked/unverified" in output
    assert "concrete-class" in output


def test_committed_baseline_legacy_label_reproduces_historical_rate():
    from scripts.phase9_common import ROOT
    from scripts.phase9b_report import load_benchmark

    evidence = Evidence(ROOT)
    benchmark = load_benchmark(evidence, "phase9-bench-real-20261015T124330508703Z")
    assert benchmark["quality"]["counts"]["checks_passed"] == 1
    assert benchmark["quality"]["counts"]["packages"] == 36
    assert run_rate(benchmark["rows"], benchmark["packages"]) == (1, 14)


@pytest.mark.parametrize(
    "change",
    ["model", "generator_settings", "git_commit", "dirty", "selection", "prompt"],
)
def test_pooling_rejects_unmatched_final_sets(change):
    from copy import deepcopy

    from scripts.phase9b_report import assert_comparable

    left = {
        "environment": {
            "git_commit": "a",
            "git_tracked_dirty": False,
            "generator_settings": {"attempt": 1},
            "model": "stub",
            "fixing_model": "stub",
            "tools": {"terraform": "1"},
            "resolved_agent_selections": {"run": {"architect": {"model": "stub"}}},
        },
        "rows": [{"measurement": "pr01", "prompt": "one"}],
    }
    right = deepcopy(left)
    assert_comparable(left, right)
    if change == "dirty":
        right["environment"]["git_tracked_dirty"] = True
    elif change == "selection":
        right["environment"]["resolved_agent_selections"]["run"]["architect"][
            "model"
        ] = "other"
    elif change == "prompt":
        right["rows"][0]["prompt"] = "other"
    else:
        right["environment"][change] = "other"
    with pytest.raises(ValueError):
        assert_comparable(left, right)


def test_report_reconciles_real_committed_inputs_and_is_deterministic(tmp_path):
    from scripts.phase9_common import ROOT
    from scripts.phase9_report import read_csv
    from scripts.phase9b_report import generate

    evidence = Evidence(ROOT)
    first = tmp_path / "first"
    second = tmp_path / "second"
    generate(evidence, first)
    generate(Evidence(ROOT), second)
    assert {f.name: f.read_bytes() for f in first.iterdir()} == {
        f.name: f.read_bytes() for f in second.iterdir()
    }
    rows = read_csv(first / "rates.csv")
    final = next(
        r
        for r in rows
        if r["benchmark"] == "final combined"
        and r["dimension"] == "all"
        and r["profile"] == "strict"
    )
    assert (final["passed"], final["total"]) == ("15", "81")
    baseline = next(
        r for r in rows if r["benchmark"] == "baseline" and r["dimension"] == "run"
    )
    assert (baseline["passed"], baseline["total"]) == ("1", "14")
    assert "0.23017361543375287" in (first / "report.md").read_text()
    assert len([r for r in rows if r["dimension"] == "prompt"]) == 9
    assert len([r for r in rows if r["dimension"] == "variant"]) == 9
    manifest = json.loads((first / "input-manifest.json").read_text())
    assert all(
        row["path"].startswith("docs/evals/") and len(row["sha256"]) == 64
        for row in manifest["files"]
    )
    with pytest.raises(ValueError):
        generate(evidence, first)
    with pytest.raises(ValueError):
        generate(evidence, ROOT / "docs/evals/phase9b-supplement/forbidden-output")
    with pytest.raises(ValueError):
        generate(evidence, ROOT / ".cache/forbidden-output")
