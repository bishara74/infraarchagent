"""Actual offline follow-up replay, immutable inputs and pinned historical bytes."""

import argparse
import asyncio
import hashlib
import json
import socket
import subprocess
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.agents.budget import AgentBudget
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.scanners.runner import ProcessToolRunner, ToolFailure
from app.scanners.scan import Scanner
from app.security.acceptance import CandidateGuard
from app.security.kubernetes_render import repair_formats_and_pods, repair_kubernetes
from app.security.profiles import assess
from app.validation.engine import ValidationEngine
from app.validation.workspace import ValidationWorkspace
from scripts.phase9i_replay import (
    EVIDENCE as OLD_EVIDENCE,
)
from scripts.phase9i_replay import (
    ROOT,
    Observer,
    ReplayScanner,
    ReplayVerifier,
    code_manifest,
    digest,
    fingerprints,
    inventory,
    projection,
    replay_change,
)
from scripts.phase9i_report import compare, prompt_labels, proposal

PROFILES = ("strict", "contextual-v1", "contextual-v2")
PINNED = "c3be20c"
EVIDENCE = ROOT / "docs/evals/phase9i-kubernetes-offline"


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


@lru_cache(maxsize=1)
def pinned_equivalents():
    """Trusted repository source preserves the historical rule set as it evolves."""
    path = "backend/app/validation/equivalents.py"
    source = subprocess.check_output(["git", "show", PINNED + ":" + path], cwd=ROOT)
    namespace: dict[str, Any] = {"__name__": "_phase9i_pinned_equivalents"}
    exec(compile(source, PINNED + ":" + path, "exec"), namespace)
    return namespace["repair_equivalents"]


def historical_retained(item: dict[str, Any]) -> dict[str, str]:
    """Reconstruct pinned equivalents; other transforms remain byte-guarded."""
    paths = (
        "validation/formats.py",
        "security/addressing.py",
        "security/defaults.py",
    )
    for relative in paths:
        path = "backend/app/" + relative
        pinned = subprocess.check_output(["git", "show", PINNED + ":" + path], cwd=ROOT)
        assert pinned == (ROOT / path).read_bytes(), path
    current = item["package"]["files"]
    filename = item["key"].replace("/", "-") + ".json"
    for name in ("equivalents", "addressing", "formats", "defaults"):
        row = json.loads((OLD_EVIDENCE / ("cumulative_" + name) / filename).read_text())
        assert digest(current) == row["before_sha256"]
        candidate, _ = (
            pinned_equivalents()(current)
            if name == "equivalents"
            else proposal(name, current, row["before"])
        )
        assert digest(candidate) == row["candidate_sha256"]
        current = candidate if row["reason"] == "accepted" else current
        assert digest(current) == row["retained_sha256"]
    return current


class KubeObserver(Observer):
    async def observe(
        self, item: dict[str, Any], files: dict[str, str]
    ) -> dict[str, Any]:
        key = digest(
            {
                "files": files,
                "plan": item["plan"],
                "variant": item["variant"],
                "versions": self.versions,
                "scanner_versions": self.scanner_versions,
                "evaluator": self.evaluator,
                "providers": self.provider_manifest,
                "network_isolated": True,
                "tool_timeout": 60,
                "validation_deadline": 120,
                "protocol": "kubernetes-1",
            }
        )
        if key in self.observations:
            return self.observations[key]
        path = self.cache / (key + ".json")
        if path.exists():
            package = json.loads(path.read_text())
        else:
            runner = ProcessToolRunner(60)
            report = await ValidationEngine(
                runner=runner, versions=self.versions
            ).validate(DeploymentPlan.model_validate(item["plan"]), files)
            all_findings: list[dict[str, Any]] = []
            try:
                scan = await Scanner(runner).scan(files, Variant(item["variant"]))
                all_findings = [v.model_dump(mode="json") for v in scan.violations]
                blockers = [v for v in all_findings if v["blocking"]]
                final = {
                    "outcome": "exhausted" if blockers else "clean",
                    "remaining_blocking": blockers,
                }
            except ToolFailure as error:
                final = {"outcome": "unknown", "failure_category": error.category}
            package = {
                "validation_report": report.model_dump(mode="json"),
                "security_report": {"final": final},
                "all_findings": all_findings,
            }
            write(path, package)
        observed = projection({**package, "files": files})
        observed["findings"] = package["all_findings"]
        self.observations[key] = observed
        return observed


