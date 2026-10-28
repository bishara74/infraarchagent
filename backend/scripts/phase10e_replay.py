"""FR-S-02/03/07: offline detect-only replay of both final benchmark rounds."""

import argparse
import asyncio
import json
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

from app.core.public_catalogue import digest
from app.domain.plan import DeploymentPlan
from app.domain.review import security_iterations
from app.security.plan_conformance import assess_plan_conformance, plan_regressions
from scripts.phase10c_replay import ROOT, Observer, write
from scripts.phase10d_diagnosis import inventory
from scripts.phase10d_replay import Replay as PairedReplay

BASELINE = "69ff06758eee01afe77b87a46221c8ed4b48ac4d"
COHORTS = (
    ("final2", "20261027T155607468680Z", 59),
    ("final3", "20261027T205119472235Z", 57),
)


def baseline_guard():
    path = "backend/app/security/acceptance.py"
    code = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
    module = types.ModuleType("phase10e_baseline_acceptance")
    sys.modules[module.__name__] = module
    exec(compile(code, path, "exec"), module.__dict__)
    return module.CandidateGuard


def recorded_rejections(package: dict) -> dict:
    """Keep attempts, partial groups and weighted error classes separate."""
    counts: Counter = Counter()
    for iteration in security_iterations(package.get("security_report")):
        verification = iteration.get("verification") or {}
        reasons = verification.get("reasons") or []
        if "plan_conformance_regression" in reasons:
            counts["security_iterations_with_conformance_reason"] += 1
            counts["security_error_class_counts"] += len(
                verification.get("error_classes") or [None]
            )
            if set(reasons) == {"plan_conformance_regression"}:
                counts["security_iterations_conformance_only"] += 1
        for key in ("catalogue", "templates", "partial_groups"):
            for record in verification.get(key, []):
                if record.get("reason") == "plan_conformance_regression":
                    counts[key + "_rejections"] += 1
    remediation = (package.get("validation_report") or {}).get("remediation") or {}
    for key in ("rounds", "deterministic_repairs"):
        for record in remediation.get(key, []):
            if record.get("reason") == "plan_conformance_regression":
                counts[key + "_rejections"] += 1
    return dict(counts)


class Replay(PairedReplay):
    def __init__(self, observer):
        self.observer = observer
        self.old_guard = baseline_guard()
        self.old_plan = plan_regressions
        self.rows, self.groups, self.missing, self.retained = [], [], [], []
        self.context, self.cache = {}, {}
        self.final_keys = set()

    async def retained_observation(self, files):
        # Final detection needs exact source maps, not a redundant scanner run.
        # Paired available candidates still use native checks and scanners.
        return None


