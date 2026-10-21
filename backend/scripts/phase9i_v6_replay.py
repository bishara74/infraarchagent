"""Offline AWS v6 migration observations; four frozen cohorts, no inference."""

import argparse
import asyncio
import hashlib
import json
import socket
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.security.generation import generation_context
from app.security.terraform import TerraformPackage, objects
from app.validation.documents import blocks
from app.validation.engine import ValidationEngine
from app.validation.provider_schema import ProviderSchemaIndex
from app.validation.v6_equivalents import repair_v6_equivalents
from app.validation.workspace import ValidationWorkspace
from scripts.phase9i_guidance_provider_replay import inputs as earlier_inputs
from scripts.phase9i_replay import (
    ROOT,
    SETS,
    Observer,
    ReplayScanner,
    ReplayVerifier,
    aggregate,
    code_manifest,
    digest,
    fingerprints,
    projection,
)

BROAD2 = "phase9-bench-broad-20261021T200436165739Z"
COHORTS = ("broad-1", "broad-2", "final-1", "final-2")
PROFILES = ("strict", "contextual-v1", "contextual-v2")
GUIDE = "https://github.com/hashicorp/terraform-provider-aws/blob/v6.68.0/website/docs/guides/version-6-upgrade.html.markdown"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def final_scenario(run):
    # PR-03 uses the registered ECS workload; no text-based matching.
    index = 0 if run["measurement"] == "pr03" else run["prompt_index"]
    return f"final-{index}"


