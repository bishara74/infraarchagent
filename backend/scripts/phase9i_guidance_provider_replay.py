"""Source-free offline Phase 9i follow-up evidence; no operator settings or LLMs."""

import argparse
import asyncio
import hashlib
import json
import socket
from collections import Counter
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.security.generation import generation_context
from app.validation.engine import ValidationEngine
from app.validation.provider_repairs import repair_required_providers
from app.validation.provider_schema import DEFAULT_INDEX
from app.validation.schema_context import _merge, index_for
from app.validation.workspace import ValidationWorkspace
from scripts.phase9i_replay import (
    ROOT,
    Observer,
    ReplayScanner,
    ReplayVerifier,
    aggregate,
    code_manifest,
    digest,
    fingerprints,
    inventory,
)

PROFILES = ("strict", "contextual-v1", "contextual-v2")
BROAD = "phase9-bench-broad-20261020T234203035108Z"
OUTPUT = ROOT / "docs/evals/phase9i-guidance-provider-offline"


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def inputs():
    packages, manifest = inventory()
    for item in packages:
        item["cohort"] = f"final-{item['set']}"
        item["key"] = "final-" + item["key"]
    source = ROOT / "docs/evals" / BROAD / "results.json"
    manifest["sources"].append(
        {
            "path": str(source.relative_to(ROOT)),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    )
    for run in json.loads(source.read_text())["runs"]:
        path = ROOT / ".cache/broad-1-results" / (run["run_id"] + ".json")
        data = json.loads(path.read_text())
        manifest["sources"].append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        manifest["missing_variants"].extend(
            {"set": "broad", "run_id": run["run_id"], "variant": missing["variant"]}
            for missing in data["missing_variants"]
        )
        for package in data["packages"]:
            packages.append(
                {
                    "key": f"broad/{run['run_id']}/{package['variant']}",
                    "cohort": "broad",
                    "scenario_id": run["scenario_id"],
                    "run_id": run["run_id"],
                    "variant": package["variant"],
                    "plan": data["plan"],
                    "package": package,
                }
            )
    manifest["packages"] = [
        {
            "key": p["key"],
            "files_sha256": digest(p["package"]["files"]),
            "plan_sha256": digest(p["plan"]),
        }
        for p in packages
    ]
    return packages, manifest


def required_paths(schema: dict, prefix="", conditional=False):
    result = {"required": set(), "conditional_required": set()}
    tier = "conditional_required" if conditional else "required"
    for name, attr in schema.get("attributes", {}).items():
        if attr.get("required"):
            result[tier].add(prefix + name)
    for name, block in schema.get("block_types", {}).items():
        path = prefix + name
        mandatory = block.get("min_items", 0) > 0
        if mandatory:
            result[tier].add(path)
        nested = required_paths(
            block["block"], path + ".", conditional or not mandatory
        )
        for group in result:
            result[group].update(nested[group])
    return result


def represented_paths(shape: dict, prefix="") -> set[str]:
    result = {prefix + name for name in shape.get("required", {})}
    blocks = shape.get("blocks", {})
    if isinstance(blocks, dict):
        for name, child in blocks.items():
            result.add(prefix + name)
            if isinstance(child, dict):
                result.update(represented_paths(child, prefix + name + "."))
    # Historical depth-limited guidance sometimes lists names without shapes.
    return result


def context_rows(packages, before):
    frozen = {row["plan_sha256"]: row for row in before["contexts"]}
    result = []
    seen = set()
    for item in packages:
        key = (item["cohort"], item["run_id"])
        if key in seen:
            continue
        seen.add(key)
        plan_hash = digest(item["plan"])
        old = frozen[plan_hash]
        context = generation_context(DeploymentPlan.model_validate(item["plan"]))
        old_entries = {entry["type"]: entry for entry in old["schema"]}
        new_entries = {
            entry["type"]: entry
            for entry in json.loads(context.text[: context.schema_chars] or "[]")
        }
        coverage = []
        for name in context.resource_types:
            for version in ("5.100.0", "6.68.0"):
                schema = index_for("aws", version, DEFAULT_INDEX).resource_schema(name)
                if schema is None:
                    continue
                wanted = required_paths(schema)
                absent = {}
                for label, entries in (("before", old_entries), ("after", new_entries)):
                    entry = entries.get(name, {})
                    shape = deepcopy(entry.get("schema", {}))
                    _merge(shape, entry.get("version_schema", {}).get(version, {}))
                    present = represented_paths(shape)
                    absent[label] = {
                        tier: sorted(paths - present) for tier, paths in wanted.items()
                    }
                allowed = {
                    "required": context.omitted_required,
                    "conditional_required": (
                        *context.omitted_required,
                        *context.omitted_conditional,
                    ),
                }
                assert all(
                    not paths or name in allowed[tier]
                    for tier, paths in absent["after"].items()
                ), (key, name, version, absent["after"])
                coverage.append({"type": name, "version": version, "omitted": absent})
        result.append(
            {
                "cohort": item["cohort"],
                "run_id": item["run_id"],
                "plan_sha256": plan_hash,
                "before": {
                    k: old[k]
                    for k in (
                        "schema_chars",
                        "checklist_chars",
                        "total_chars",
                        "truncated",
                    )
                },
                "after": {
                    "schema_chars": context.schema_chars,
                    "checklist_chars": context.checklist_chars,
                    "total_chars": len(context.text),
                    **context.metrics(),
                },
                "required_coverage": coverage,
            }
        )
    return result


def summarize(rows):
    result = {}
    for cohort in ("broad", "final-1", "final-2", "final-combined", "all"):
        selected = [
            r
            for r in rows
            if cohort == "all"
            or r["cohort"] == cohort
            or (cohort == "final-combined" and r["cohort"].startswith("final-"))
        ]
        stages = {
            stage: aggregate([{"observed": r[stage]} for r in selected])
            for stage in ("before", "candidate", "retained")
        }
        stages["outcomes"] = dict(Counter(r["reason"] for r in selected))
        stages["deltas"] = {
            "valid": stages["retained"]["validation"].get("valid", 0)
            - stages["before"]["validation"].get("valid", 0),
            "profiles": {
                p: {
                    k: stages["retained"]["profiles"][p][k]
                    - stages["before"]["profiles"][p][k]
                    for k in ("passes", "blockers")
                }
                for p in PROFILES
            },
        }
        result[cohort] = stages
    return result


def report(output: Path, rows, contexts, manifest):
    summaries = summarize(rows)
    write(output / "summary.json", summaries)
    write(output / "context-sizes-and-coverage.json", contexts)
    write(output / "per-package-deltas.json", rows)
    lines = [
        "# phase9i: schema guidance and provider consolidation offline replay",
        "",
        f"{len(rows)} packages; {len(manifest['missing_variants'])} missing variants "
        "remain separate. Zero LLM calls. Original packages and historical "
        "reports are unchanged.",
        "",
        "| Cohort | Packages | Valid before → retained | Strict passes | "
        "v1 passes | v2 passes | Strict/v1/v2 blocker deltas |",
        "|---|---:|---|---|---|---|---|",
    ]
    for cohort, values in summaries.items():
        old, new = values["before"], values["retained"]
        passes = [
            f"{old['profiles'][p]['passes']} → {new['profiles'][p]['passes']}"
            for p in PROFILES
        ]
        deltas = [str(values["deltas"]["profiles"][p]["blockers"]) for p in PROFILES]
        lines.append(
            f"| {cohort} | {old['packages']} | {old['validation'].get('valid', 0)} "
            f"→ {new['validation'].get('valid', 0)} | "
            + " | ".join(passes)
            + " | "
            + " / ".join(deltas)
            + " |"
        )
    lines.extend(
        [
            "",
            "Guidance alone changes no package bytes and receives zero attributed "
            "validity/security improvement. Deltas compare fresh observations of "
            "original bytes against guarded provider-merge proposals only; "
            "they do not include previous offline repair experiments.",
            "Context-before measurements apply the frozen pre-follow-up budgeter "
            "to saved plans; they are separate from historical inference metadata.",
            "",
            "| Cohort | Schema before → after | Checklist before → after | "
            "Total before → after | Required / conditional overflow plans |",
            "|---|---|---|---|---|",
        ]
    )
    for cohort in ("broad", "final-1", "final-2"):
        selected = [r for r in contexts if r["cohort"] == cohort]
        cells = []
        for component in ("schema_chars", "checklist_chars", "total_chars"):
            ranges = [
                f"{min(r[stage][component] for r in selected)}–"
                f"{max(r[stage][component] for r in selected)}"
                for stage in ("before", "after")
            ]
            cells.append(" → ".join(ranges))
        overflow = [
            sum(
                bool(r["after"]["generator_schema_omitted_resource_types"][tier])
                for r in selected
            )
            for tier in ("required", "conditional_required")
        ]
        lines.append(
            f"| {cohort} | " + " | ".join(cells) + f" | {overflow[0]} / {overflow[1]} |"
        )
    lines.extend(
        [
            "",
            "Previously omitted required items by resource type (union across plans "
            "and provider versions; complete per-plan/version coverage is in "
            "context-sizes-and-coverage.json):",
            "",
            "| Cohort | Resource type | Unconditional previously omitted | "
            "Conditional previously omitted |",
            "|---|---|---|---|",
        ]
    )
    omissions = {}
    for row in contexts:
        for coverage in row["required_coverage"]:
            key = (row["cohort"], coverage["type"])
            target = omissions.setdefault(
                key, {"required": set(), "conditional_required": set()}
            )
            for tier in target:
                target[tier].update(coverage["omitted"]["before"][tier])
    for (cohort, name), tiers in sorted(omissions.items()):
        if any(tiers.values()):
            lines.append(
                f"| {cohort} | {name} | "
                + " | ".join(
                    ", ".join(sorted(tiers[tier])) or "none"
                    for tier in ("required", "conditional_required")
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "Overflow omissions by plan (conditional omissions retain the "
            "complete unconditional core):",
            "",
        ]
    )
    for row in contexts:
        omitted = row["after"]["generator_schema_omitted_resource_types"]
        if any(omitted.values()):
            lines.append(
                f"- {row['cohort']}/{row['run_id']}: "
                f"{json.dumps(omitted, sort_keys=True)}"
            )
    lines.extend(
        ["", "| Cohort | Outcomes | Unknown scans before / retained |", "|---|---|---|"]
    )
    for cohort, values in summaries.items():
        lines.append(
            f"| {cohort} | {values['outcomes']} | "
            f"{values['before']['scan_unknown']} / "
            f"{values['retained']['scan_unknown']} |"
        )
    lines.extend(
        [
            "",
            "Provider-merge proposals (all other packages are unchanged):",
            "",
            "| Package | Guard reason | Failed checks before → candidate | "
            "Candidate diagnostics |",
            "|---|---|---|---|",
            *[
                f"| {r['key']} | {r['reason']} | "
                f"{len(r['before']['failed_checks'])} → "
                f"{len(r['candidate']['failed_checks'])} | "
                + ", ".join(
                    sorted({c["message"] for c in r["candidate"]["failed_checks"]})
                )
                + " |"
                for r in rows
                if r["before_sha256"] != r["candidate_sha256"]
            ],
            "",
            "Consolidation replaces duplicate-declaration diagnostics with other "
            "existing configuration errors. The unchanged guard requires a failed-"
            "check improvement and rejects a Terraform failure-count regression; "
            "neither proposal qualifies. Broad retains two validation-error "
            "packages; there are no unknown scanner outcomes.",
            "",
            "All proposals are idempotent and use the existing checked_one "
            "validity/security guard. Candidate observations, retained hashes, "
            "removed/introduced findings and audit records are preserved per "
            "package. Unknown verification is not a pass. Tool/provider/evaluator "
            "hashes and source hashes bind the replay. Runtime deployment, live "
            "pipeline deadlines and future LLM output quality are unverified.",
            "",
            "The legacy generator_schema_context_chars field is preserved; older "
            "final-set values sometimes include the checklist. "
            "generator_schema_only_context_chars is measured directly from the "
            "schema portion. Historical absence is unknown; no historical value "
            "is rewritten.",
        ]
    )
    (output / "README.md").write_text("\n".join(lines) + "\n")


async def run(args):
    if any(name != "lo" for _, name in socket.if_nameindex()):
        raise ValueError(
            "Replay requires an isolated network namespace containing only loopback"
        )
    packages, manifest = inputs()
    before = json.loads(args.before.read_text())
    for row in before["contexts"]:
        assert (
            hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest()
            == row["sha256"]
        )
    contexts = context_rows(packages, before)
    output = args.output
    if (output / "input-manifest.json").exists():
        assert json.loads((output / "input-manifest.json").read_text()) == manifest
    write(output / "input-manifest.json", manifest)
    write(output / "before-guidance.json", before)
    observer = Observer(args.cache, network_isolated=True)
    evaluator = {
        **code_manifest(),
        **{
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "backend/app/agents/deterministic.py", Path(__file__))
        },
    }
    provenance = {
        "evaluator": evaluator,
        "tool_versions": observer.versions,
        "scanner_versions": observer.scanner_versions,
        "provider_manifest_sha256": observer.provider_manifest,
        "network_isolated": True,
        "llm_calls": 0,
        "tool_timeout": 60,
        "validation_deadline": 120,
    }
    write(output / "execution-manifest.json", provenance)
    semaphore = asyncio.Semaphore(args.workers)
    completed = 0

    async def process(item):
        nonlocal completed
        async with semaphore:
            workspace = ValidationWorkspace()
            try:
                with workspace.activate():
                    files = item["package"]["files"]
                    candidate, proposed = repair_required_providers(files)
                    repeated, _ = repair_required_providers(candidate)
                    assert candidate == repeated, item["key"]
                    old = await observer.observe(item, files)
                    candidate_observed = (
                        await observer.observe(item, candidate)
                        if candidate != files
                        else old
                    )
                    baseline = (
                        await ValidationEngine().validate(
                            DeploymentPlan.model_validate(item["plan"]), files
                        )
                        if candidate != files
                        else None
                    )
                    records = proposed
                    retained, final = files, old
                    reason = "unchanged"
                    if candidate != files:
                        # Run the production wrapper against real observations;
                        # the engine uses the same local validator as the baseline.
                        retained, _, records = await checked_one(
                            files,
                            DeploymentPlan.model_validate(item["plan"]),
                            Variant(item["variant"]),
                            baseline,
                            ValidationEngine(),
                            SimpleNamespace(
                                terraform_verifier=ReplayVerifier(observer, item),
                                scanner=ReplayScanner(observer, item),
                            ),
                            AgentBudget(120),
                            repair_required_providers,
                        )
                        reason = next(
                            (
                                r.get("reason")
                                for r in records
                                if r.get("outcome") != "skipped"
                            ),
                            "unchanged",
                        )
                        final = candidate_observed if retained == candidate else old
                    row = {
                        "key": item["key"],
                        "cohort": item["cohort"],
                        "scenario_id": item.get("scenario_id"),
                        "before": old,
                        "candidate": candidate_observed,
                        "retained": final,
                        "reason": reason,
                        "records": records,
                        "before_sha256": digest(files),
                        "candidate_sha256": digest(candidate),
                        "retained_sha256": digest(retained),
                        "removed_candidate_findings": sorted(
                            fingerprints(old) - fingerprints(candidate_observed)
                        ),
                        "introduced_candidate_findings": sorted(
                            fingerprints(candidate_observed) - fingerprints(old)
                        ),
                        "evaluator_sha256": digest(evaluator),
                    }
                    write(
                        output / "packages" / (item["key"].replace("/", "-") + ".json"),
                        row,
                    )
            finally:
                workspace.close()
            completed += 1
            print(
                f"replay {completed}/{len(packages)} {item['key']} {reason}", flush=True
            )
            return row

    rows = await asyncio.gather(*(process(item) for item in packages))
    assert evaluator == {
        **code_manifest(),
        **{
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "backend/app/agents/deterministic.py", Path(__file__))
        },
    }, "Evaluator changed during replay"
    report(output, rows, contexts, manifest)
    print(json.dumps(summarize(rows)), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, default=OUTPUT / "before-guidance.json")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument(
        "--cache",
        type=Path,
        default=ROOT / ".cache/phase9i-guidance-provider-observations",
    )
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
