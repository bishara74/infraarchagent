"""Reproduce Chapter 6 tables from committed evidence only; never load settings."""

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.core.logging import RedactingFilter
from scripts.phase9_common import ROOT, write_json
from scripts.phase9_report import statistics_for, write_csv
from scripts.phase9b_stats import fisher, wilson
from scripts.phase9d_quality import compact_snapshot, quality_table

VARIANTS = ("cost", "performance", "security")
BENCHMARKS = (
    (
        "baseline",
        "20261015T124330508703Z",
        "Generator format enforcement; original quality baseline",
    ),
    (
        "9d",
        "20261015T180417396510Z",
        "Declaration repairs, generation checklist, validation repair",
    ),
    ("9e", "20261016T210350514549Z", "Syntax gates and schema-grounded repair"),
    (
        "9e2",
        "20261017T144629709424Z",
        "Continue bounded repair after unchanged findings",
    ),
    ("A", "20261017T220548142797Z", "Catalogue/templates, partial groups, prompt v7"),
    ("A2", "20261018T163731511036Z", "Syntax recovery and corrected prompt v8"),
    (
        "A3",
        "20261018T213645241170Z",
        "Declaration/deadline recovery, v9/three attempts; provider-limited",
    ),
    (
        "B",
        "20261018T231027886459Z",
        "Haiku fixer; provider-limited incomplete schedule",
    ),
    (
        "final set 1",
        "20261020T010134093069Z",
        "9g fixer wire schema and 9h/runtime changes",
    ),
    ("final set 2", "20261020T013911945957Z", "Matched repeat of final set 1"),
)
# Identifiers captured from immutable source-commit inspection in section 0.
# Generation reads no historical source files, cached inputs or working-tree data.
PROMPT_VERSIONS = {
    "973926bc": "3/1/2",
    "9d703230": "4/1/2",
    "77eefd1a": "5/2/2",
    "dede5c88": "6/3/2",
    "887a4b77": "6/4/2",
    "27d6a124": "7/5/2",
    "acafb82d": "8/6/2",
    "6c0073b9": "9/6/2",
    "84c0198f": "9/7/2",
    "20281387": "9/7/2",
}

SUPPLEMENT = "docs/evals/phase9b-supplement/proposal-counts.json"


class Evidence:
    """Read blobs from an immutable revision, never working-tree evidence."""

    def __init__(self, root: Path, revision: str = "HEAD"):
        self.root = root
        self.revision = (
            self.git("rev-parse", "--verify", revision + "^{commit}").decode().strip()
        )
        self.paths = set(
            self.git("ls-tree", "-r", "--name-only", self.revision)
            .decode()
            .splitlines()
        )
        self.used: dict[str, str] = {}

    def git(self, *args: str) -> bytes:
        return subprocess.check_output(
            ["git", "-C", str(self.root), *args], stderr=subprocess.PIPE
        )

    def read(self, path: str) -> bytes:
        if (
            path not in self.paths
            or not path.startswith("docs/evals/")
            or any(part.startswith(".env") for part in Path(path).parts)
        ):
            raise ValueError("Input must be committed evaluation evidence")
        data = self.git("show", f"{self.revision}:{path}")
        self.used[path] = hashlib.sha256(data).hexdigest()
        return data

    def json(self, path: str):
        return json.loads(self.read(path))


def rate(
    label: str,
    dimension: str,
    group: str,
    passed: int,
    total: int,
    missing: int = 0,
    profile: str = "strict",
) -> dict:
    low, high = wilson(passed, total)
    return {
        "benchmark": label,
        "dimension": dimension,
        "group": group,
        "profile": profile,
        "passed": passed,
        "total": total,
        "rate": passed / total if total else None,
        "wilson_low": low,
        "wilson_high": high,
        "missing_variants": missing,
    }


def complete_rows(rows: list[dict]) -> list[dict]:
    return [
        r
        for r in rows
        if r.get("measurement") in {"pr01", "pr03"}
        and r.get("complete") is True
        and r.get("run_id")
    ]


