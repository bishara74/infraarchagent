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