def inputs():
    items, manifest = earlier_inputs()
    final_runs = {}
    for number, name in enumerate(SETS, 1):
        for run in json.loads(
            (ROOT / "docs/evals" / name / "results.json").read_text()
        )["runs"]:
            final_runs[(f"final-{number}", run["run_id"])] = final_scenario(run)
    for item in items:
        if item["cohort"] == "broad":
            item["cohort"] = "broad-1"
            item["key"] = item["key"].replace("broad/", "broad-1/", 1)
        else:
            item["scenario_id"] = final_runs[(item["cohort"], item["run_id"])]
    source = ROOT / "docs/evals" / BROAD2 / "results.json"
    manifest["sources"].append(
        {
            "path": str(source.relative_to(ROOT)),
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    )
    for run in json.loads(source.read_text())["runs"]:
        path = ROOT / ".cache/broad-2-results" / (run["run_id"] + ".json")
        data = json.loads(path.read_text())
        manifest["sources"].append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
        for missing in data["missing_variants"]:
            manifest["missing_variants"].append(
                {
                    "set": "broad-2",
                    "run_id": run["run_id"],
                    "variant": missing["variant"],
                }
            )
        for package in data["packages"]:
            items.append(
                {
                    "key": f"broad-2/{run['run_id']}/{package['variant']}",
                    "cohort": "broad-2",
                    "run_id": run["run_id"],
                    "scenario_id": run["scenario_id"],
                    "variant": package["variant"],
                    "plan": data["plan"],
                    "package": package,
                }
            )
    manifest["packages"] = [
        {
            "key": i["key"],
            "scenario_id": i["scenario_id"],
            "files_sha256": digest(i["package"]["files"]),
            "plan_sha256": digest(i["plan"]),
        }
        for i in items
    ]
    return items, manifest


def removed_fields(body, old, new, prefix=""):
    for name, value in body.items():
        previous, current = old.get("attributes", {}), new.get("attributes", {})
        if name in previous and name not in current:
            if previous[name].get("optional") or previous[name].get("required"):
                yield prefix + name, "argument"
        previous, current = old.get("block_types", {}), new.get("block_types", {})
        if name in previous:
            if name not in current:
                yield prefix + name, "block"
            else:
                for child in objects(value):
                    yield from removed_fields(
                        child,
                        previous[name]["block"],
                        current[name]["block"],
                        prefix + name + ".",
                    )
        elif name == "dynamic":
            for dynamic in objects(value):
                for block_name, content in dynamic.items():
                    if block_name in previous and block_name not in current:
                        yield prefix + block_name, "dynamic_block"
                    elif block_name in previous and block_name in current:
                        for child in objects(content.get("content", [])):
                            yield from removed_fields(
                                child,
                                previous[block_name]["block"],
                                current[block_name]["block"],
                                prefix + block_name + ".",
                            )


def configuration_blocks(data, kind):
    declared = blocks(data, kind)
    if kind == "data":
        return [
            ((*labels, name), body)
            for labels, group in declared
            for name, body in group.items()
            if isinstance(body, dict)
        ]
    return declared


def inventory(items):
    indexes = {v: ProviderSchemaIndex("aws", v) for v in ("5.100.0", "6.68.0")}
    assert all(i.available for i in indexes.values())
    rows, modules, uninspectable = [], [], []
    for item in items:
        if item["cohort"] != "broad-2":
            continue
        for stage in ("files", "original_files"):
            package = TerraformPackage(item["package"][stage])
            for module in sorted(
                {str(Path(d.path).parent) for d in package.documents.documents.values()}
            ):
                modules.append(
                    {
                        "key": item["key"],
                        "stage": stage,
                        "module": module,
                        "safe": package.module_safe(module),
                        "resolved_aws": package.version(module),
                    }
                )
            for doc in package.documents.documents.values():
                module = str(Path(doc.path).parent)
                if doc.parse_error or not (package.version(module) or "").startswith(
                    "6."
                ):
                    continue
                for kind in ("resource", "data"):
                    for labels, body in configuration_blocks(doc.data, kind):
                        if len(labels) != 2:
                            uninspectable.append(
                                {
                                    "key": item["key"],
                                    "stage": stage,
                                    "file": doc.path,
                                    "kind": kind,
                                    "reason": "invalid_declaration_labels",
                                }
                            )
                            continue
                        typ, name = labels
                        old = indexes["5.100.0"].resource_schema(
                            typ, data_source=kind == "data"
                        )
                        new = indexes["6.68.0"].resource_schema(
                            typ, data_source=kind == "data"
                        )
                        if old and new:
                            for field, field_kind in removed_fields(body, old, new):
                                rows.append(
                                    {
                                        "key": item["key"],
                                        "scenario_id": item["scenario_id"],
                                        "stage": stage,
                                        "file": doc.path,
                                        "kind": kind,
                                        "type": typ,
                                        "resource": name,
                                        "field": field,
                                        "field_kind": field_kind,
                                        "resolved_aws": package.version(module),
                                    }
                                )
    return {
        "scope": (
            "All parsed resource/data configuration arguments and nested "
            "blocks; original and retained round-2 bytes. Computed-only "
            "references and removed resource types are not argument "
            "migrations."
        ),
        "modules": modules,
        "uninspectable": uninspectable,
        "occurrences": rows,
        "counts": dict(Counter(f"{r['stage']}:{r['type']}.{r['field']}" for r in rows)),
        "documented_equivalents": [
            {
                "field": "aws_eip.vpc",
                "replacement": 'domain = "vpc" only for literal true',
                "guide": GUIDE + "#resource-aws_eip",
            },
            {
                "field": "aws_ssm_association.instance_id",
                "replacement": (
                    "targets with key InstanceIds and one preserved expression; "
                    "existing targets/dynamic skip"
                ),
                "guide": GUIDE + "#resource-aws_ssm_association",
                "example": "https://github.com/hashicorp/terraform-provider-aws/blob/v6.68.0/website/docs/r/ssm_association.html.markdown",
            },
            {
                "field": "aws_flow_log.log_group_name",
                "replacement": (
                    "log_destination using the same uniquely bound CloudWatch group "
                    "ARN; unbound names skip"
                ),
                "guide": GUIDE + "#resource-aws_flow_log",
                "semantics": "https://registry.terraform.io/providers/hashicorp/aws/5.0.1/docs/resources/flow_log#argument-reference",
            },
        ],
    }


class MigrationObserver(Observer):
    """Reuse immutable baselines explicitly; native checks for every changed byte."""

    def __init__(self, cache, items):
        super().__init__(cache, network_isolated=True)
        previous = ROOT / "docs/evals/phase9i-guidance-provider-offline"
        execution = json.loads((previous / "execution-manifest.json").read_text())
        assert execution["tool_versions"] == self.versions
        assert execution["scanner_versions"] == self.scanner_versions
        assert execution["provider_manifest_sha256"] == self.provider_manifest
        # Proposal/guidance code and the repair-kind enum changed; observational
        # validator, scanner, binding and policy implementations did not.
        excluded = {
            "backend/app/validation/equivalents.py",
            "backend/app/security/generation.py",
            "backend/app/domain/validation.py",
        }
        self.unchanged_sources = {}
        for path, expected in execution["evaluator"].items():
            if path in excluded:
                continue
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, (
                path
            )
            self.unchanged_sources[path] = expected
        self.previous_path = previous / "per-package-deltas.json"
        old_rows = {}
        for row in json.loads(self.previous_path.read_text()):
            key = row["key"].replace("broad/", "broad-1/", 1)
            old_rows[key] = row
        self.frozen = {}
        self.fresh_keys = set()
        for item in items:
            files = item["package"]["files"]
            candidate, _ = repair_v6_equivalents(files)
            if candidate != files:
                self.fresh_keys.add(item["key"])
            elif item["key"] in old_rows:
                row = old_rows[item["key"]]
                assert row["before_sha256"] == digest(files)
                self.frozen[item["key"]] = ("prior_native_offline", row["before"])
            else:
                assert item["cohort"] == "broad-2"
                assert (
                    item["package"]["validation_report"]["tool_versions"]
                    == self.versions
                )
                self.frozen[item["key"]] = (
                    "stored_round2_immutable",
                    projection(item["package"]),
                )
        # Scanner versions for the historical round-2 observations are recorded
        # with the benchmark rather than each package's validation tool map.
        env = json.loads(
            (ROOT / "docs/evals" / BROAD2 / "environment.json").read_text()
        )
        for tool, value in self.scanner_versions.items():
            assert env["tools"][tool] == value["version"], tool

    async def observe(self, item, files):
        if item["key"] not in self.fresh_keys:
            assert files == item["package"]["files"]
            return self.frozen[item["key"]][1]
        return await super().observe(item, files)

    def method(self, item):
        return (
            "fresh_native_pair"
            if item["key"] in self.fresh_keys
            else self.frozen[item["key"]][0]
        )


def summarize(rows):
    stages = {
        s: aggregate([{"observed": r[s]} for r in rows])
        for s in ("before", "candidate", "retained")
    }
    stages["outcomes"] = dict(Counter(r["reason"] for r in rows))
    old, new = stages["before"], stages["retained"]
    stages["deltas"] = {
        "valid": new["validation"].get("valid", 0) - old["validation"].get("valid", 0),
        "profiles": {
            p: {
                k: new["profiles"][p][k] - old["profiles"][p][k]
                for k in ("passes", "blockers")
            }
            for p in PROFILES
        },
    }
    return stages


def report(output, rows):
    cohorts = {c: summarize([r for r in rows if r["cohort"] == c]) for c in COHORTS}
    scenarios = [
        {
            "cohort": c,
            "scenario_id": scenario,
            **summarize(
                [r for r in rows if r["cohort"] == c and r["scenario_id"] == scenario]
            ),
        }
        for c in COHORTS
        for scenario in sorted({r["scenario_id"] for r in rows if r["cohort"] == c})
    ]
    write(output / "summary.json", {"cohorts": cohorts, "all": summarize(rows)})
    write(output / "per-scenario-deltas.json", scenarios)
    write(output / "per-package-deltas.json", rows)
    lines = [
        "# phase9i: documented AWS v6 migrations — offline replay",
        "",
        f"{len(rows)} immutable stored final packages: 60 broad-1, 60 broad-2 "
        "and 81 final-set packages. Three missing final variants remain separate. "
        "No inference, deployment or new benchmark.",
        "",
        (
            "Changed proposals receive paired native validation and scans. "
            "Unchanged packages reuse hash-verified frozen observations with "
            "matching tools and unchanged validator/scanner/policy sources. "
            "Byte-identical packages have identity deltas. "
            "The recorded baseline_method identifies each source. "
            "Before/candidate/retained observations use validators and "
            "strict scanners offline. Only the new v6 equivalents are "
            "proposed; unrelated existing repairs and provider merging are "
            "not rerun. Guidance changes alter no replayed IaC bytes and "
            "receive no attributed validity/security gain."
        ),
        "",
        (
            "| Cohort / scenario | Packages | Valid before → retained (delta) "
            "| Strict passes | v1 passes | v2 passes | Strict / v1 / v2 "
            "blocker deltas |"
        ),
        "|---|---:|---|---|---|---|---|",
    ]
    for row in [
        *({"cohort": c, "scenario_id": "all", **v} for c, v in cohorts.items()),
        *scenarios,
    ]:
        old, new = row["before"], row["retained"]
        passes = [
            f"{old['profiles'][p]['passes']} → {new['profiles'][p]['passes']} "
            f"({row['deltas']['profiles'][p]['passes']:+})"
            for p in PROFILES
        ]
        deltas = " / ".join(
            f"{row['deltas']['profiles'][p]['blockers']:+}" for p in PROFILES
        )
        lines.append(
            f"| {row['cohort']} / {row['scenario_id']} | {old['packages']} | "
            f"{old['validation'].get('valid', 0)} → "
            f"{new['validation'].get('valid', 0)} ({row['deltas']['valid']:+}) | "
            + " | ".join(passes)
            + f" | {deltas} |"
        )
    lines += [
        "",
        (
            "Broad scenario IDs retain their pre-registration meaning. Final "
            "scenario IDs use existing prompt_index metadata: final-0 ECS "
            "application (including registered PR-03), final-1 EKS "
            "microservices, final-2 static site. No prompt-text matching or "
            "cross-scenario pooling."
        ),
        "",
        (
            "| Changed proposal | Guard outcome | Failed checks before → "
            "candidate | Retained valid |"
        ),
        "|---|---|---|---|",
    ]
    for r in rows:
        if r["before_sha256"] != r["candidate_sha256"]:
            lines.append(
                f"| {r['key']} | {r['reason']} | "
                f"{len(r['before']['failed_checks'])} → "
                f"{len(r['candidate']['failed_checks'])} | "
                f"{r['retained']['validation']} |"
            )
    lines += [
        "",
        (
            "[Migration inventory](migration-inventory.json) includes "
            "original generator bytes as a separate audit only. [Per-package "
            "evidence](per-package-deltas.json) records candidate/retained "
            "hashes, guard records, blocker changes and unknown observations. "
            "Inputs and evaluator/tool/provider hashes are bound in the "
            "manifests. Unknown/error observations never count as passes."
        ),
        "",
        (
            "Provider major-version drift is a discussion finding: a "
            "generator can choose a valid v6 constraint while emitting "
            "removed v5 syntax. This replay measures narrow migration effects "
            "on saved bytes; it does not isolate prompt/guidance causation or "
            "establish live deadline/deployment success. Fixed generation "
            "caps, recursive tiers, strict acceptance, readiness and "
            "thresholds remain unchanged."
        ),
    ]
    (output / "README.md").write_text("\n".join(lines) + "\n")


async def run(args):
    if any(name != "lo" for _, name in socket.if_nameindex()):
        raise ValueError("Replay requires a loopback-only network namespace")
    items, manifest = inputs()
    write(args.output / "input-manifest.json", manifest)
    write(args.output / "migration-inventory.json", inventory(items))
    contexts = []
    seen = set()
    for item in items:
        key = (item["cohort"], item["run_id"])
        if key in seen:
            continue
        seen.add(key)
        context = generation_context(DeploymentPlan.model_validate(item["plan"]))
        assert (
            context.schema_chars <= 4500
            and context.checklist_chars <= 1500
            and len(context.text) <= 6000
        )
        contexts.append(
            {
                "cohort": item["cohort"],
                "run_id": item["run_id"],
                "schema_chars": context.schema_chars,
                "checklist_chars": context.checklist_chars,
                "total_chars": len(context.text),
                "resource_types": context.resource_types,
                **context.metrics(),
            }
        )
    write(args.output / "contexts.json", contexts)
    evaluator = {
        **code_manifest(),
        **{
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                Path(__file__),
                ROOT / "backend/scripts/phase9i_replay.py",
                ROOT / "backend/scripts/phase9i_guidance_provider_replay.py",
                ROOT / "backend/app/agents/deterministic.py",
                ROOT / "backend/app/domain/plan.py",
                ROOT / "backend/app/agents/prompts/architect.py",
            )
        },
    }
    observer = MigrationObserver(args.cache, items)
    write(
        args.output / "execution-manifest.json",
        {
            "evaluator": evaluator,
            "evaluator_sha256": digest(evaluator),
            "tool_versions": observer.versions,
            "scanner_versions": observer.scanner_versions,
            "provider_manifest_sha256": observer.provider_manifest,
            "network_isolated": True,
            "llm_calls": 0,
            "tool_timeout": 60,
            "validation_deadline": 120,
            "fresh_changed_packages": sorted(observer.fresh_keys),
            "unchanged_observation_sources": observer.unchanged_sources,
            "prior_native_baseline": str(observer.previous_path.relative_to(ROOT)),
            "prior_native_baseline_sha256": hashlib.sha256(
                observer.previous_path.read_bytes()
            ).hexdigest(),
            "baseline_methods": dict(Counter(observer.method(i) for i in items)),
        },
    )
    semaphore = asyncio.Semaphore(args.workers)
    completed = 0

    async def process(item):
        nonlocal completed
        async with semaphore:
            workspace = ValidationWorkspace()
            try:
                with workspace.activate():
                    files = item["package"]["files"]
                    old = await observer.observe(item, files)
                    candidate, records = repair_v6_equivalents(files)
                    assert repair_v6_equivalents(candidate) == (candidate, []), item[
                        "key"
                    ]
                    proposed = (
                        await observer.observe(item, candidate)
                        if candidate != files
                        else old
                    )
                    retained, final, reason = files, old, "unchanged"
                    if candidate != files:
                        engine = ValidationEngine()
                        baseline = await engine.validate(
                            DeploymentPlan.model_validate(item["plan"]), files
                        )
                        retained, _, records = await checked_one(
                            files,
                            DeploymentPlan.model_validate(item["plan"]),
                            Variant(item["variant"]),
                            baseline,
                            engine,
                            SimpleNamespace(
                                terraform_verifier=ReplayVerifier(observer, item),
                                scanner=ReplayScanner(observer, item),
                            ),
                            AgentBudget(120),
                            repair_v6_equivalents,
                        )
                        reason = next(
                            (
                                r.get("reason")
                                for r in records
                                if r.get("outcome") != "skipped"
                            ),
                            "unchanged",
                        )
                        final = proposed if retained == candidate else old
                    row = {
                        "key": item["key"],
                        "cohort": item["cohort"],
                        "scenario_id": item["scenario_id"],
                        "before": old,
                        "candidate": proposed,
                        "retained": final,
                        "stored": projection(item["package"]),
                        "baseline_method": observer.method(item),
                        "reason": reason,
                        "records": records,
                        "before_sha256": digest(files),
                        "candidate_sha256": digest(candidate),
                        "retained_sha256": digest(retained),
                        "removed_candidate_findings": sorted(
                            fingerprints(old) - fingerprints(proposed)
                        ),
                        "introduced_candidate_findings": sorted(
                            fingerprints(proposed) - fingerprints(old)
                        ),
                        "evaluator_sha256": digest(evaluator),
                    }
                    write(
                        args.output
                        / "packages"
                        / (item["key"].replace("/", "-") + ".json"),
                        row,
                    )
            finally:
                workspace.close()
            completed += 1
            print(f"replay {completed}/{len(items)} {item['key']} {reason}", flush=True)
            return row

    rows = await asyncio.gather(*(process(i) for i in items))
    for p, h in evaluator.items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h, (
            "Evaluator changed"
        )
    for source in manifest["sources"]:
        assert (
            hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest()
            == source["sha256"]
        ), "Input changed"
    report(args.output, rows)
    print(
        json.dumps(
            {
                c: summarize([r for r in rows if r["cohort"] == c])["deltas"]
                for c in COHORTS
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/evals/phase9i-v6-migrations-offline"
    )
    parser.add_argument(
        "--cache", type=Path, default=ROOT / ".cache/phase9i-v6-observations"
    )
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