async def run(output: Path, cache: Path) -> dict:
    if output.exists() or not output.is_relative_to(ROOT / "docs/evals"):
        raise ValueError("Output must be a fresh evidence directory")
    if not cache.is_relative_to(ROOT / ".cache"):
        raise ValueError("Cache must remain under repository .cache")
    cohorts = []
    # Validate every input before producing evidence or invoking native tools.
    for name, timestamp, expected_count in COHORTS:
        cohort = ROOT / "docs/evals" / ("phase9-bench-broad-" + timestamp)
        items, manifest = inventory(
            cohort, ROOT / (".cache/broad-" + name + "-results")
        )
        if len(items) != expected_count:
            raise ValueError("Unexpected cohort package count")
        cohorts.append((name, items, manifest))
    output.mkdir(parents=True)
    observer = Observer(cache)
    manifest = {"baseline": BASELINE, "runtime": observer.identity, "cohorts": {}}
    summaries = {}
    for name, items, inputs in cohorts:
        replay = Replay(observer)
        rows = []
        recorded: Counter = Counter()
        directory = output / name
        directory.mkdir()
        manifest["cohorts"][name] = {
            "inputs": inputs,
            "canonical_hash_checks": 3 * len(items),
        }
        for item in items:
            package = item["package"]
            package_rejections = recorded_rejections(package)
            recorded.update(package_rejections)
            assessment = assess_plan_conformance(
                DeploymentPlan.model_validate(item["plan"]),
                package.get("original_files"),
                package["files"],
            )
            print(
                f"Replay {name} {len(rows) + 1}/{len(items)} {item['variant']}",
                flush=True,
            )
            try:
                row = await replay.package(item)
            except (ValueError, KeyError) as error:
                row = {k: item[k] for k in ("run_id", "scenario", "round", "variant")}
                row["reconstruction"] = "unavailable_" + type(error).__name__
                replay.missing.append(
                    {**row, "kind": "exact_reconstruction_unavailable"}
                )
            row["recorded_rejections"] = package_rejections
            row["retained_sha256"] = digest(package["files"])
            row["final_assessment"] = assessment.model_dump(mode="json")
            rows.append(row)
            for filename, value in (
                ("packages", rows),
                ("candidates", replay.rows),
                ("groups", replay.groups),
                ("missing", replay.missing),
            ):
                write(directory / (filename + ".json"), value)
        guarded = [
            r for r in replay.rows if r.get("before") == "plan_conformance_regression"
        ]
        summaries[name] = {
            "packages": len(rows),
            "canonical_hash_checks": 3 * len(rows),
            "recorded_rejections_removed_as_conformance_gates": dict(recorded),
            "packages_with_security_conformance_reason": sum(
                bool(
                    r["recorded_rejections"].get(
                        "security_iterations_with_conformance_reason"
                    )
                )
                for r in rows
            ),
            "available_candidate_occurrences": len(replay.rows),
            "available_candidate_decisions": {
                side: dict(Counter(r.get(side, "unavailable") for r in replay.rows))
                for side in ("before", "after")
            },
            "distinct_candidate_pairs": len(
                {(r["before_sha256"], r["candidate_sha256"]) for r in replay.rows}
            ),
            "paired_guard_rejections_removed": len(guarded),
            "paired_after_decisions": dict(
                Counter(r.get("after", "unavailable") for r in guarded)
            ),
            "final_retained_packages_flagged": sum(
                bool(r["final_assessment"]["conflicts"]) for r in rows
            ),
            "final_retained_packages_with_information": sum(
                bool(r["final_assessment"]["notes"]) for r in rows
            ),
            "reconstruction": dict(Counter(r["reconstruction"] for r in rows)),
            "missing": dict(Counter(r["kind"] for r in replay.missing)),
        }
        write(directory / "summary.json", summaries[name])
    summary = {
        "cohorts": summaries,
        "combined": {
            key: sum(s[key] for s in summaries.values())
            for key in (
                "packages",
                "canonical_hash_checks",
                "paired_guard_rejections_removed",
                "available_candidate_occurrences",
                "packages_with_security_conformance_reason",
                "final_retained_packages_flagged",
                "final_retained_packages_with_information",
            )
        },
        "limitation": (
            "Recorded rejection counts disappear as conformance gates, not necessarily "
            "as whole-candidate rollbacks: other gates still apply. Native paired "
            "observations cover reconstructable proposals only; rejected model bodies "
            "and accepted post-security patches can be absent. Final flags describe "
            "frozen retained files, not a counterfactual new remediation trajectory. "
            "No pass-rate, causal recovery or historical deadline claim."
        ),
    }
    summary["combined"]["available_candidate_decisions"] = {}
    for side in ("before", "after"):
        decisions: Counter = Counter()
        for cohort_summary in summaries.values():
            decisions.update(cohort_summary["available_candidate_decisions"][side])
        summary["combined"]["available_candidate_decisions"][side] = dict(decisions)

    for key in (
        "recorded_rejections_removed_as_conformance_gates",
        "paired_after_decisions",
    ):
        combined: Counter = Counter()
        for cohort_summary in summaries.values():
            combined.update(cohort_summary[key])
        summary["combined"][key] = dict(combined)
    write(output / "manifest.json", manifest)
    write(output / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--cache", type=Path, default=ROOT / ".cache/phase10e-observations"
    )
    args = parser.parse_args()
    asyncio.run(run(args.output_dir.resolve(), args.cache.resolve()))


if __name__ == "__main__":
    main()
