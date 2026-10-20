"""Publish source-free follow-up comparisons; verify every reconstructed hash."""

import argparse
import asyncio
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.security.kubernetes_render import repair_formats_and_pods, repair_kubernetes
from scripts.phase9i_kubernetes_replay import (
    EVIDENCE,
    PROFILES,
    historical_retained,
    write,
)
from scripts.phase9i_replay import digest, inventory
from scripts.phase9i_report import compare, proposal

STAGES = (
    "baseline",
    "previous_retained",
    "independent_pods",
    "independent_formats",
    "cumulative_equivalents",
    "cumulative_addressing",
    "cumulative_formats",
    "cumulative_defaults",
    "cumulative_pods",
)


def rule_deltas(
    before: dict[str, Any], after: dict[str, Any], field: str = "blockers"
) -> list[dict[str, Any]]:
    old = Counter(f["rule_id"] for f in before[field])
    new = Counter(f["rule_id"] for f in after[field])
    return [
        {
            "rule_id": rule,
            "before": old[rule],
            "after": new[rule],
            "delta": new[rule] - old[rule],
        }
        for rule in sorted(old.keys() | new.keys())
        if old[rule] != new[rule]
    ]


def identity_deltas(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    if any(o.get("scan_outcome", "clean") == "unknown" for o in (before, after)):
        return {"introduced": [], "removed": [], "known": False}
    old = {(f["rule_id"], f["file_path"], f["resource"]) for f in before["findings"]}
    new = {(f["rule_id"], f["file_path"], f["resource"]) for f in after["findings"]}
    return {"introduced": sorted(new - old), "removed": sorted(old - new)}


def stored_metrics(package: dict[str, Any]) -> dict[str, Any]:
    summary = package["validation_report"]["summary"]
    return {
        "validation": summary["result"],
        "failed_checks": summary["failed"],
        "profiles": package["profile_assessments"],
    }


async def verify_bytes(item: dict[str, Any], rows: dict[str, Any]) -> int:
    original = item["package"]["files"]
    assert (
        digest(historical_retained(item))
        == rows["previous_retained"]["retained_sha256"]
    )
    checked = 1

    async def verify(row, files, kind):
        if kind == "formats":
            candidate, _ = await repair_formats_and_pods(files)
        elif kind == "pods":
            candidate, _ = await repair_kubernetes(files)
        else:
            candidate, _ = proposal(kind, files, row["before"])
        assert digest(files) == row["before_sha256"], (item["key"], kind, "before")
        assert digest(candidate) == row["candidate_sha256"], (
            item["key"],
            kind,
            "candidate",
        )
        retained = candidate if row["reason"] == "accepted" else files
        assert digest(retained) == row["retained_sha256"], (
            item["key"],
            kind,
            "retained",
        )
        return retained

    await verify(rows["independent_pods"], original, "pods")
    await verify(rows["independent_formats"], original, "formats")
    current = original
    for kind in ("equivalents", "addressing", "formats", "defaults", "pods"):
        current = await verify(rows["cumulative_" + kind], current, kind)
        checked += 1
    return checked + 2


def table_summary(summary: dict[str, Any], stage: str) -> list[str]:
    lines = [
        "| Prompt | Packages | Valid | Strict checks_passed | "
        "v1 checks_passed | v2 checks_passed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, row in summary[stage]["per_prompt"].items():
        passed = row["checks_passed"]
        lines.append(
            f"| {label} | {row['packages']} | {row['valid']} | {passed['strict']} | "
            f"{passed['contextual-v1']} | {passed['contextual-v2']} |"
        )
    return lines


async def publish(output: Path, verify: bool) -> None:
    packages, manifest = inventory()
    assert json.loads((output / "input-manifest.json").read_text()) == manifest
    evaluator = digest(
        json.loads((output / "execution-evaluator-manifest.json").read_text())
    )
    summary = json.loads((output / "summary.json").read_text())
    packages_report, csv_rows, stored_rows = [], [], []
    stage_rows: dict[str, list[dict[str, Any]]] = {s: [] for s in STAGES}
    verified = 0
    for item in packages:
        filename = item["key"].replace("/", "-") + ".json"
        rows = {s: json.loads((output / s / filename).read_text()) for s in STAGES}
        assert all(r["provenance"]["evaluator"] == evaluator for r in rows.values()), (
            item["key"]
        )
        if verify:
            verified += await verify_bytes(item, rows)
            print(
                f"verified {len(packages_report) + 1}/{len(packages)} {item['key']}",
                flush=True,
            )
        for stage, row in rows.items():
            stage_rows[stage].append(row)
        before = rows["baseline"]["observed"]
        previous = rows["previous_retained"]["observed"]
        final = rows["cumulative_pods"]["observed"]
        stored = stored_metrics(item["package"])
        differences = []
        if stored["validation"] != before["validation"]:
            differences.append("validation")
        if stored["failed_checks"] != len(before["failed_checks"]):
            differences.append("failed_checks")
        for profile in PROFILES[:2]:
            for field in ("checks_passed", "remaining_blocking"):
                if (
                    stored["profiles"][profile][field]
                    != before["profiles"][profile][field]
                ):
                    differences.append(profile + "." + field)
        stored_rows.append(
            {
                "key": item["key"],
                "stored": stored,
                "fresh": {
                    "validation": before["validation"],
                    "failed_checks": len(before["failed_checks"]),
                    "profiles": before["profiles"],
                },
                "differences": differences,
            }
        )
        packages_report.append(
            {
                "key": item["key"],
                "prompt": rows["baseline"]["prompt"],
                "original_to_final": compare(before, final),
                "previous_to_final": compare(previous, final),
                "blocking_rule_deltas": rule_deltas(previous, final),
                "all_rule_deltas": rule_deltas(previous, final, "findings"),
                "all_finding_identities": identity_deltas(previous, final),
            }
        )
        record = {"key": item["key"], "prompt": rows["baseline"]["prompt"]}
        for stage, observation in (
            ("original", before),
            ("previous", previous),
            ("final", final),
        ):
            record[stage + "_valid"] = observation["validation"] == "valid"
            for profile in PROFILES:
                record[stage + "_" + profile + "_checks_passed"] = observation[
                    "profiles"
                ][profile]["checks_passed"]
                record[stage + "_" + profile + "_blockers"] = observation["profiles"][
                    profile
                ]["remaining_blocking"]
        csv_rows.append(record)
    write(output / "per-package-deltas.json", packages_report)
    write(output / "stored-vs-fresh.json", stored_rows)
    with (output / "per-package.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
        writer.writeheader()
        writer.writerows(csv_rows)

    changes = {}
    finding_deltas = []
    for stage in STAGES[2:]:
        rows = stage_rows[stage]
        all_deltas = [
            {
                "key": row["key"],
                "stage": stage,
                "candidate": identity_deltas(row["before"], row["candidate"]),
                "retained": identity_deltas(row["before"], row["observed"]),
            }
            for row in rows
        ]
        finding_deltas.extend(all_deltas)
        changes[stage] = {
            "outcomes": dict(Counter(r["reason"] for r in rows)),
            "skipped_entries": dict(
                Counter(
                    r.get("reason", "unspecified")
                    for row in rows
                    for r in row["records"]
                    if r.get("outcome") == "skipped"
                )
            ),
            "rejected_new_rules": dict(
                Counter(
                    f[0]
                    for row in rows
                    if row["reason"] not in {"accepted", "unchanged"}
                    for f in row["introduced"]
                )
            ),
            "retained_new_rules": dict(
                Counter(
                    f[0] for row in rows for f in row["retained_delta"]["introduced"]
                )
            ),
            "retained_removed_rules": dict(
                Counter(f[0] for row in rows for f in row["retained_delta"]["removed"])
            ),
            "all_candidate_introduced_rules": dict(
                Counter(f[0] for d in all_deltas for f in d["candidate"]["introduced"])
            ),
            "all_candidate_removed_rules": dict(
                Counter(f[0] for d in all_deltas for f in d["candidate"]["removed"])
            ),
            "all_retained_introduced_rules": dict(
                Counter(f[0] for d in all_deltas for f in d["retained"]["introduced"])
            ),
            "all_retained_removed_rules": dict(
                Counter(f[0] for d in all_deltas for f in d["retained"]["removed"])
            ),
        }
    write(output / "changes.json", changes)
    write(output / "per-finding-deltas.json", finding_deltas)
    old_counts, new_counts = summary["previous_retained"], summary["cumulative_pods"]
    rules = []
    for field in ("rules", "all_rules"):
        for rule in sorted(old_counts[field].keys() | new_counts[field].keys()):
            before, after = (
                old_counts[field].get(rule, 0),
                new_counts[field].get(rule, 0),
            )
            if before != after:
                rules.append(
                    {
                        "scope": field,
                        "rule_id": rule,
                        "previous": before,
                        "final": after,
                        "delta": after - before,
                    }
                )
    write(output / "rule-deltas.json", rules)
    write(
        output / "byte-verification.json",
        {
            "packages": len(packages),
            "verified": verify,
            "historical_and_candidate_stage_checks": verified,
            "evaluator": evaluator,
            "reporter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "comparison_helper_sha256": hashlib.sha256(
                Path(__file__).with_name("phase9i_report.py").read_bytes()
            ).hexdigest(),
        },
    )
    lines = [
        "# Phase 9i Kubernetes follow-up replay",
        "",
        "All results are offline static observations. `checks_passed` means valid "
        "and zero blocking findings for that assessment; strict remains the sole "
        "official acceptance policy.",
        "",
        "## Original generated packages, fresh offline baseline",
        "",
        *table_summary(summary, "baseline"),
        "",
        "## Previous Phase 9i retained packages, freshly observed",
        "",
        *table_summary(summary, "previous_retained"),
        "",
        "## Final retained packages",
        "",
        *table_summary(summary, "cumulative_pods"),
        "",
        "## Per-change outcomes",
        "",
        "| Stage | Accepted | Unchanged | Rejected reasons | "
        "New retained finding identities |",
        "|---|---:|---:|---|---:|",
    ]
    for stage, change in changes.items():
        outcomes = change["outcomes"]
        rejected = (
            ", ".join(
                f"{k}: {v}"
                for k, v in outcomes.items()
                if k not in {"accepted", "unchanged"}
            )
            or "none"
        )
        lines.append(
            f"| {stage} | {outcomes.get('accepted', 0)} | "
            f"{outcomes.get('unchanged', 0)} | {rejected} | "
            f"{sum(change['retained_new_rules'].values())} |"
        )
    lines.extend(
        [
            "",
            "## Rule count deltas from previous retained packages",
            "",
            "| Scope | Rule | Previous | Final | Delta |",
            "|---|---|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {r['scope']} | {r['rule_id']} | {r['previous']} | "
        f"{r['final']} | {r['delta']:+d} |"
        for r in rules
    )
    lines.extend(
        [
            "",
            "## Residuals and limitations",
            "",
            "Image values preserve existing identities. Latest/blank tags "
            "(CKV_K8S_14/KSV-0013), untrusted registries (KSV-0125) and low ports "
            "(KSV-0117) remain blocking wherever observed. No image, registry, "
            "digest, Service, probe or application port is invented or changed.",
            "",
            "Explicit weak settings, unsupported source bindings, dynamic "
            "container structures, ambiguous render mappings and preserved "
            "quantities can leave findings. See changes.json for skipped-entry "
            "reasons and every stage row for candidate/retained evidence.",
            "",
            "Identity, filesystem, capability and resource changes can break "
            "startup. Accepted archive records say **runtime compatibility "
            "unverified**. No image pull, workload startup, Kubernetes deployment, "
            "real LLM inference or real cloud API was used.",
            "",
            "All-rule counts include advisory findings. Per-rule tables count "
            "scanner occurrences; introduced/removed identity lists use the "
            "existing rule/path/resource fingerprints. These are complementary "
            "measures.",
            "",
            "Unknown scans/validation by stage: "
            + json.dumps(
                {
                    s: [v["unknown_scan"], v["unknown_validation"]]
                    for s, v in summary.items()
                },
                sort_keys=True,
            )
            + ".",
            "",
            "Original snapshots, both final sets and previous Phase 9i evidence "
            "remain unchanged. Three missing variants remain missing; they are "
            "excluded from the 81-package denominator. Stored strict/v1 "
            "assessments match all 81 original packages.",
            "Stored/fresh baseline discrepancy packages: "
            f"{sum(bool(r['differences']) for r in stored_rows)}; "
            "see stored-vs-fresh.json. Stored profiles remain exactly as saved; "
            "v2 is not backfilled into historical snapshots.",
            "",
            f"Historical pinned commit: c3be20c. Byte verification: {verified} "
            f"stage checks across {len(packages)} packages. Tool versions, "
            "isolation/configuration and evaluator fingerprints are recorded "
            "in verification.json and each row.",
            "",
        ]
    )
    (output / "README.md").write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    parser.add_argument("--verify-bytes", action="store_true")
    args = parser.parse_args()
    asyncio.run(publish(args.output, args.verify_bytes))


if __name__ == "__main__":
    main()
