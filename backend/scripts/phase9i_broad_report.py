"""Descriptive broad tables from committed evidence, separate from final sets."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from app.core.logging import RedactingFilter
from scripts.benchmark import eligible
from scripts.phase9_common import write_json
from scripts.phase9_report import statistics_for, write_csv
from scripts.phase9b_stats import fisher, wilson
from scripts.phase9d_quality import compact_snapshot, quality_table
from scripts.phase9i_broad import METADATA_FIELDS, SCENARIO_PATH, broad_schedule

PROFILES = ("strict", "contextual-v1", "contextual-v2")


def load_broad(evidence, folder: str) -> dict:
    base = "docs/evals/" + folder
    env = evidence.json(base + "/environment.json")
    raw = evidence.read(base + "/broad-v1.json")
    digest = hashlib.sha256(raw).hexdigest()
    if env.get("benchmark_kind") != "broad" or env.get("scenario_sha256") != digest:
        raise ValueError("Broad registration hash mismatch")
    registered = evidence.git("show", f"{env['registration_commit']}:{SCENARIO_PATH}")
    if registered != raw:
        raise ValueError("Broad registration differs from pre-registered commit")
    evidence.git(
        "merge-base", "--is-ancestor", env["registration_commit"], env["git_commit"]
    )
    registration = json.loads(raw)
    slots = broad_schedule(registration, env["runs_per_scenario"], digest)
    data = evidence.json(base + "/results.json")
    rows = data["runs"]
    if (
        env["planned_runs"] != len(slots)
        or len(rows) != len(slots)
        or data.get("cohorts")
    ):
        raise ValueError("Broad schedule is inconsistent")
    for row, slot in zip(rows, slots, strict=True):
        if (
            any(row.get(k) != value for k, value in slot.items())
            or row.get("mode") != env["mode"]
        ):
            raise ValueError("Broad row differs from registered schedule")
    by_run = {r["run_id"]: r for r in rows if r.get("run_id") and r.get("complete")}
    packages = []
    for path in sorted(evidence.paths):
        parts = path.split("/")
        if (
            path.startswith(base + "/quality/")
            and len(parts) == 6
            and parts[-2] in by_run
            and Path(path).stem in {"cost", "performance", "security"}
        ):
            raw_package = evidence.json(path)
            if any(raw_package.get(k) != by_run[parts[-2]][k] for k in METADATA_FIELDS):
                raise ValueError("Broad package scenario metadata mismatch")
            packages.append(
                {
                    **compact_snapshot(raw_package, RedactingFilter()),
                    "run_id": parts[-2],
                    "variant": Path(path).stem,
                }
            )
    return {
        "folder": folder,
        "environment": env,
        "rows": rows,
        "packages": packages,
        "registration": registration,
    }


def passing(package: dict, profile: str):
    view = package.get("profile_assessments", {}).get(profile)
    if isinstance(view, dict):
        return view.get("checks_passed") is True
    if profile == "strict":
        return package.get("status") == "checks_passed"
    return None


def counts(packages: list[dict], profile: str):
    values = [passing(p, profile) for p in packages]
    return sum(values) if values and all(v is not None for v in values) else None


def grouped(benchmark: dict) -> tuple[list[dict], list[dict]]:
    rows, packages = benchmark["rows"], benchmark["packages"]
    scenarios = benchmark["registration"]["scenarios"]
    groups = [("scenario", s["id"], {s["id"]}) for s in scenarios]
    groups += [
        ("complexity", level, {s["id"] for s in scenarios if s["complexity"] == level})
        for level in range(1, 6)
    ]
    output, blockers = [], []
    for dimension, group, ids in groups:
        selected = [r for r in rows if r["scenario_id"] in ids]
        observed = [r for r in selected if r.get("execution_status") != "not_started"]
        settled = [r for r in observed if r.get("complete") and r.get("run_id")]
        run_ids = {r["run_id"] for r in settled}
        generated = [p for p in packages if p["run_id"] in run_ids]
        times = [
            r["seconds"]
            for r in settled
            if eligible(r) and r.get("seconds") is not None
        ]
        costs = [r["cost_usd"] for r in settled if r.get("cost_usd") is not None]
        shared = {
            "benchmark": benchmark["folder"],
            "mode": benchmark["environment"]["mode"],
            "dimension": dimension,
            "group": group,
            "planned_runs": len(selected),
            "observed_runs": len(observed),
            "settled_runs": len(settled),
            "not_started": len(selected) - len(observed),
            "incomplete_runs": len(observed) - len(settled),
            "failed_runs": sum(r.get("run_status") == "failed" for r in settled),
            "packages": len(generated),
            "valid": sum(p.get("validation_result") == "valid" for p in generated),
            "missing_variants": 3 * len(settled) - len(generated),
            "unknown_variant_slots": 3
            * sum(bool(r.get("run_id")) and not r.get("complete") for r in observed),
            "timed_runs": len(times),
            "median_seconds": statistics_for(times)["median"],
            "priced_runs": len(costs),
            "median_cost_usd": statistics_for(costs)["median"],
        }
        for profile in PROFILES:
            passed = counts(generated, profile)
            low, high = (
                wilson(passed, len(generated)) if passed is not None else (None, None)
            )
            output.append(
                {
                    **shared,
                    "profile": profile,
                    "passed": passed,
                    "rate": passed / len(generated) if passed is not None else None,
                    "wilson_low": low,
                    "wilson_high": high,
                }
            )
            if passed is None:
                continue
            rules = Counter()
            for package in generated:
                rules.update(package["remaining_findings"])
                if profile != "strict":
                    rules.subtract(
                        e["rule_id"]
                        for e in package["profile_assessments"][profile]["excepted"]
                    )
            blockers.extend(
                {
                    "benchmark": benchmark["folder"],
                    "mode": shared["mode"],
                    "dimension": dimension,
                    "group": group,
                    "profile": profile,
                    "rule_id": rule,
                    "count": count,
                }
                for rule, count in sorted(rules.items(), key=lambda x: (-x[1], x[0]))
                if count > 0
            )
    return output, blockers


def anchor_comparisons(benchmark: dict, finals: dict) -> list[dict]:
    if benchmark["environment"]["mode"] != "real":
        return []
    result = []
    for scenario in benchmark["registration"]["scenarios"]:
        if scenario["id"] not in {2, 9, 10}:
            continue
        prompt = scenario["prompt"]
        for label, baseline in finals.items():
            left_rows = [r for r in benchmark["rows"] if r["prompt"] == prompt]
            right_rows = [r for r in baseline["rows"] if r.get("prompt") == prompt]
            left_ids = {
                r["run_id"] for r in left_rows if r.get("complete") and r.get("run_id")
            }
            right_ids = {
                r["run_id"] for r in right_rows if r.get("complete") and r.get("run_id")
            }
            left = [p for p in benchmark["packages"] if p["run_id"] in left_ids]
            right = [p for p in baseline["packages"] if p["run_id"] in right_ids]
            for profile in PROFILES:
                a, b = counts(left, profile), counts(right, profile)
                for unit in ("package", "run"):
                    n, m = (
                        (len(left), len(right))
                        if unit == "package"
                        else (len(left_ids), len(right_ids))
                    )
                    x, y = a, b
                    if unit == "run":
                        x = (
                            len({p["run_id"] for p in left if passing(p, profile)})
                            if a is not None
                            else None
                        )
                        y = (
                            len({p["run_id"] for p in right if passing(p, profile)})
                            if b is not None
                            else None
                        )
                    result.append(
                        {
                            "benchmark": benchmark["folder"],
                            "scenario_id": scenario["id"],
                            "comparison": label,
                            "profile": profile,
                            "unit": unit,
                            "broad_passed": x,
                            "broad_total": n,
                            "final_passed": y,
                            "final_total": m,
                            "fisher_two_sided": fisher(x, n, y, m)
                            if x is not None and y is not None and n and m
                            else None,
                        }
                    )
    return result


def append_broad_report(
    evidence, folders: list[str], datasets: dict, output: Path
) -> None:
    if not folders:
        return
    # Local import keeps the existing historical generator independent of this module.
    from scripts.phase9b_report import interval, table

    finals = {k: datasets[k] for k in ("final set 1", "final set 2")}
    finals["final combined"] = {
        "rows": [r for b in finals.values() for r in b["rows"]],
        "packages": [p for b in finals.values() for p in b["packages"]],
    }
    lines = [
        "",
        "## Broad scenario benchmark",
        "",
        "Descriptive statistics for one model family, with two runs per "
        "scenario by default. "
        "Actual repetition counts and model selections are recorded "
        "below. Complexity is "
        "pre-assigned, not inferred from generated resources. PR-01 "
        "timing has no verdict; "
        "PR-05 retains the existing thresholds. Stub results are "
        "rehearsals, separate from real results.",
        "",
        "Rates use generated packages; missing variants count only "
        "settled runs. Unstarted slots "
        "are excluded, and incomplete accepted runs have unknown variant "
        "slots. Timing includes "
        "eligible success/partial-success runs; cost medians use known "
        "settled sequential costs. "
        "Missing measurements remain unavailable.",
        "",
    ]
    all_groups, all_blockers, all_comparisons = [], [], []
    for folder in folders:
        benchmark = load_broad(evidence, folder)
        groups, blockers = grouped(benchmark)
        comparisons = anchor_comparisons(benchmark, finals)
        all_groups.extend(groups)
        all_blockers.extend(blockers)
        all_comparisons.extend(comparisons)
        env = benchmark["environment"]
        lines += [
            f"### {folder} ({env['mode']})",
            "",
            f"Runs per scenario: {env['runs_per_scenario']}; "
            f"registration SHA-256: `{env['scenario_sha256']}`; "
            f"registration commit: `{env['registration_commit']}`.",
            "",
            "Recorded model: "
            + str(env.get("model", "unknown"))
            + "; fixer: "
            + str(env.get("fixing_model", "unknown"))
            + ".",
            "",
            "Resolved selections: `"
            + json.dumps(env.get("resolved_agent_selections", {}), sort_keys=True)
            + "`.",
            "",
        ]
        for dimension in ("scenario", "complexity"):
            table_rows = []
            for group in sorted(
                {r["group"] for r in groups if r["dimension"] == dimension}
            ):
                views = {
                    r["profile"]: r
                    for r in groups
                    if r["dimension"] == dimension and r["group"] == group
                }
                row = views["strict"]
                rates = [
                    interval({**views[p], "total": row["packages"]})
                    if views[p]["passed"] is not None
                    else "unavailable"
                    for p in PROFILES
                ]
                top = (
                    "; ".join(
                        f"{b['profile']}:{b['rule_id']}={b['count']}"
                        for p in PROFILES
                        for b in [
                            x
                            for x in blockers
                            if x["dimension"] == dimension
                            and x["group"] == group
                            and x["profile"] == p
                        ][:5]
                    )
                    or "none observed / unavailable"
                )
                table_rows.append(
                    [
                        (
                            f"{group}. "
                            + next(
                                s["name"]
                                for s in benchmark["registration"]["scenarios"]
                                if s["id"] == group
                            )
                            if dimension == "scenario"
                            else group
                        ),
                        row["packages"],
                        row["valid"],
                        *rates,
                        row["missing_variants"],
                        row["not_started"],
                        row["incomplete_runs"],
                        row["unknown_variant_slots"],
                        row["failed_runs"],
                        f"{row['median_seconds']} (n={row['timed_runs']})",
                        f"{row['median_cost_usd']} (n={row['priced_runs']})",
                        top,
                    ]
                )
            lines += [
                "#### "
                + (
                    "Per scenario"
                    if dimension == "scenario"
                    else "Per complexity level"
                ),
                "",
                table(
                    [
                        "ID / level",
                        "Packages",
                        "Valid",
                        "Strict; Wilson 95%",
                        "Contextual-v1; Wilson 95%",
                        "Contextual-v2; Wilson 95%",
                        "Missing",
                        "Unstarted",
                        "Incomplete",
                        "Unknown slots",
                        "Failed runs",
                        "Median s",
                        "Median USD",
                        "Top blockers",
                    ],
                    table_rows,
                ),
                "",
            ]
        complexity_rates = [r for r in groups if r["dimension"] == "complexity"]
        lines += [
            "#### Pass rate versus complexity level",
            "",
            table(
                ["Level", "Packages", *PROFILES],
                [
                    [
                        level,
                        next(
                            r["packages"]
                            for r in complexity_rates
                            if r["group"] == level
                        ),
                        *[
                            next(
                                interval({**r, "total": r["packages"]})
                                if r["passed"] is not None
                                else "unavailable"
                                for r in complexity_rates
                                if r["group"] == level and r["profile"] == profile
                            )
                            for profile in PROFILES
                        ],
                    ]
                    for level in range(1, 6)
                ],
            ),
            "",
        ]
        if comparisons:
            lines += [
                "#### Anchors versus final sets",
                "",
                table(
                    [
                        "Scenario",
                        "Final set",
                        "Profile",
                        "Unit",
                        "Broad",
                        "Final",
                        "Fisher two-sided p",
                    ],
                    [
                        [
                            r["scenario_id"],
                            r["comparison"],
                            r["profile"],
                            r["unit"],
                            f"{r['broad_passed']}/{r['broad_total']}",
                            f"{r['final_passed']}/{r['final_total']}",
                            r["fisher_two_sided"],
                        ]
                        for r in comparisons
                    ],
                ),
                "",
            ]
        quality, _ = quality_table(benchmark["packages"], missing=0)
        if "generator_schema_overflow" in quality:
            lines += [
                "Schema-only context sizes: "
                + str(quality["schema_context_chars"].get("generator_schema_only")),
                "",
                "Schema guidance overflow (omitted types by tier): "
                + str(quality["generator_schema_overflow"]),
                "",
            ]
        summary = evidence.read("docs/evals/" + folder + "/summary.md").decode()
        pr05 = re.search(r"PR-05 individual thresholds: (\w+)", summary)
        lines += [
            "PR-05 recorded verdict: " + (pr05[1] if pr05 else "UNMEASURED") + ".",
            "",
        ]
    lines += [
        "Wilson intervals and Fisher tests are descriptive. Three "
        "variants share a plan, so "
        "package independence is unrealistic and package-level p-values "
        "are optimistic. Run-level "
        "sensitivity counts complete runs with at least one passing "
        "package, including complete "
        "failed runs in the denominator. Repeated prompts, provider "
        "conditions, model choices and "
        "changed code remain confounders; these comparisons cannot "
        "isolate the causal effect of "
        "Phase 9i. Historical contextual-v2 remains unavailable. No "
        "deployment success is implied.",
        "",
    ]
    with (output / "report.md").open("a") as report:
        report.write("\n".join(lines))
    write_csv(output / "broad-groups.csv", all_groups)
    write_csv(
        output / "broad-complexity.csv",
        [r for r in all_groups if r["dimension"] == "complexity"],
    )
    write_csv(
        output / "broad-blockers.csv",
        all_blockers,
        ["benchmark", "mode", "dimension", "group", "profile", "rule_id", "count"],
    )
    write_csv(
        output / "broad-anchors.csv",
        all_comparisons,
        [
            "benchmark",
            "scenario_id",
            "comparison",
            "profile",
            "unit",
            "broad_passed",
            "broad_total",
            "final_passed",
            "final_total",
            "fisher_two_sided",
        ],
    )
    write_json(
        output / "broad-summary.json",
        {
            "folders": folders,
            "groups": all_groups,
            "anchor_comparisons": all_comparisons,
        },
    )
