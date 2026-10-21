"""PR-01/05, NFR-01: descriptive broad rates and immutable historical rows."""

import json
import subprocess
from copy import deepcopy

import pytest

from scripts.phase9_common import ROOT
from scripts.phase9b_report import Evidence, generate
from scripts.phase9b_stats import fisher
from scripts.phase9i_broad import (
    METADATA_FIELDS,
    SCENARIO_PATH,
    broad_schedule,
    scenario_digest,
)
from scripts.phase9i_broad_report import anchor_comparisons, grouped, load_broad

pytestmark = pytest.mark.req("PR-01", "PR-05", "NFR-01")
FOLDER = "phase9-bench-broad-fixture"


def test_broad_report_includes_measured_schema_overflow(
    committed_broad, tmp_path, monkeypatch
):
    from scripts import phase9i_broad_report

    evidence, _ = committed_broad
    benchmark = load_broad(evidence, FOLDER)
    for package in benchmark["packages"]:
        package.setdefault("phase9e", {}).update(
            {
                "generator_schema_only_context_chars": 4400,
                "generator_schema_context_overflow": True,
                "generator_schema_omitted_resource_types": {
                    "required": [],
                    "conditional_required": ["aws_ecs_service"],
                },
            }
        )
    monkeypatch.setattr(phase9i_broad_report, "load_broad", lambda *args: benchmark)
    output = tmp_path / "overflow-report"
    output.mkdir()
    (output / "report.md").write_text("")
    phase9i_broad_report.append_broad_report(
        evidence,
        [FOLDER],
        {
            "final set 1": benchmark,
            "final set 2": benchmark,
        },
        output,
    )
    text = (output / "report.md").read_text()
    assert "Schema-only context sizes" in text
    assert "conditional_required" in text and "aws_ecs_service" in text


def fixture_benchmark(mode="real"):
    raw = (ROOT / SCENARIO_PATH).read_bytes()
    registration = json.loads(raw)
    rows = broad_schedule(registration, 2, scenario_digest(raw))
    for i, row in enumerate(rows):
        row.update(
            mode=mode,
            complete=True,
            run_id=f"run-{i}",
            run_status="success",
            seconds=i + 1,
            cost_usd=(i + 1) / 100,
        )
    packages = []
    # Static anchor has one pass, one blocked package, and a complete failed run.
    first = rows[1]
    for variant, passed in [("cost", True), ("security", False)]:
        packages.append(
            {
                "run_id": first["run_id"],
                "variant": variant,
                "status": "checks_passed" if passed else "pending_review",
                "validation_result": "valid",
                "remaining_findings": {} if passed else {"CKV_TEST": 1},
                "profile_assessments": {
                    p: {
                        "checks_passed": passed,
                        "remaining_blocking": 0 if passed else 1,
                        "excepted": [],
                    }
                    for p in ("strict", "contextual-v1", "contextual-v2")
                },
            }
        )
    rows[18].update(run_status="failed", seconds=999, cost_usd=None)
    rows[19].update(
        complete=False,
        run_id=None,
        seconds=None,
        cost_usd=None,
        execution_status="not_started",
    )
    rows[0].update(complete=False, seconds=None, cost_usd=None)
    return {
        "folder": FOLDER,
        "environment": {"mode": mode},
        "rows": rows,
        "packages": packages,
        "registration": registration,
    }


def test_groups_denominators_intervals_missing_timing_and_unknowns():
    benchmark = fixture_benchmark()
    groups, blockers = grouped(benchmark)
    static = next(
        r
        for r in groups
        if r["dimension"] == "scenario" and r["group"] == 2 and r["profile"] == "strict"
    )
    assert (
        static["passed"],
        static["packages"],
        static["valid"],
        static["missing_variants"],
    ) == (1, 2, 2, 4)
    assert static["rate"] == 0.5 and static["wilson_low"] < 0.5 < static["wilson_high"]
    assert static["median_seconds"] == 2  # complete failed run excluded from timing
    assert static["timed_runs"] == static["priced_runs"] == static["failed_runs"] == 1
    storage = next(
        r for r in groups if r["dimension"] == "scenario" and r["group"] == 1
    )
    assert storage["missing_variants"] == 0
    assert storage["unknown_variant_slots"] == 3
    assert storage["not_started"] == storage["incomplete_runs"] == 1
    assert storage["rate"] is None
    assert any(b["rule_id"] == "CKV_TEST" and b["count"] == 1 for b in blockers)
    for profile in ("strict", "contextual-v1", "contextual-v2"):
        levels = [
            r
            for r in groups
            if r["dimension"] == "complexity" and r["profile"] == profile
        ]
        assert sum(r["packages"] for r in levels) == 2
        assert sum(r["planned_runs"] for r in levels) == 20


def test_absent_profile_is_unknown_and_contextual_exceptions_reduce_blockers():
    benchmark = fixture_benchmark()
    for p in benchmark["packages"]:
        del p["profile_assessments"]["contextual-v2"]
    benchmark["packages"][1]["profile_assessments"]["contextual-v1"] = {
        "checks_passed": True,
        "remaining_blocking": 0,
        "excepted": [{"rule_id": "CKV_TEST"}],
    }
    groups, blockers = grouped(benchmark)
    assert all(r["passed"] is None for r in groups if r["profile"] == "contextual-v2")
    assert not [b for b in blockers if b["profile"] != "strict"]
    v1 = next(
        r
        for r in groups
        if r["dimension"] == "scenario"
        and r["group"] == 2
        and r["profile"] == "contextual-v1"
    )
    assert v1["passed"] == 2