async def catalogue_change(
    observer: KubeObserver,
    item: dict[str, Any],
    files: dict[str, str],
    *,
    formats: bool,
):
    before = await observer.observe(item, files)
    name = "formats_and_pods" if formats else "pods"
    records: list[dict[str, Any]] = []
    candidate = files
    reason = "unchanged"
    budget = AgentBudget(120)
    after = before
    try:
        async with asyncio.timeout(budget.remaining()):
            candidate, records = await (
                repair_formats_and_pods(files) if formats else repair_kubernetes(files)
            )
            repeated, _ = await (
                repair_formats_and_pods(candidate)
                if formats
                else repair_kubernetes(candidate)
            )
            assert repeated == candidate, (item["key"], "candidate not idempotent")
            if candidate != files:
                after = await observer.observe(item, candidate)
                verifier, scanner = (
                    ReplayVerifier(observer, item),
                    ReplayScanner(observer, item),
                )
                guard = CandidateGuard(
                    verifier,
                    scanner,
                    Variant(item["variant"]),
                    budget,
                    {
                        "terraform_verification_seconds": 0.0,
                        "security_verification_seconds": 0.0,
                    },
                )
                result = await guard.evaluate(
                    files,
                    candidate,
                    await verifier.checks(files),
                    await scanner.scan(files, Variant(item["variant"])),
                )
                reason = result.reason or "accepted"
                if reason == "accepted" and formats:
                    if after["validation"] == "error":
                        reason = "verification_unavailable"
                    elif len(after["failed_checks"]) >= len(before["failed_checks"]):
                        reason = "no_improvement"
    except (ToolFailure, TimeoutError):
        reason = "verification_unavailable"
    retained = candidate if reason == "accepted" else files
    for record in records:
        if record.get("outcome") == "skipped":
            continue
        record.update(
            outcome="accepted" if reason == "accepted" else "rejected", reason=reason
        )
    return retained, {
        "key": item["key"],
        "change": name,
        "reason": reason,
        "before": before,
        "candidate": after,
        "observed": after if reason == "accepted" else before,
        "records": records,
        "removed": sorted(fingerprints(before) - fingerprints(after)),
        "introduced": sorted(fingerprints(after) - fingerprints(before)),
        "before_sha256": digest(files),
        "candidate_sha256": digest(candidate),
        "retained_sha256": digest(retained),
        "candidate_idempotent": True,
    }


def counts(observations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "packages": len(observations),
        "valid": sum(o["validation"] == "valid" for o in observations),
        "unknown_scan": sum(o["scan_outcome"] == "unknown" for o in observations),
        "unknown_validation": sum(o["validation"] == "error" for o in observations),
        "checks_passed": {
            p: sum(o["profiles"][p]["checks_passed"] is True for o in observations)
            for p in PROFILES
        },
        "blockers": {
            p: sum(o["profiles"][p]["remaining_blocking"] or 0 for o in observations)
            for p in PROFILES
        },
        "rules": dict(
            Counter(f["rule_id"] for o in observations for f in o["blockers"])
        ),
        "all_rules": dict(
            Counter(f["rule_id"] for o in observations for f in o["findings"])
        ),
    }


