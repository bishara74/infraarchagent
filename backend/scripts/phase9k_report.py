"""Architect experiment comparison from immutable evidence; no settings or rescans."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from app.domain.agent_selection import ROLES
from scripts.benchmark import timings
from scripts.phase9_common import write_json
from scripts.phase9_report import statistics_for, write_csv
from scripts.phase9i_broad_report import grouped, load_broad
from scripts.phase9k_audit import BASELINE_AUDIT
from scripts.phase9k_catalogue import BASELINE_FOLDERS
from scripts.phase9k_routing import routing_statistics

EXPOSURES = ("public", "internal", "mixed", "absent", "unknown")
RULES = ("AWS-0053", "CKV_AWS_91")


def unique_calls(row: dict, role=None) -> list[dict]:
    seen, result = set(), []
    for i, call in enumerate(row.get("telemetry", [])):
        if call.get("kind") != "llm" or role and call.get("role") != role:
            continue
        identity = call.get("call_id") or call.get("id") or ("unknown", i)
        if identity not in seen:
            seen.add(identity)
            result.append(call)
    return result


def architect_diagnostics(row: dict, agent_seconds=None) -> dict:
    calls = unique_calls(row, "architect")

    def total(field):
        values = [c.get(field) for c in calls]
        return (
            sum(values)
            if values and all(type(v) in {int, float} for v in values)
            else None
        )

    return {
        "run_id": row.get("run_id"),
        "scenario_id": row["scenario_id"],
        "complexity": row["complexity"],
        "complete": row.get("complete"),
        "architect_calls": len(calls),
        "architect_agent_seconds": agent_seconds,
        "architect_llm_seconds": total("elapsed_seconds"),
        "reasoning_tokens": total("reasoning_tokens"),
        "input_tokens": total("input_tokens"),
        "output_tokens": total("output_tokens"),
        "finish_reasons": dict(
            Counter(c.get("finish_reason") or "unknown" for c in calls)
        ),
        "unknown_finish_reasons": sum(not c.get("finish_reason") for c in calls),
        "truncated_calls": sum(
            c.get("format_reason") == "truncated"
            or c.get("category") == "truncated"
            or c.get("finish_reason") in {"length", "max_tokens"}
            for c in calls
        ),
        "timeout_calls": sum(c.get("category") == "timeout" for c in calls),
        "deadline_calls": sum(
            c.get("category") == "deadline" or c.get("deadline_exceeded") is True
            for c in calls
        ),
        "failure_categories": row.get("failure_categories"),
    }


def run_selections(benchmark: dict, row: dict) -> dict:
    return benchmark["environment"].get("resolved_agent_selections", {}).get(
        row.get("run_id")
    ) or benchmark["environment"].get("benchmark_preflight", {}).get("selections", {})


def run_statistics(benchmark: dict, row: dict) -> dict:
    return routing_statistics(
        unique_calls(row),
        run_selections(benchmark, row),
        benchmark["environment"].get("provider_aliases"),
    )


def combine_routing(stats: list[dict]) -> dict:
    counts = {
        key: sum(s[key] for s in stats)
        for key in (
            "preferred_calls",
            "fallback_calls",
            "unknown_calls",
            "known_preference_calls",
        )
    }
    known = counts["known_preference_calls"]
    providers = Counter()
    for record in stats:
        providers.update(record["served_by"])
    return {
        **counts,
        "fallback_share": counts["fallback_calls"] / known if known else None,
        "runs_with_fallback": sum(s["any_fallback"] for s in stats),
        "served_by": dict(providers),
    }


def group_experiment(benchmark: dict, audits: list[dict]) -> list[dict]:
    existing, _ = grouped(benchmark)
    indexed = {(a["run_id"], a["variant"]): a for a in audits}
    output = []
    for row in existing:
        ids = {
            s["id"]
            for s in benchmark["registration"]["scenarios"]
            if row["dimension"] == "scenario"
            and s["id"] == row["group"]
            or row["dimension"] == "complexity"
            and s["complexity"] == row["group"]
        }
        runs = [
            r for r in benchmark["rows"] if r["scenario_id"] in ids and r.get("run_id")
        ]
        settled_ids = {r["run_id"] for r in runs if r.get("complete")}
        packages = [p for p in benchmark["packages"] if p["run_id"] in settled_ids]
        exposure_counts = {}
        for stage in ("plan", "original", "retained"):
            # Plan unit is run; Terraform unit is package.
            views = [
                indexed.get((p["run_id"], p["variant"]), {})
                .get(stage, {})
                .get("classification", "unknown")
                for p in packages
            ]
            if stage == "plan":
                views = [
                    benchmark.get("plan_audits", {})
                    .get(r["run_id"], {})
                    .get(
                        "classification",
                        next(
                            (
                                indexed[(p["run_id"], p["variant"])][stage][
                                    "classification"
                                ]
                                for p in packages
                                if p["run_id"] == r["run_id"]
                                and (p["run_id"], p["variant"]) in indexed
                            ),
                            "unknown",
                        ),
                    )
                    for r in runs
                    if r.get("complete")
                ]
            for view in EXPOSURES:
                exposure_counts[stage + "_" + view] = views.count(view)
        blockers = {}
        for rule in RULES:
            values = []
            for package in packages:
                count = package.get("remaining_findings", {}).get(rule, 0)
                if row["profile"] != "strict":
                    assessment = package.get("profile_assessments", {}).get(
                        row["profile"]
                    )
                    if not isinstance(assessment, dict):
                        values = None
                        break
                    count -= sum(
                        e.get("rule_id") == rule for e in assessment.get("excepted", [])
                    )
                values.append(max(0, count))
            blockers[rule + "_findings"] = sum(values) if values is not None else None
            blockers[rule + "_packages"] = (
                sum(v > 0 for v in values) if values is not None else None
            )
        output.append(
            {
                **row,
                **exposure_counts,
                **blockers,
                "provider_routing": combine_routing(
                    [run_statistics(benchmark, r) for r in runs]
                ),
            }
        )
    return output


def pool(baselines: list[dict]) -> dict:
    if any(b["registration"] != baselines[0]["registration"] for b in baselines):
        raise ValueError("Baseline registrations differ")
    rows = [r for b in baselines for r in b["rows"]]
    selections = {
        run: selection
        for b in baselines
        for run, selection in b["environment"]
        .get("resolved_agent_selections", {})
        .items()
    }
    return {
        "folder": "pooled-gpt-oss-broad",
        "environment": {"mode": "real", "resolved_agent_selections": selections},
        "registration": baselines[0]["registration"],
        "rows": rows,
        "packages": [p for b in baselines for p in b["packages"]],
    }


def load_architecture(evidence, benchmark: dict) -> list[dict]:
    result = []
    for package in benchmark["packages"]:
        path = (
            "docs/evals/"
            + benchmark["folder"]
            + "/architecture/"
            + package["run_id"]
            + "/"
            + package["variant"]
            + ".json"
        )
        if path not in evidence.paths:
            continue
        audit = evidence.json(path)
        row = next(r for r in benchmark["rows"] if r.get("run_id") == package["run_id"])
        if (
            any(
                audit.get(k) != row[k]
                for k in ("run_id", "scenario_id", "complexity", "scenario_sha256")
            )
            or audit.get("variant") != package["variant"]
        ):
            raise ValueError("Experiment architecture identity mismatch")
        result.append(audit)
    return result


def check_sibling_selections(baseline: dict, experiment: dict) -> None:
    for role in ROLES[1:]:
        expected = {
            (choice.get("model"), choice.get("thinking_mode"))
            for row in baseline["rows"]
            if row.get("run_id")
            for choice in [run_selections(baseline, row).get(role, {})]
        }
        if len(expected) != 1 or next(iter(expected))[0] is None:
            raise ValueError("Baseline role selections are unknown or inconsistent")
        for row in experiment["rows"]:
            if not row.get("run_id"):
                continue
            choice = run_selections(experiment, row).get(role, {})
            if (choice.get("model"), choice.get("thinking_mode")) not in expected:
                raise ValueError(
                    "Generator/Fixer selection differs; comparison refused"
                )


def load_plans(evidence, benchmark: dict) -> dict:
    result = {}
    for row in benchmark["rows"]:
        if not row.get("run_id"):
            continue
        path = (
            "docs/evals/"
            + benchmark["folder"]
            + "/architecture/"
            + row["run_id"]
            + "/plan.json"
        )
        if path in evidence.paths:
            plan = evidence.json(path)
            if any(
                plan.get(k) != row[k]
                for k in ("run_id", "scenario_id", "complexity", "scenario_sha256")
            ):
                raise ValueError("Experiment plan identity mismatch")
            result[row["run_id"]] = plan
    return result


def append_experiment_report(evidence, folder: str, output: Path) -> None:
    from scripts.phase9b_report import table

    experiment = load_broad(evidence, folder)
    if experiment["environment"]["mode"] != "real" or experiment["environment"].get(
        "broad_smoke"
    ):
        raise ValueError("Experiment comparison requires a real full broad round")
    if not experiment["environment"].get("explicit_architect_model"):
        raise ValueError("Experiment manifest lacks explicit ARCHITECT_MODEL")
    baselines = [load_broad(evidence, f) for f in BASELINE_FOLDERS]
    baseline = pool(baselines)
    if experiment["registration"] != baseline["registration"]:
        raise ValueError("Experiment and baseline registrations differ")
    check_sibling_selections(baseline, experiment)
    audited = evidence.json(BASELINE_AUDIT)
    if audited.get("version") != 1:
        raise ValueError("Unsupported architecture audit")
    # Verify baseline audit bindings again against the committed source revision.
    for source in audited["input_files"]:
        if (
            hashlib.sha256(evidence.read(source["path"])).hexdigest()
            != source["sha256"]
        ):
            raise ValueError("Baseline audit source hash mismatch")
    expected_packages = {(p["run_id"], p["variant"]) for p in baseline["packages"]}
    actual_packages = {(p["run_id"], p["variant"]) for p in audited["packages"]}
    if expected_packages != actual_packages or len(actual_packages) != len(
        audited["packages"]
    ):
        raise ValueError("Baseline audit package identities differ")
    run_rows = {r["run_id"]: r for r in baseline["rows"] if r.get("run_id")}
    for package in audited["packages"]:
        if any(
            package.get(k) != run_rows[package["run_id"]][k]
            for k in ("scenario_id", "complexity")
        ):
            raise ValueError("Baseline audit scenario mismatch")
    baseline["plan_audits"] = {p["run_id"]: p for p in audited.get("plans", [])}
    experiment["plan_audits"] = load_plans(evidence, experiment)
    architecture = audited["packages"] + [
        {"folder": folder, **a} for a in load_architecture(evidence, experiment)
    ]
    groups = group_experiment(baseline, audited["packages"]) + group_experiment(
        experiment, [a for a in architecture if a["folder"] == folder]
    )
    diagnostics, routing = [], []
    for benchmark in [*baselines, experiment]:
        event_path = "docs/evals/" + benchmark["folder"] + "/events.json"
        events = evidence.json(event_path) if event_path in evidence.paths else []
        for row in benchmark["rows"]:
            if not row.get("run_id"):
                continue
            measured = [
                r["seconds"]
                for r in timings(
                    row["run_id"], [e for e in events if e["run_id"] == row["run_id"]]
                )
                if r["agent"] == "architect" and r.get("complete")
            ]
            diagnostics.append(
                {
                    "folder": benchmark["folder"],
                    **architect_diagnostics(row, sum(measured) if measured else None),
                }
            )
            routing.append(
                {
                    "folder": benchmark["folder"],
                    "run_id": row["run_id"],
                    "scenario_id": row["scenario_id"],
                    "complexity": row["complexity"],
                    **run_statistics(benchmark, row),
                }
            )
    config = experiment["environment"]
    lines = [
        "",
        "## Architect-model experiment",
        "",
        (
            "The intended role-selection change is the Architect "
            "model/thinking; Generators and Fixer retain the recorded baseline "
            "models. Prompts are unchanged by Phase 9k. Historical code "
            "revisions, provider preferences, serving-provider fallback and "
            "prompt evolution remain confounders; this comparison does not "
            "isolate a causal model effect."
        ),
        "",
        "Explicit Architect: `"
        + config["explicit_architect_model"]
        + "`; advisory recommendation: `"
        + str(config.get("recommended_architect_model"))
        + "`.",
        "",
        (
            "Plan exposure counts use settled runs; original/retained Terraform "
            "counts use generated packages. Only explicit structured LB "
            "services and statically resolved configured scheme are classified. "
            "Absent is not private; unknowns and plan/code disagreements remain "
            "visible. No network reachability or deployment success is "
            "inferred."
        ),
        "",
        (
            "Per-package audit: experiment-architecture.json. Per-run "
            "reasoning/latency/finish reasons/truncation/timeouts: "
            "architect-diagnostics.json. Historical absent finish reasons "
            "remain unknown. Provider fallback shares exclude unknown serving "
            "providers and calls without an explicit preference; "
            "provider-routing.json retains every denominator."
        ),
        "",
    ]
    for dimension in ("scenario", "complexity"):
        lines += [
            "### " + dimension.capitalize(),
            "",
            table(
                [
                    "Cohort",
                    "Group",
                    "Profile",
                    "Packages",
                    "Valid",
                    "Passed",
                    "Plan public/internal/mixed/absent/unknown",
                    "Retained public/internal/mixed/absent/unknown",
                    "AWS-0053 packages/findings",
                    "CKV_AWS_91 packages/findings",
                    "Fallback/known calls",
                    "Runs with fallback",
                ],
                [
                    [
                        r["benchmark"],
                        r["group"],
                        r["profile"],
                        r["packages"],
                        r["valid"],
                        r["passed"],
                        "/".join(str(r["plan_" + v]) for v in EXPOSURES),
                        "/".join(str(r["retained_" + v]) for v in EXPOSURES),
                        str(r["AWS-0053_packages"]) + "/" + str(r["AWS-0053_findings"]),
                        str(r["CKV_AWS_91_packages"])
                        + "/"
                        + str(r["CKV_AWS_91_findings"]),
                        str(r["provider_routing"]["fallback_calls"])
                        + "/"
                        + str(r["provider_routing"]["known_preference_calls"]),
                        r["provider_routing"]["runs_with_fallback"],
                    ]
                    for r in groups
                    if r["dimension"] == dimension
                ],
            ),
            "",
        ]
    for cohort, folders in [
        ("pooled-gpt-oss-broad", set(BASELINE_FOLDERS)),
        (folder, {folder}),
    ]:
        selected = [d for d in diagnostics if d["folder"] in folders]
        lines += [
            cohort
            + " Architect diagnostics: "
            + json.dumps(
                {
                    "agent_seconds": statistics_for(
                        [
                            d["architect_agent_seconds"]
                            for d in selected
                            if d["architect_agent_seconds"] is not None
                        ]
                    ),
                    "reasoning_tokens": sum(
                        d["reasoning_tokens"]
                        for d in selected
                        if d["reasoning_tokens"] is not None
                    ),
                    "runs_with_unknown_reasoning": sum(
                        d["reasoning_tokens"] is None for d in selected
                    ),
                    "truncated_calls": sum(d["truncated_calls"] for d in selected),
                    "timeout_calls": sum(d["timeout_calls"] for d in selected),
                    "deadline_calls": sum(d["deadline_calls"] for d in selected),
                    "unknown_finish_reasons": sum(
                        d["unknown_finish_reasons"] for d in selected
                    ),
                },
                sort_keys=True,
            ),
            "",
        ]
    with (output / "report.md").open("a") as handle:
        handle.write("\n".join(lines))
    write_json(
        output / "experiment-comparison.json",
        {
            "baseline_folders": BASELINE_FOLDERS,
            "experiment_folder": folder,
            "groups": groups,
            "configuration": {
                "baseline_revisions": [
                    b["environment"].get("git_commit") for b in baselines
                ],
                "experiment_revision": config.get("git_commit"),
                "preflight": config.get("benchmark_preflight"),
                "cost": config.get("experiment_cost"),
            },
        },
    )
    write_json(output / "experiment-architecture.json", architecture)
    write_json(
        output / "experiment-plans.json",
        {"baseline": baseline["plan_audits"], "experiment": experiment["plan_audits"]},
    )
    write_json(output / "architect-diagnostics.json", diagnostics)
    write_json(output / "provider-routing.json", routing)
    write_csv(
        output / "experiment-groups.csv",
        [
            {**r, "provider_routing": json.dumps(r["provider_routing"], sort_keys=True)}
            for r in groups
        ],
    )
    write_csv(
        output / "architect-diagnostics.csv",
        [
            {
                **r,
                "finish_reasons": json.dumps(r["finish_reasons"], sort_keys=True),
                "failure_categories": json.dumps(
                    r["failure_categories"], sort_keys=True
                ),
            }
            for r in diagnostics
        ],
    )
    write_csv(
        output / "provider-routing.csv",
        [
            {
                **r,
                "served_by": json.dumps(r["served_by"], sort_keys=True),
                "by_role": json.dumps(r["by_role"], sort_keys=True),
            }
            for r in routing
        ],
    )
