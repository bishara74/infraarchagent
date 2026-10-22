"""Offline path-only deltas over the immutable v6-retained 201-package cohort."""

import argparse
import ast
import asyncio
import hashlib
import json
import socket
import subprocess
from pathlib import Path
from types import SimpleNamespace

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.validation.engine import ValidationEngine
from app.validation.file_paths import repair_file_paths
from app.validation.v6_equivalents import repair_v6_equivalents
from app.validation.workspace import ValidationWorkspace
from scripts.phase9i_replay import (
    ROOT,
    Observer,
    ReplayScanner,
    ReplayVerifier,
    code_manifest,
    digest,
    fingerprints,
    projection,
)
from scripts.phase9i_v6_replay import COHORTS, PROFILES, inputs, summarize, write

PREVIOUS = ROOT / "docs/evals/phase9i-v6-migrations-offline"
PINNED = "4efd4dd"


def retained_files(item, previous):
    """Reconstruct only hash-proven prior retained bytes, without live rules."""
    files = item["package"]["files"]
    assert digest(files) == previous["before_sha256"]
    if previous["retained_sha256"] == digest(files):
        return files
    candidate, _ = repair_v6_equivalents(files)
    assert previous["reason"] == "improved"
    assert digest(candidate) == previous["candidate_sha256"]
    assert digest(candidate) == previous["retained_sha256"]
    return candidate


def observational_model_ast(source):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "DeterministicRepair":
            for child in node.body:
                if (
                    isinstance(child, ast.AnnAssign)
                    and isinstance(child.target, ast.Name)
                    and child.target.id == "kind"
                    and isinstance(child.annotation, ast.Subscript)
                    and isinstance(child.annotation.slice, ast.Tuple)
                ):
                    child.annotation.slice.elts = [
                        value
                        for value in child.annotation.slice.elts
                        if not (
                            isinstance(value, ast.Constant)
                            and value.value == "terraform_file_path"
                        )
                    ]
    return ast.dump(tree, include_attributes=False)


class PathObserver(Observer):
    def __init__(self, cache, items, previous_rows, baselines, execution):
        super().__init__(cache, network_isolated=True)
        assert execution["tool_versions"] == self.versions
        assert execution["scanner_versions"] == self.scanner_versions
        assert execution["provider_manifest_sha256"] == self.provider_manifest
        excluded = {
            "backend/app/validation/equivalents.py",
            "backend/app/domain/validation.py",
        }
        self.unchanged_sources = {}
        for path, expected in execution["evaluator"].items():
            if path not in excluded:
                assert (
                    hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
                ), path
                self.unchanged_sources[path] = expected
        model_path = "backend/app/domain/validation.py"
        old_model = subprocess.check_output(
            ["git", "show", PINNED + ":" + model_path], cwd=ROOT
        )
        assert (
            hashlib.sha256(old_model).hexdigest() == execution["evaluator"][model_path]
        )
        assert observational_model_ast(old_model.decode()) == observational_model_ast(
            (ROOT / model_path).read_text()
        )
        self.baselines, self.previous_rows = baselines, previous_rows
        self.fresh_keys = {
            i["key"]
            for i in items
            if repair_file_paths(baselines[i["key"]])[0] != baselines[i["key"]]
        }

    async def observe(self, item, files):
        if item["key"] not in self.fresh_keys:
            assert files == self.baselines[item["key"]]
            return self.previous_rows[item["key"]]["retained"]
        return await super().observe(item, files)


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
        "# phase9i: literal file-path rebasing — offline replay",
        "",
        f"{len(rows)} saved packages: 60 broad-1, 60 broad-2, 40 final-1 and "
        "41 final-2. Three missing final variants remain separate. Baseline "
        "is the committed v6-retained replay, not original generator output. "
        "No inference, deployment or new real benchmark.",
        "",
        "Every path proposal receives paired native validation and scans, "
        "then the existing checked_one/CandidateGuard decides retention. "
        "Byte-identical packages reuse hash-verified prior retained observations "
        "with matching tool/provider versions and unchanged observational "
        "sources. Each row states its baseline method. Only file-path "
        "proposals run; other repairs and provider consolidation are not rerun.",
        "",
        "| Cohort / scenario | Packages | Valid before → retained (delta) | "
        "Strict passes | v1 passes | v2 passes | Strict / v1 / v2 blocker deltas |",
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
        blockers = " / ".join(
            f"{row['deltas']['profiles'][p]['blockers']:+}" for p in PROFILES
        )
        lines.append(
            f"| {row['cohort']} / {row['scenario_id']} | {old['packages']} | "
            f"{old['validation'].get('valid', 0)} → "
            f"{new['validation'].get('valid', 0)} ({row['deltas']['valid']:+}) | "
            + " | ".join(passes)
            + f" | {blockers} |"
        )
    lines.extend(
        [
            "",
            "Broad scenario IDs keep their registered meaning. Final scenario "
            "IDs come from existing metadata: final-0 ECS (including PR-03), "
            "final-1 EKS, final-2 static site. No prompt-text matching.",
            "",
            "| Path proposal | Guard outcome | Failed checks before → candidate | "
            "Retained validity |",
            "|---|---|---|---|",
        ]
    )
    for row in rows:
        if row["before_sha256"] != row["candidate_sha256"]:
            lines.append(
                f"| {row['key']} | {row['reason']} | "
                f"{len(row['before']['failed_checks'])} → "
                f"{len(row['candidate']['failed_checks'])} | "
                f"{row['retained']['validation']} |"
            )
    lines.extend(
        [
            "",
            "A literal canonical file() argument is rebased only when the "
            "module-relative target is absent, the exact package-root artifact "
            "exists and the replacement remains inside the package. An existing "
            "root-working-directory target is also authoritative for child "
            "modules. No basename search, file creation, host filesystem reads "
            "or artifact-content changes. Dynamic, escaping, missing or "
            "ambiguous inputs skip. Existing valid paths remain unchanged.",
            "",
            "Semantics: [file()](https://developer.hashicorp.com/terraform/"
            "language/functions/file), "
            "[path.module](https://developer.hashicorp.com/terraform/language/"
            "expressions/references#filesystem-and-workspace-info). "
            "The expression still returns a string; pinned schemas and native "
            "validation remain authoritative. "
            "[Per-package evidence](per-package-deltas.json) "
            "records before/candidate/retained hashes, guard records and findings. "
            "Manifests bind all 201 inputs, prior evidence and evaluator sources. "
            "Unknown/error observations never count as passes.",
            "",
            "These are offline effects on saved bytes. Static validity does not "
            "prove deployment success. SSM commands coercion, prompts, guidance "
            "caps/tiers, readiness, blocking and thresholds are unchanged.",
        ]
    )
    (output / "README.md").write_text("\n".join(lines) + "\n")