def run_rate(rows: list[dict], packages: list[dict]) -> tuple[int, int]:
    complete = {r["run_id"] for r in complete_rows(rows)}
    passing = {p["run_id"] for p in packages if p["status"] == "checks_passed"}
    return len(complete & passing), len(complete)


def breakdown(label: str, rows: list[dict], packages: list[dict]) -> list[dict]:
    """Exact text joins work for historical PR-03 rows lacking prompt_index."""
    by_run = {r["run_id"]: r for r in rows if r.get("run_id")}
    prompts = sorted(
        {
            r["prompt"]
            for r in rows
            if r.get("measurement") in {"pr01", "pr03"} and r.get("prompt")
        }
    )
    output = []
    for dimension, groups in (("prompt", prompts), ("variant", VARIANTS)):
        for group in groups:
            selected = [
                p
                for p in packages
                if (
                    by_run[p["run_id"]]["prompt"]
                    if dimension == "prompt"
                    else p["variant"]
                )
                == group
            ]
            expected = (
                3
                * sum(
                    r.get("prompt") == group
                    for r in rows
                    if r.get("measurement") in {"pr01", "pr03"}
                )
                if dimension == "prompt"
                else sum(r.get("measurement") in {"pr01", "pr03"} for r in rows)
            )
            output.append(
                rate(
                    label,
                    dimension,
                    group,
                    sum(p["status"] == "checks_passed" for p in selected),
                    len(selected),
                    expected - len(selected),
                )
            )
    return output


def table(headers: list[str], rows) -> str:
    def cell(value):
        return (
            str(value if value is not None else "unknown")
            .replace("|", "\\|")
            .replace("\n", " ")
        )

    return "\n".join(
        ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        + ["| " + " | ".join(cell(x) for x in row) + " |" for row in rows]
    )


def interval(row: dict) -> str:
    if not row["total"]:
        return "unknown"
    return (
        f"{row['passed']}/{row['total']} ({100 * row['rate']:.2f}%; "
        f"{100 * row['wilson_low']:.2f}–{100 * row['wilson_high']:.2f}%)"
    )


def verdict(summary: str, requirement: str) -> str:
    pattern = (
        r"PR-05 individual thresholds: (\w+)"
        if requirement == "pr05"
        else rf"{requirement} threshold: (\w+)"
    )
    match = re.search(pattern, summary)
    return match[1] if match else "UNMEASURED"


def load_benchmark(evidence: Evidence, folder: str) -> dict:
    base = "docs/evals/" + folder
    env = evidence.json(base + "/environment.json")
    data = evidence.json(base + "/results.json")
    rows = [r for r in data["runs"] if r.get("measurement") in {"pr01", "pr03"}]
    by_run = {r["run_id"]: r for r in rows if r.get("run_id")}
    quality_base = (
        "docs/evals/phase9d-baseline-quality-20261015"
        if folder.endswith("20261015T124330508703Z")
        else base
    )
    packages = []
    for path in sorted(evidence.paths):
        parts = path.split("/")
        if (
            not path.startswith(quality_base + "/quality/")
            or len(parts) != 6
            or parts[-2] not in by_run
            or Path(path).stem not in VARIANTS
        ):
            continue
        raw = evidence.json(path)
        clean = compact_snapshot(raw, RedactingFilter())
        if (
            raw.get("status") == "production_ready"
            and not raw.get("failed_checks")
            and not raw.get("remaining_findings")
        ):
            # Pre-9e benchmark projections omitted validation_result. Preserve
            # their recorded historical automatic label, not a new assessment.
            clean["status"] = "checks_passed"
        packages.append({**clean, "run_id": parts[-2], "variant": Path(path).stem})
    quality, _ = quality_table(packages, missing=3 * len(rows) - len(packages))
    if not packages:
        quality = None
    summary = evidence.read(base + "/summary.md").decode()
    costs = sum(
        (
            Decimal(str(r["cost_usd"]))
            for r in data["runs"]
            if r.get("cost_usd") is not None
        ),
        Decimal(0),
    )
    costs += sum(
        (
            Decimal(str(c["cost_usd"]))
            for c in data.get("cohorts", [])
            if c.get("cost_usd") is not None
        ),
        Decimal(0),
    )
    return {
        "folder": folder,
        "environment": env,
        "rows": rows,
        "packages": packages,
        "quality": quality,
        "data": data,
        "summary": summary,
        "cost": costs,
        "prompt_versions": PROMPT_VERSIONS.get(env["git_commit"][:8], "unknown"),
        "verdicts": {
            key: verdict(summary, key) for key in ("pr01", "pr03", "pr04", "pr05")
        },
    }