async def run(output: Path, cache: Path, workers: int) -> None:
    if any(name != "lo" for _, name in socket.if_nameindex()):
        raise ValueError("Replay requires a network namespace containing only loopback")
    packages, manifest = inventory()
    output.mkdir(parents=True, exist_ok=True)
    write(output / "input-manifest.json", manifest)
    evaluator_manifest = code_manifest()
    for relative in (
        "backend/scripts/phase9i_kubernetes_replay.py",
        "backend/app/agents/deterministic.py",
        "backend/app/agents/security/agent.py",
        "backend/app/domain/archive.py",
    ):
        evaluator_manifest[relative] = hashlib.sha256(
            (ROOT / relative).read_bytes()
        ).hexdigest()
    fingerprint = digest(evaluator_manifest)
    observer = KubeObserver(cache, network_isolated=True)
    observer.evaluator = fingerprint
    write(output / "execution-evaluator-manifest.json", evaluator_manifest)
    labels, semaphore = prompt_labels(), asyncio.Semaphore(workers)
    completed = 0

    async def process(item):
        nonlocal completed
        async with semaphore:
            stored = item["package"]["profile_assessments"]
            actual = assess(item["package"])
            assert all(stored[p] == actual[p] for p in PROFILES[:2]), item["key"]
            original = item["package"]["files"]
            previous = historical_retained(item)
            workspace = ValidationWorkspace()
            rows = {}
            try:
                with workspace.activate():
                    initial = await observer.observe(item, original)
                    old = await observer.observe(item, previous)
                    rows["baseline"] = {
                        "key": item["key"],
                        "observed": initial,
                        "reason": "baseline",
                    }
                    rows["previous_retained"] = {
                        "key": item["key"],
                        "observed": old,
                        "reason": "historical_retained",
                        "retained_sha256": digest(previous),
                    }
                    _, rows["independent_pods"] = await catalogue_change(
                        observer, item, original, formats=False
                    )
                    _, rows["independent_formats"] = await catalogue_change(
                        observer, item, original, formats=True
                    )
                    current = original
                    for name in (
                        "equivalents",
                        "addressing",
                        "formats",
                        "defaults",
                        "pods",
                    ):
                        if name in {"formats", "pods"}:
                            current, row = await catalogue_change(
                                observer, item, current, formats=name == "formats"
                            )
                        else:
                            current, row = await replay_change(
                                observer, item, current, name
                            )
                        rows["cumulative_" + name] = row
            finally:
                workspace.close()
            completed += 1
            for stage, row in rows.items():
                row["prompt"] = labels[item["key"].rsplit("/", 1)[0]]
                row["provenance"] = {
                    "evaluator": fingerprint,
                    "plan": digest(item["plan"]),
                    "variant": item["variant"],
                    "tool_versions": observer.versions,
                    "scanner_versions": observer.scanner_versions,
                    "providers": observer.provider_manifest,
                    "network_isolated": True,
                    "tool_timeout": 60,
                    "validation_deadline": 120,
                    "protocol": "kubernetes-1",
                }
                if "before" in row:
                    row["candidate_delta"] = compare(row["before"], row["candidate"])
                    row["retained_delta"] = compare(row["before"], row["observed"])
                write(output / stage / (item["key"].replace("/", "-") + ".json"), row)
            print(f"replay {completed}/{len(packages)} {item['key']}", flush=True)
            return rows

    results = await asyncio.gather(*(process(item) for item in packages))
    summary = {}
    for stage in results[0]:
        rows = [result[stage] for result in results]
        summary[stage] = {
            **counts([r["observed"] for r in rows]),
            "outcomes": dict(Counter(r["reason"] for r in rows)),
            "per_prompt": {
                label: counts([r["observed"] for r in rows if r["prompt"] == label])
                for label in ("ECS", "EKS", "static")
            },
            "candidate_new_rules": dict(
                Counter(f[0] for r in rows for f in r.get("introduced", []))
            ),
            "candidate_removed_rules": dict(
                Counter(f[0] for r in rows for f in r.get("removed", []))
            ),
        }
    write(output / "summary.json", summary)
    write(
        output / "verification.json",
        {
            "packages": len(packages),
            "runs": 28,
            "missing_variants": manifest["missing_variants"],
            "strict_v1_golden_matches": len(packages),
            "catalogue_candidate_idempotence_checks": len(packages) * 4,
            "historical_package_hash_matches": len(packages),
            "pinned_commit": PINNED,
            "network_isolated": True,
            "llm_calls": 0,
            "evaluator": fingerprint,
            "versions": observer.versions,
            "scanner_versions": observer.scanner_versions,
        },
    )
    assert inventory()[1] == manifest
    print(
        json.dumps(
            {
                s: {
                    k: v
                    for k, v in row.items()
                    if k in {"valid", "checks_passed", "outcomes"}
                }
                for s, row in summary.items()
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    parser.add_argument(
        "--cache", type=Path, default=ROOT / ".cache/phase9i-kubernetes-replay"
    )
    parser.add_argument("--workers", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    asyncio.run(run(args.output, args.cache, args.workers))


if __name__ == "__main__":
    main()