async def run(args):
    if any(name != "lo" for _, name in socket.if_nameindex()):
        raise ValueError("Replay requires a loopback-only network namespace")
    items, manifest = inputs()
    assert manifest == json.loads((PREVIOUS / "input-manifest.json").read_text())
    previous_path = PREVIOUS / "per-package-deltas.json"
    previous_rows = {r["key"]: r for r in json.loads(previous_path.read_text())}
    assert set(previous_rows) == {i["key"] for i in items}
    baselines = {i["key"]: retained_files(i, previous_rows[i["key"]]) for i in items}
    previous_execution = json.loads((PREVIOUS / "execution-manifest.json").read_text())
    assert all(
        r["evaluator_sha256"] == previous_execution["evaluator_sha256"]
        for r in previous_rows.values()
    )
    evaluator = {
        **code_manifest(),
        **{
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                Path(__file__),
                ROOT / "backend/scripts/phase9i_replay.py",
                ROOT / "backend/scripts/phase9i_v6_replay.py",
                ROOT / "backend/scripts/phase9i_guidance_provider_replay.py",
                ROOT / "backend/app/agents/deterministic.py",
            )
        },
    }
    observer = PathObserver(
        args.cache, items, previous_rows, baselines, previous_execution
    )
    write(args.output / "input-manifest.json", manifest)
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
            "model_proof": (
                "Git-pinned model AST identical except additive "
                "terraform_file_path kind"
            ),
            "baseline_commit": PINNED,
            "baseline_methods": {
                "fresh_native_pair": len(observer.fresh_keys),
                "prior_v6_retained_immutable": len(items) - len(observer.fresh_keys),
            },
            "prior_evidence": {
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (
                    previous_path,
                    PREVIOUS / "execution-manifest.json",
                    PREVIOUS / "input-manifest.json",
                )
            },
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
                    files = baselines[item["key"]]
                    old = await observer.observe(item, files)
                    candidate, records = repair_file_paths(files)
                    assert repair_file_paths(candidate) == (candidate, []), item["key"]
                    proposed = (
                        await observer.observe(item, candidate)
                        if candidate != files
                        else old
                    )
                    retained, final, reason = files, old, "unchanged"
                    if candidate != files:
                        engine = ValidationEngine()
                        plan = DeploymentPlan.model_validate(item["plan"])
                        baseline = await engine.validate(plan, files)
                        retained, _, records = await checked_one(
                            files,
                            plan,
                            Variant(item["variant"]),
                            baseline,
                            engine,
                            SimpleNamespace(
                                terraform_verifier=ReplayVerifier(observer, item),
                                scanner=ReplayScanner(observer, item),
                            ),
                            AgentBudget(120),
                            repair_file_paths,
                        )
                        reason = next(r["reason"] for r in records)
                        final = proposed if retained == candidate else old
                    row = {
                        "key": item["key"],
                        "cohort": item["cohort"],
                        "scenario_id": item["scenario_id"],
                        "before": old,
                        "candidate": proposed,
                        "retained": final,
                        "stored": projection(item["package"]),
                        "baseline_method": (
                            "fresh_native_pair"
                            if item["key"] in observer.fresh_keys
                            else "prior_v6_retained_immutable"
                        ),
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
            finally:
                workspace.close()
            completed += 1
            print(f"replay {completed}/{len(items)} {item['key']} {reason}", flush=True)
            return row

    rows = await asyncio.gather(*(process(item) for item in items))
    for p, expected in evaluator.items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == expected, p
    for source in manifest["sources"]:
        assert (
            hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest()
            == source["sha256"]
        )
    report(args.output, rows)
    print(
        json.dumps(
            {
                c: v["deltas"]
                for c, v in json.loads((args.output / "summary.json").read_text())[
                    "cohorts"
                ].items()
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/evals/phase9i-file-paths-offline"
    )
    parser.add_argument(
        "--cache", type=Path, default=ROOT / ".cache/phase9i-file-path-observations"
    )
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