def assert_comparable(left: dict, right: dict) -> None:
    """Do not silently pool different prompts, code or effective settings."""
    for key in ("git_commit", "generator_settings", "model", "fixing_model", "tools"):
        if left["environment"].get(key) != right["environment"].get(key):
            raise ValueError("Final benchmark settings are not comparable")
    for benchmark in (left, right):
        if benchmark["environment"].get("git_tracked_dirty") is not False:
            raise ValueError("Final benchmark code provenance is not clean")

    def selections(benchmark):
        return {
            json.dumps(value, sort_keys=True)
            for value in benchmark["environment"]
            .get("resolved_agent_selections", {})
            .values()
        }

    if not selections(left) or selections(left) != selections(right):
        raise ValueError("Final resolved selections are not comparable")

    def schedule(benchmark):
        return Counter(
            (row.get("measurement"), row.get("prompt")) for row in benchmark["rows"]
        )

    if schedule(left) != schedule(right):
        raise ValueError("Final prompt schedules are not comparable")


def generate(
    evidence: Evidence, output: Path, *, experiment_folder: str | None = None
) -> None:
    if output.exists():
        raise ValueError("Report destination already exists; use a fresh --output-dir")
    historical_folders = {
        evidence.root / "docs/evals" / path.split("/")[2]
        for path in evidence.paths
        if path.startswith("docs/evals/")
    }
    if any(
        output.resolve().is_relative_to(folder.resolve())
        for folder in historical_folders
    ):
        raise ValueError("Output cannot be nested in committed evidence")
    if output.resolve().is_relative_to(evidence.root / ".cache"):
        raise ValueError("Cache is read-only")
    inventory = []
    broad_folders = []
    datasets = {}
    for path in sorted(evidence.paths):
        if re.fullmatch(r"docs/evals/phase9-bench-[^/]+/results.json", path):
            folder = path.split("/")[2]
            if folder.startswith("phase9-bench-broad-"):
                broad_folders.append(folder)
                continue
            inventory.append(load_benchmark(evidence, folder))
    by_folder = {b["folder"]: b for b in inventory}
    rates, costs, timings, blockers, main = [], [], [], [], []
    lines = [
        "# Phase 9 final evaluation",
        "",
        f"Committed evidence revision: `{evidence.revision}`.",
        "",
        (
            "Descriptive evaluation of generated candidate IaC; no successful "
            "deployment is implied. Original evidence, thresholds and "
            "readiness rules are unchanged."
        ),
        "",
        "## Main results",
        "",
        (
            "Intervals are Wilson 95%. Missing variants are excluded from "
            "generated-package denominators and shown separately. "
            "Contextual-v1 is experimental (D-48), never an official readiness"
            " policy."
        ),
        "",
    ]
    for label, stamp, change in BENCHMARKS:
        benchmark = by_folder["phase9-bench-real-" + stamp]
        datasets[label] = benchmark
        rows, packages, q = (
            benchmark["rows"],
            benchmark["packages"],
            benchmark["quality"],
        )
        passed = q["counts"]["checks_passed"]
        missing = 3 * len(rows) - len(packages)
        strict = rate(label, "all", "all", passed, len(packages), missing)
        rates.append(strict)
        profiles = all("contextual-v1" in p["profile_assessments"] for p in packages)
        contextual = (
            rate(
                label,
                "all",
                "all",
                sum(
                    p["profile_assessments"]
                    .get("contextual-v1", {})
                    .get("checks_passed", False)
                    for p in packages
                ),
                len(packages),
                missing,
                "contextual-v1",
            )
            if profiles
            else None
        )
        if contextual:
            rates.append(contextual)
        elif label in {"A3", "B"}:
            reclassified = evidence.json(
                f"docs/evals/phase9g-reclassification-20261019/{label}/quality.json"
            )
            view = reclassified.get("profile_rates", {}).get("contextual-v1")
            if view:
                contextual = rate(
                    label,
                    "all",
                    "all",
                    view["passed"],
                    view["packages"],
                    missing,
                    "contextual-v1",
                )
                rates.append(contextual)
        stats = statistics_for(
            [
                r["seconds"]
                for r in rows
                if r["measurement"] == "pr01"
                and r.get("complete")
                and r.get("run_status") in {"success", "partial_success"}
            ]
        )
        usable = sum(
            r.get("run_status") in {"success", "partial_success"} for r in rows
        )
        main.append(
            [
                label,
                change,
                f"{len(complete_rows(rows))}/14 ({usable} usable)",
                interval(strict),
                interval(contextual) if contextual else "unavailable",
                missing,
                stats["median"],
                benchmark["verdicts"]["pr03"],
                benchmark["verdicts"]["pr05"],
                str(benchmark["cost"]),
            ]
        )
        costs.append(
            {
                "benchmark": label,
                "known_cost_usd": str(benchmark["cost"]),
                "unknown_run_costs": sum(r.get("cost_usd") is None for r in rows),
                "cohort_costs_counted_once": len(benchmark["data"].get("cohorts", [])),
            }
        )
        timings.append(
            {
                "benchmark": label,
                "stage": "pr01",
                **stats,
                "verdict": benchmark["verdicts"]["pr01"],
            }
        )
        for stage, values in q["measurements"]["durations"].items():
            timings.append({"benchmark": label, "stage": stage, **values})
        for profile in ("strict", "contextual-v1"):
            counts = Counter()
            known = profile == "strict" or profiles
            if known:
                for p in packages:
                    counts.update(p["remaining_findings"])
                    if profile != "strict":
                        counts.subtract(
                            x["rule_id"]
                            for x in p["profile_assessments"][profile]["excepted"]
                        )
                blockers.extend(
                    {"benchmark": label, "profile": profile, "rule_id": k, "count": n}
                    for k, n in sorted(counts.items())
                    if n > 0
                )
        if label.startswith("final"):
            rates.extend(breakdown(label, rows, packages))
    assert_comparable(datasets["final set 1"], datasets["final set 2"])
    final_rows = datasets["final set 1"]["rows"] + datasets["final set 2"]["rows"]
    final_packages = (
        datasets["final set 1"]["packages"] + datasets["final set 2"]["packages"]
    )
    q, _ = quality_table(final_packages, missing=3)
    combined = rate(
        "final combined",
        "all",
        "all",
        q["counts"]["checks_passed"],
        len(final_packages),
        3,
    )
    contextual_combined = rate(
        "final combined",
        "all",
        "all",
        sum(
            p["profile_assessments"]["contextual-v1"]["checks_passed"]
            for p in final_packages
        ),
        len(final_packages),
        3,
        "contextual-v1",
    )
    rates += [
        combined,
        contextual_combined,
        *breakdown("final combined", final_rows, final_packages),
    ]
    main.append(
        [
            "final combined",
            "Only the matched final repetitions pooled",
            "28/28",
            interval(combined),
            interval(contextual_combined),
            3,
            "see individual sets",
            "FAIL both",
            "PASS both",
            str(datasets["final set 1"]["cost"] + datasets["final set 2"]["cost"]),
        ]
    )
    costs.append(
        {
            "benchmark": "final combined",
            "known_cost_usd": str(
                datasets["final set 1"]["cost"] + datasets["final set 2"]["cost"]
            ),
            "unknown_run_costs": sum(r.get("cost_usd") is None for r in final_rows),
            "cohort_costs_counted_once": 2,
        }
    )
    for stage, values in q["measurements"]["durations"].items():
        timings.append({"benchmark": "final combined", "stage": stage, **values})
    quiet_path = "docs/evals/phase9b-download-quiet/results.json"
    if quiet_path in evidence.paths:
        quiet = evidence.json(quiet_path)
        for condition, values in quiet["summary"].items():
            timings.append(
                {"benchmark": "quiet stub PR-04", "stage": condition, **values}
            )
    for profile in ("strict", "contextual-v1"):
        counts = Counter()
        for item in blockers:
            if (
                item["benchmark"] in {"final set 1", "final set 2"}
                and item["profile"] == profile
            ):
                counts[item["rule_id"]] += item["count"]
        blockers.extend(
            {
                "benchmark": "final combined",
                "profile": profile,
                "rule_id": rule,
                "count": n,
            }
            for rule, n in sorted(counts.items())
        )
    lines += [
        table(
            [
                "Benchmark",
                "Change",
                "Settled/planned",
                "Strict; CI",
                "Contextual; CI",
                "Missing",
                "PR-01 median s",
                "PR-03",
                "PR-05",
                "Known USD",
            ],
            main,
        ),
        "",
        (
            "A3 and B are HTTP-402/provider-usage-limited incomplete "
            "schedules. Each observed 11/14 runs, including a failed PR-03 "
            "baseline; their missing counts omit nine unobserved variant "
            "slots. Other phases differ in prompts/settings/code and are not "
            "silently pooled. Costs are observed usage deltas; zeros do not "
            "establish free inference. Cohort totals are counted once, without"
            " per-run attribution."
        ),
        "",
        "## Statistics and clustering sensitivity",
        "",
    ]
    comparisons = []
    for left, right in (
        ("final combined", "baseline"),
        ("final combined", "A3"),
        ("final set 1", "final set 2"),
    ):
        left_rate = (
            combined
            if left == "final combined"
            else next(
                r
                for r in rates
                if r["benchmark"] == left
                and r["dimension"] == "all"
                and r["profile"] == "strict"
            )
        )
        r = next(
            r
            for r in rates
            if r["benchmark"] == right
            and r["dimension"] == "all"
            and r["profile"] == "strict"
        )
        comparisons.append(
            [
                "package",
                left + " vs " + right,
                f"{left_rate['passed']}/{left_rate['total']}",
                f"{r['passed']}/{r['total']}",
                fisher(
                    left_rate["passed"], left_rate["total"], r["passed"], r["total"]
                ),
            ]
        )
    bpass, btotal = run_rate(
        datasets["baseline"]["rows"], datasets["baseline"]["packages"]
    )
    fpass, ftotal = run_rate(final_rows, final_packages)
    comparisons.append(
        [
            "run",
            "final combined vs baseline",
            f"{fpass}/{ftotal}",
            f"{bpass}/{btotal}",
            fisher(fpass, ftotal, bpass, btotal),
        ]
    )
    rates += [
        rate("baseline", "run", "at least one pass", bpass, btotal),
        rate("final combined", "run", "at least one pass", fpass, ftotal),
    ]
    lines += [
        table(
            ["Unit", "Comparison", "Left", "Right", "Fisher two-sided p"], comparisons
        ),
        "",
        (
            "Fisher tests condition on margins and sum probabilities no "
            "greater than the observed table. Package-level p-values assume "
            "independent packages and are optimistic because the three "
            "variants of a run share one plan. Run-level sensitivity counts "
            "complete runs with at least one checks_passed package, including "
            "complete failed runs in the denominator. It reduces within-run "
            "dependence but does not remove repeated-prompt/provider effects. "
            "P-values are descriptive; p=1 is not proof of reproducibility or "
            "equivalence."
        ),
        "",
        "## Final breakdowns",
        "",
        (
            "Three exact prompt texts, not fourteen distinct prompts, were "
            "used per set. Ten PR-01 runs repeat them 4/3/3; PR-03 adds four "
            "runs of the first prompt. Denominators below are generated "
            "packages; missing variants are separate. Intervals are "
            "descriptive and retain clustering limitations."
        ),
        "",
        table(
            [
                "Set",
                "Dimension",
                "Prompt text / variant",
                "Passed/generated; CI",
                "Missing",
            ],
            [
                [
                    r["benchmark"],
                    r["dimension"],
                    r["group"],
                    interval(r),
                    r["missing_variants"],
                ]
                for r in rates
                if r["dimension"] in {"prompt", "variant"}
            ],
        ),
        "",
        "## Final failure and remediation analysis",
        "",
    ]
    lines += [
        table(
            ["Review reason", "Packages (overlap allowed)"],
            sorted(q["review_reason_counts"].items()),
        ),
        "",
        table(
            ["Failed validation check", "Occurrences"],
            [
                [c["check_id"] + ": " + c["message"], c["count"]]
                for c in q["failed_check_counts"][:10]
            ],
        ),
        "",
    ]
    for profile in ("strict", "contextual-v1"):
        counts = Counter()
        for label in ("final set 1", "final set 2"):
            counts.update(
                {
                    r["rule_id"]: r["count"]
                    for r in blockers
                    if r["benchmark"] == label and r["profile"] == profile
                }
            )
        lines += [
            f"### {profile} remaining blockers",
            "",
            table(["Rule", "Occurrences"], counts.most_common(15)),
            "",
        ]
    lines += [
        (
            "Contextual-v1 removes 9/12 blocker occurrences in set 1/2, but "
            "remaining blockers and invalid validation prevent any extra "
            "package passing. Missing plan-to-resource bindings restrict "
            "broader context rules (D-48); this is not the sole reason equal "
            "pass rates persist."
        ),
        "",
        "### Valid-package near misses",
        "",
        table(
            ["Set", "One blocker", "2–3 blockers", "4+ blockers"],
            [
                [label, *datasets[label]["quality"]["phase9f"]["near_misses"].values()]
                for label in ("final set 1", "final set 2")
            ],
        ),
        "",
        "### Catalogue and template outcomes",
        "",
        table(
            ["Retained catalogue rule", "Occurrences"],
            sorted(q["phase9f"]["catalogue_retained_by_rule"].items()),
        ),
        "",
        table(
            ["Template", "Outcome", "Occurrences"],
            [
                [x["template"], x["status"], x["count"]]
                for x in q["phase9f"]["template_outcomes"]
            ],
        ),
        "",
        "Introduced template-rule occurrences (including rejected candidates): "
        + json.dumps(q["phase9f"]["template_introduced_rules"], sort_keys=True),
        "",
    ]
    supplement = evidence.json(SUPPLEMENT)
    acceptance = Counter()
    for r in supplement["records"]:
        acceptance[(r["benchmark"], "accepted")] += r["accepted"]
        acceptance[(r["benchmark"], "proposals")] += r["proposals"]
    lines += [
        "### Security proposal acceptance before verification",
        "",
        table(
            ["Benchmark", "Accepted", "Proposals"],
            [
                [
                    label,
                    acceptance[(label, "accepted")],
                    acceptance[(label, "proposals")],
                ]
                for label in ("A3", "smoke", "final set 1", "final set 2")
            ],
        ),
        "",
        (
            "The 47/49 figure belongs to the three-run smoke benchmark. Final "
            "proposal acceptance is 295/304. Proposals are not LLM attempts, "
            "verified retained changes or package pass counts. A3 "
            "attempt/format coverage remains unknown. Counts-only supplemental"
            " provenance hashes the read-only cached source snapshots without "
            "committing their contents."
        ),
        "",
        "## Timing and runtime attribution",
        "",
        table(
            ["Benchmark", "Stage", "Count", "Median s", "Max s", "Verdict"],
            [
                [
                    r["benchmark"],
                    r["stage"],
                    r["count"],
                    r["median"],
                    r["max"],
                    r.get("verdict", "descriptive"),
                ]
                for r in timings
            ],
        ),
        "",
    ]
    for label in ("final set 1", "final set 2"):
        lines += [
            f"### {label}: PR-05 workloads",
            "",
            table(
                ["Workload", "Verdict", "Observations", "Failures", "Missing"],
                [
                    [
                        name,
                        v["verdict"],
                        v["observations"],
                        v["failures"],
                        v["missing_measurements"],
                    ]
                    for name, v in datasets[label]["data"]
                    .get("pr05_workloads", {})
                    .items()
                ],
            ),
            "",
        ]
    lines += [
        "### Final runtime telemetry",
        "",
        (
            "Per-run interval-union wall time and summed invocation work are "
            "distinct. Medians below are independent, non-additive and include"
            " only recorded observations."
        ),
        "",
        table(
            ["Set", "Metric", "Runs", "Median", "Maximum"],
            [
                [label, metric, stats["count"], stats["median"], stats["max"]]
                for label in ("final set 1", "final set 2")
                for metric in (
                    "tool_wall_seconds",
                    "tool_invocation_seconds",
                    "tool_queue_seconds",
                    "tool_invocations",
                    "cache_reuses",
                )
                for stats in [
                    statistics_for(
                        [
                            r["runtime_attribution"][metric]
                            for r in datasets[label]["rows"]
                            if metric in (r.get("runtime_attribution") or {})
                        ]
                    )
                ]
            ],
        ),
        "",
    ]
    lines += [
        (
            "D-54 runtime attribution: independent stage medians are not "
            "additive, nested/parallel tool intervals require unions, and "
            "missing historical reasoning/latency stays unknown. The "
            "historical 266.48 → 239.74 s smoke projection is counterfactual, "
            "not measured speedup. One fixed-input replay per configuration "
            "cannot isolate host load or cache warming. See "
            "../../phase9-runtime-attribution.md."
        ),
        "",
        "### PR-03 reference methods",
        "",
        table(
            [
                "Set",
                "Isolated-baseline ratios (official ≤1.5)",
                "PR-01 prompt-median ratios (secondary)",
            ],
            [
                [
                    label,
                    [
                        r["ratio_to_baseline"]
                        for r in datasets[label]["rows"]
                        if r.get("ratio_to_baseline")
                    ],
                    [
                        r.get("ratio_to_pr01_prompt_median")
                        for r in datasets[label]["rows"]
                        if r.get("ratio_to_baseline")
                    ],
                ]
                for label in ("final set 1", "final set 2")
            ],
        ),
        "",
        (
            "The i5-1135G7 / approximately 8 GB WSL2 host runs CPU-heavy local"
            " scanners and Terraform alongside concurrent runs. Resource "
            "contention is consistent with the evidence, but uncontrolled host"
            " load prevents a precise causal decomposition. No threshold or "
            "readiness condition changes."
        ),
        "",
        "## Inventory and comparability",
        "",
    ]
    inventory_rows = []
    for b in inventory:
        e = b["environment"]
        settings = e.get("generator_settings")
        selections = e.get("resolved_agent_selections", {})
        efforts = sorted(
            {
                str(v.get("configured_thinking"))
                for selected in selections.values()
                for v in selected.values()
            }
        )
        observed = b["rows"]
        statuses = Counter(
            r.get(v + "_variant_status") for r in observed for v in VARIANTS
        )
        packages = (
            b["quality"]["counts"]["packages"]
            if b["quality"]
            else sum(
                n
                for status, n in statuses.items()
                if status not in {None, "failed", "not_generated"}
            )
        )
        passed = (
            b["quality"]["counts"]["checks_passed"]
            if b["quality"]
            else statuses["checks_passed"] + statuses["production_ready"]
        )
        inventory_rows.append(
            [
                b["folder"],
                e.get("recorded_at"),
                e["git_commit"],
                e.get("model"),
                e.get("fixing_model"),
                efforts or "unknown; fixer details below",
                b["prompt_versions"],
                len(complete_rows(observed)),
                len(observed),
                3 if "smoke" in b["folder"] else 14,
                statuses[None],
                packages,
                passed,
                3 * len(observed) - packages,
                b["data"].get("stop_reason")
                or (
                    "incomplete observation"
                    if any(not r.get("complete") for r in observed)
                    else "schedule settled"
                ),
                *b["verdicts"].values(),
                str(b["cost"]),
            ]
        )
        lines += [
            f"### {b['folder']}",
            "",
            "Captured settings: `" + json.dumps(settings, sort_keys=True) + "`.",
            "",
        ]
        if b["quality"]:
            lines += [
                "Recorded fixer configurations: `"
                + json.dumps(b["quality"]["phase9f"]["fixer_models"], sort_keys=True)
                + "`.",
                "",
            ]
    lines += [
        table(
            [
                "Folder",
                "Date UTC",
                "Commit",
                "Generation model",
                "Fixer model",
                "Effort",
                "Prompt G/F/A",
                "Settled",
                "Observed",
                "Planned pipeline runs",
                "Unknown variant slots",
                "Packages",
                "Passed",
                "Missing observed",
                "Stop",
                "PR-01",
                "PR-03",
                "PR-04",
                "PR-05",
                "Known USD",
            ],
            inventory_rows,
        ),
        "",
        (
            "Only final sets 1 and 2 are pooled: same commit, three prompt "
            "texts, settings and resolved low-effort gpt-oss-120b selections. "
            "All other phases are descriptive comparisons. A3/B are "
            "incomplete; B changes fixer model. Smoke samples cannot establish"
            " ten-run PR-01. Stub timings are rehearsal evidence, not real-"
            "provider performance. Historical production_ready preserves the "
            "recorded benchmark label when no failures/blockers were stored; "
            "early validity metadata is absent. Automatic labels do"
            " not establish deployment success."
        ),
        "",
        "## Threats to validity",
        "",
        (
            "Single WSL2 machine; one model family in the matched final "
            "comparison; three prompt texts repeatedly sampled; shared plans "
            "and repeated prompts; changing local work and provider "
            "routing/load; incomplete provider-limited sets; usage-delta cost "
            "limitations; stub/real differences; no deployment validation; "
            "exploratory multiple comparisons. NFR-04 clean deployment remains"
            " unverified."
        ),
    ]
    # Later numbered sections supply committed collection and latency evidence.
    for path, title in (
        ("docs/evals/phase9b-traceability/traceability.md", "Requirement traceability"),
        ("docs/evals/phase9b-download-quiet/summary.md", "PR-04 attribution"),
    ):
        if path in evidence.paths:
            content = evidence.read(path).decode()
            if "traceability" in path:
                trace = content + (
                    "\nCollection snapshot: committed section 2 evidence. Later "
                    "reporting-tool tests are recorded in the implementation log; "
                    "links do not assert passing results.\n"
                )
            else:
                lines += ["", "## " + title, "", content]
    output.mkdir(parents=True, exist_ok=False)
    (output / "report.md").write_text("\n".join(lines).rstrip() + "\n")
    if "trace" in locals():
        (output / "traceability.md").write_text(trace)
    write_csv(output / "rates.csv", rates)
    write_csv(output / "blockers.csv", blockers)
    write_csv(output / "timings.csv", timings)
    write_csv(output / "costs.csv", costs)
    from scripts.phase9i_broad_report import append_broad_report

    append_broad_report(evidence, broad_folders, datasets, output)
    if experiment_folder:
        from scripts.phase9k_report import append_experiment_report

        append_experiment_report(evidence, experiment_folder, output)
    write_json(
        output / "input-manifest.json",
        {
            "revision": evidence.revision,
            "folders": sorted({str(Path(p).parent) for p in evidence.used}),
            "files": [
                {"path": p, "sha256": h} for p, h in sorted(evidence.used.items())
            ],
        },
    )
    print(
        f"Report: {len(inventory)} benchmark folders; {len(rates)} rate rows; "
        f"{len(evidence.used)} hashed input files"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--experiment-folder")
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "docs/evals/phase9-final-report"
    )
    args = parser.parse_args()
    generate(
        Evidence(ROOT, args.revision),
        args.output_dir,
        experiment_folder=args.experiment_folder,
    )


if __name__ == "__main__":
    main()
