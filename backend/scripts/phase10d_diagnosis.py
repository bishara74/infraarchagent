"""FR-P-04/FR-S-07: source-free inventory of the accepted Phase 10d diagnosis."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.core.public_catalogue import digest
from scripts.phase10c_replay import ROOT, source, write

COHORT = ROOT / "docs/evals/phase9-bench-broad-20261027T155607468680Z"
ROUND2 = ROOT / "docs/evals/phase9-bench-broad-20261021T200436165739Z"


def inventory(cohort: Path, snapshots: Path) -> tuple[list[dict], list[dict]]:
    items, manifest = [], []
    for run in json.loads(source(cohort / "results.json"))["runs"]:
        path = snapshots / (run["run_id"] + ".json")
        raw = source(path)
        manifest.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        data = json.loads(raw)
        for package in data["packages"]:
            architecture = (
                cohort / "architecture" / run["run_id"] / (package["variant"] + ".json")
            )
            if cohort == COHORT or architecture.exists():
                expected = json.loads(source(architecture))
                for key, value in (
                    ("plan_sha256", data["plan"]),
                    ("original_files_sha256", package["original_files"]),
                    ("retained_files_sha256", package["files"]),
                ):
                    if digest(value) != expected[key]:
                        raise ValueError("Snapshot does not match committed hashes")
            items.append(
                {
                    "run_id": run["run_id"],
                    "scenario": run["scenario_id"],
                    "round": run["round"],
                    "variant": package["variant"],
                    "plan": data["plan"],
                    "package": package,
                }
            )
    return items, manifest


def analyze(items: list[dict], cohort: Path) -> tuple[list[dict], list[dict]]:
    anomalies, packages = [], []
    for item in items:
        p = item["package"]
        context = {k: item[k] for k in ("run_id", "scenario", "round", "variant")}
        compact = json.loads(
            source(cohort / "quality" / item["run_id"] / (item["variant"] + ".json"))
        )
        counts: Counter = Counter()
        iterations = [
            i
            for s in p["security_report"].get("sessions", [])
            for i in s.get("iterations", [])
            if i.get("verification")
        ]
        for iteration, exported in zip(
            iterations, compact["phase9e"]["security_iteration_repairs"], strict=True
        ):
            verification = iteration["verification"]
            reasons = verification.get("reasons", [])
            counts["security_" + verification["outcome"]] += 1
            for reason in reasons:
                counts["reason_" + reason] += 1
            kinds = []
            if verification["outcome"] == "rolled_back" and not exported["reasons"]:
                kinds.append("empty_export_reason")
            if "terraform_verification_unavailable" in reasons:
                kinds.append("terraform_verification_unavailable")
            for kind in kinds:
                anomalies.append(
                    {
                        **context,
                        "kind": kind,
                        "iteration": iteration["index"],
                        "raw_reasons": reasons,
                        "error_class_count": len(
                            verification.get("error_classes") or ["unknown"]
                        ),
                        "path": (
                            "CandidateGuard.evaluate -> SecurityAgent._fix_iteration"
                            " -> quality_snapshot"
                        ),
                    }
                )
            for group in verification.get("partial_groups", []):
                counts["group_" + group["status"]] += 1
                counts["group_reason_" + group["reason"]] += 1
            for fix in iteration.get("fixes", []):
                counts["fix_proposed"] += 1
                counts["fix_patch_accepted"] += bool(fix.get("accepted"))
                counts["fix_retained"] += bool(fix.get("retained"))
        remediation = p["validation_report"]["remediation"]
        for raw, exported in zip(
            remediation.get("rounds", []),
            compact["phase9e"]["repair_rounds"],
            strict=True,
        ):
            counts["repair_" + raw["outcome"]] += 1
            if raw["outcome"] == "rejected" and exported["reason"] == "unknown":
                anomalies.append(
                    {
                        **context,
                        "kind": "unknown_export_repair",
                        "phase": raw["phase"],
                        "iteration": raw["index"],
                        "raw_reasons": [raw["reason"]],
                        "error_class_count": len(
                            raw.get("error_classes") or ["unknown"]
                        ),
                        "path": (
                            "ValidationRepair.run -> plan_regressions"
                            " -> quality_snapshot"
                        ),
                    }
                )
        for record in remediation.get("deterministic_repairs", []):
            counts["deterministic_" + (record.get("outcome") or "applied")] += 1
        packages.append(
            {
                **context,
                "status": p["status"],
                "gate": remediation.get("gate", {}).get("outcome"),
                "validation": p["validation_report"]["summary"]["result"],
                "counts": dict(counts),
                "blockers": [
                    {k: v[k] for k in ("rule_id", "resource", "file_path")}
                    for v in p["security_report"]["final"].get("remaining_blocking", [])
                ],
                "failed_checks": [
                    {
                        k: c.get(k)
                        for k in (
                            "check_id",
                            "message",
                            "file_path",
                            "line_start",
                            "origin",
                        )
                    }
                    for c in p["validation_report"]["checks"]
                    if c["status"] == "failed"
                ],
            }
        )
    return anomalies, packages


def run(output: Path) -> dict:
    if output.exists() or not output.resolve().is_relative_to(ROOT / "docs/evals"):
        raise ValueError("Output must be a fresh evidence directory")
    items, inputs = inventory(COHORT, ROOT / ".cache/broad-final2-results")
    old, older_inputs = inventory(ROUND2, ROOT / ".cache/broad-2-results")
    anomalies, packages = analyze(items, COHORT)
    _, older = analyze(old, ROUND2)
    previous = {(p["scenario"], p["round"], p["variant"]): p for p in older}
    losses, gains = [], []
    for p in packages:
        if p["scenario"] > 5:
            continue
        prior = previous[p["scenario"], p["round"], p["variant"]]
        if prior["status"] == "checks_passed" and p["status"] != "checks_passed":
            losses.append(p)
        if prior["status"] != "checks_passed" and p["status"] == "checks_passed":
            gains.append(p)
    summary = {
        "packages": len(items),
        "canonical_hash_checks": 3 * len(items),
        "anomaly_attempts": dict(Counter(a["kind"] for a in anomalies)),
        "anomaly_error_class_counts": {
            k: sum(a["error_class_count"] for a in anomalies if a["kind"] == k)
            for k in sorted({a["kind"] for a in anomalies})
        },
        "low_complexity_losses": len(losses),
        "low_complexity_gains": len(gains),
        "limitation": (
            "Observed outcome buckets, not exclusive causal or recoverable-pass "
            "counts. Rejected Fixer bodies and one accepted post-security "
            "patch are missing."
        ),
    }
    output.mkdir(parents=True)
    for name, data in [
        ("input-manifest", {"rerun": inputs, "round2": older_inputs}),
        ("anomalies", anomalies),
        ("packages", packages),
        ("round2-packages", older),
        ("matched-slots", {"losses": losses, "gains": gains}),
        ("summary", summary),
    ]:
        write(output / (name + ".json"), data)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().output_dir.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