def test_anchor_exact_text_join_run_clustering_and_missing_historical_v2():
    broad = fixture_benchmark()
    final = deepcopy(broad)
    final["rows"][1].pop("scenario_id")  # historical join must use exact text
    for p in final["packages"]:
        del p["profile_assessments"]["contextual-v2"]
    results = anchor_comparisons(broad, {"final combined": final})
    run = next(
        r
        for r in results
        if r["scenario_id"] == 2 and r["profile"] == "strict" and r["unit"] == "run"
    )
    assert (
        run["broad_passed"],
        run["broad_total"],
        run["final_passed"],
        run["final_total"],
    ) == (1, 2, 1, 2)
    assert run["fisher_two_sided"] == fisher(1, 2, 1, 2)
    assert all(
        r["fisher_two_sided"] is None
        for r in results
        if r["profile"] == "contextual-v2"
    )
    assert anchor_comparisons(fixture_benchmark("stub"), {"final": final}) == []


@pytest.fixture
def committed_broad(tmp_path):
    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(tmp_path), *args], stderr=subprocess.PIPE
        )

    def commit():
        git("add", "docs")
        git(
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        )
        return git("rev-parse", "HEAD").decode().strip()

    git("init", "-q")
    raw = (ROOT / SCENARIO_PATH).read_bytes()
    path = tmp_path / SCENARIO_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(raw)
    registration_commit = commit()
    base = tmp_path / "docs/evals" / FOLDER
    base.mkdir()
    benchmark = fixture_benchmark()
    env = {
        "benchmark_kind": "broad",
        "mode": "real",
        "scenario_sha256": scenario_digest(raw),
        "registration_commit": registration_commit,
        "git_commit": registration_commit,
        "runs_per_scenario": 2,
        "planned_runs": 20,
    }
    (base / "environment.json").write_text(json.dumps(env))
    (base / "results.json").write_text(
        json.dumps({"runs": benchmark["rows"], "cohorts": []})
    )
    (base / "broad-v1.json").write_bytes(raw)
    (base / "summary.md").write_text("PR-05 individual thresholds: PASS.")
    for p in benchmark["packages"]:
        directory = base / "quality" / p["run_id"]
        directory.mkdir(parents=True, exist_ok=True)
        row = next(r for r in benchmark["rows"] if r["run_id"] == p["run_id"])
        (directory / (p["variant"] + ".json")).write_text(
            json.dumps({**p, **{k: row[k] for k in METADATA_FIELDS}})
        )
    commit()
    return Evidence(tmp_path), base


def test_loader_uses_committed_evidence_ignores_dirty_copy(committed_broad):
    evidence, base = committed_broad
    (base / "results.json").write_text("uncommitted invalid data")
    benchmark = load_broad(evidence, FOLDER)
    assert len(benchmark["rows"]) == 20
    assert len(benchmark["packages"]) == 2
    assert any(p.endswith("/broad-v1.json") for p in evidence.used)


@pytest.mark.parametrize("bad", ["hash", "row", "package", "schedule", "registration"])
def test_loader_rejects_inconsistent_evidence(committed_broad, bad):
    evidence, _ = committed_broad
    original = evidence.json

    def changed(path):
        value = original(path)
        if bad == "hash" and path.endswith("environment.json"):
            value["scenario_sha256"] = "wrong"
        if bad == "registration" and path.endswith("environment.json"):
            value["registration_commit"] = "invalid-revision"
        if bad == "row" and path.endswith("results.json"):
            value["runs"][0]["prompt"] = "different prompt"
        if bad == "schedule" and path.endswith("results.json"):
            value["runs"].pop()
        if bad == "package" and "/quality/" in path:
            value["scenario_id"] = 99
        return value

    evidence.json = changed
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        load_broad(evidence, FOLDER)


def test_historical_outputs_unchanged_when_broad_section_is_appended(
    committed_broad, tmp_path
):
    broad, _ = committed_broad
    historical = Evidence(ROOT)
    # Real broad runs may already be committed. This fixture compares the
    # historical final-set prefix against adding exactly one synthetic broad set.
    historical.paths = {
        path
        for path in historical.paths
        if not path.startswith("docs/evals/phase9-bench-broad-")
    }
    original_output = tmp_path / "original"
    generate(historical, original_output)
    combined = Evidence(ROOT)
    combined.paths = historical.paths | broad.paths
    original_read = combined.read

    def read(path):
        if path.startswith("docs/evals/" + FOLDER + "/"):
            raw = broad.read(path)
            combined.used[path] = broad.used[path]
            return raw
        return original_read(path)

    combined.read = read
    # Registration ancestry is in the fixture's own immutable Git repository.
    combined.git = lambda *args: (
        broad.git(*args)
        if args[0] in {"show", "merge-base"}
        and (args[0] == "merge-base" or SCENARIO_PATH in args[-1])
        else historical.git(*args)
    )
    new_output = tmp_path / "extended"
    generate(combined, new_output)
    for name in ("rates.csv", "costs.csv", "timings.csv", "blockers.csv"):
        assert (new_output / name).read_bytes() == (original_output / name).read_bytes()
    assert (
        (new_output / "report.md")
        .read_text()
        .startswith((original_output / "report.md").read_text())
    )
    assert "Broad scenario benchmark" in (new_output / "report.md").read_text()
    assert "Pass rate versus complexity level" in (new_output / "report.md").read_text()
    from scripts.phase9_report import read_csv

    assert len(read_csv(new_output / "broad-complexity.csv")) == 15
    assert (
        len(json.loads((new_output / "broad-summary.json").read_text())["groups"]) == 45
    )
