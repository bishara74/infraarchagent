"""Immutable, offline Phase 9i observations. Never instantiate operator settings."""

import argparse
import asyncio
import hashlib
import json
import socket
from collections import Counter
from pathlib import Path
from typing import Any

from app.agents.budget import AgentBudget
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationCheck
from app.scanners.runner import ProcessToolRunner, ToolFailure, scanner_versions
from app.scanners.scan import Scanner, ScanResult
from app.security.acceptance import CandidateGuard
from app.security.addressing import repair_addressing
from app.security.defaults import repair_defaults
from app.security.generation import generation_context
from app.security.profiles import assess
from app.validation.engine import ValidationEngine
from app.validation.equivalents import repair_equivalents
from app.validation.formats import repair_formats
from app.validation.provider_schema import DEFAULT_INDEX
from app.validation.tools import report_versions
from app.validation.workspace import ValidationWorkspace

ROOT = Path(__file__).resolve().parents[2]
SETS = (
    "phase9-bench-real-20261020T010134093069Z",
    "phase9-bench-real-20261020T013911945957Z",
)
EVIDENCE = ROOT / "docs/evals/phase9i-offline"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def inventory(root: Path = ROOT) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    packages, sources, missing = [], [], []
    for number, name in enumerate(SETS, 1):
        run_path = root / "docs/evals" / name / "results.json"
        sources.append(
            {
                "path": str(run_path.relative_to(root)),
                "sha256": hashlib.sha256(run_path.read_bytes()).hexdigest(),
            }
        )
        for run in json.loads(run_path.read_text())["runs"]:
            path = root / f".cache/final-{number}-results/{run['run_id']}.json"
            data = json.loads(path.read_text())
            sources.append(
                {
                    "path": str(path.relative_to(root)),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
            for item in data["missing_variants"]:
                missing.append(
                    {"set": number, "run_id": run["run_id"], "variant": item["variant"]}
                )
            for package in data["packages"]:
                packages.append(
                    {
                        "key": f"{number}/{run['run_id']}/{package['variant']}",
                        "set": number,
                        "run_id": run["run_id"],
                        "variant": package["variant"],
                        "plan": data["plan"],
                        "package": package,
                    }
                )
    manifest = {
        "sources": sources,
        "missing_variants": missing,
        "packages": [
            {
                "key": p["key"],
                "files_sha256": digest(p["package"]["files"]),
                "plan_sha256": digest(p["plan"]),
            }
            for p in packages
        ],
    }
    return packages, manifest


def code_manifest() -> dict[str, str]:
    paths = [
        *(ROOT / "backend/app/validation").glob("*.py"),
        *(ROOT / "backend/app/scanners").glob("*.py"),
        *(ROOT / "backend/app/security").rglob("*.py"),
        *(ROOT / "backend/app/security/profiles").glob("*.json"),
        ROOT / "backend/app/domain/validation.py",
    ]
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(paths)
    }


def code_fingerprint() -> str:
    return digest(code_manifest())


def projection(package: dict[str, Any]) -> dict[str, Any]:
    validation = package.get("validation_report") or {}
    final = (package.get("security_report") or {}).get("final") or {}
    findings = final.get("remaining_blocking", [])
    return {
        "validation": validation.get("summary", {}).get("result", "error"),
        "failed_checks": [
            {k: c.get(k) for k in ("check_id", "file_path", "line_start", "message")}
            for c in validation.get("checks", [])
            if c.get("status") == "failed"
        ],
        "blockers": [
            {k: f.get(k) for k in ("rule_id", "file_path", "resource")}
            for f in findings
        ],
        "scan_outcome": final.get("outcome", "unknown"),
        "terraform_unknown": any(
            c.get("tool") == "terraform" and c.get("status") == "skipped"
            for c in validation.get("checks", [])
        ),
        "profiles": assess(package),
    }


class Observer:
    def __init__(self, cache: Path, network_isolated: bool = False):
        self.cache = cache
        self.versions = report_versions()
        self.evaluator = code_fingerprint()
        self.scanner_versions = scanner_versions()
        self.network_isolated = network_isolated
        self.observations: dict[str, dict[str, Any]] = {}
        self.provider_manifest = hashlib.sha256(
            (DEFAULT_INDEX / "manifest.json").read_bytes()
        ).hexdigest()

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
                "network_isolated": self.network_isolated,
                "evaluator": self.evaluator,
                "provider_manifest": self.provider_manifest,
                "protocol": 2,
                "tool_timeout": 60,
                "validation_deadline": 120,
            }
        )
        path = self.cache / f"{key}.json"
        if key in self.observations:
            return self.observations[key]
        if path.exists():
            package = json.loads(path.read_text())
        else:
            runner = ProcessToolRunner(60)
            report = await ValidationEngine(
                runner=runner, versions=self.versions
            ).validate(DeploymentPlan.model_validate(item["plan"]), files)
            try:
                scan = await Scanner(runner).scan(files, Variant(item["variant"]))
                blockers = [
                    v.model_dump(mode="json") for v in scan.violations if v.blocking
                ]
                final = {
                    "outcome": "exhausted" if blockers else "clean",
                    "remaining_blocking": blockers,
                }
            except Exception:
                final = {"outcome": "unknown"}
            package = {
                "validation_report": report.model_dump(mode="json"),
                "security_report": {"final": final},
            }
            self.cache.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(package, sort_keys=True))
        observed = projection({**package, "files": files})
        self.observations[key] = observed
        return observed


def fingerprints(value: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {(f["rule_id"], f["file_path"], f["resource"]) for f in value["blockers"]}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profiles: dict[str, Any] = {}
    for row in rows:
        for name, view in row["observed"]["profiles"].items():
            p = profiles.setdefault(name, {"passes": 0, "blockers": 0, "exceptions": 0})
            p["passes"] += bool(view["checks_passed"])
            p["blockers"] += view["remaining_blocking"]
            p["exceptions"] += len(view["excepted"])
    return {
        "packages": len(rows),
        "validation": dict(Counter(r["observed"]["validation"] for r in rows)),
        "scan_unknown": sum(r["observed"]["scan_outcome"] == "unknown" for r in rows),
        "profiles": profiles,
    }


async def baseline(output: Path, cache: Path) -> None:
    packages, manifest = inventory()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "input-manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        raise ValueError("input manifest changed")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    observer = Observer(cache)
    rows = []
    for item in packages:
        path = output / "baseline" / (item["key"].replace("/", "-") + ".json")
        if path.exists():
            rows.append(json.loads(path.read_text()))
            continue
        observed = await observer.observe(item, item["package"]["files"])
        context = generation_context(DeploymentPlan.model_validate(item["plan"]))
        row = {
            "key": item["key"],
            "stored": projection(item["package"]),
            "observed": observed,
            "context": {
                "schema": context.schema_chars,
                "checklist": context.checklist_chars,
                "total": len(context.text),
                "truncated": context.truncated,
                "resource_types": context.resource_types,
            },
            "versions": observer.versions,
            "evaluator_sha256": observer.evaluator,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(row, indent=2) + "\n")
        rows.append(row)
        print(f"baseline {len(rows)}/{len(packages)} {item['key']}", flush=True)
    summary = aggregate(rows)
    (output / "baseline-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


def reassess(observation: dict[str, Any], files: dict[str, str]) -> dict[str, Any]:
    final = {"outcome": observation["scan_outcome"]}
    if observation["scan_outcome"] != "unknown":
        final["remaining_blocking"] = observation["blockers"]
    return {
        **observation,
        "profiles": assess(
            {
                "files": files,
                "validation_report": {"summary": {"result": observation["validation"]}},
                "security_report": {"final": final},
            }
        ),
    }


class ReplayVerifier:
    def __init__(self, observer: Observer, item: dict[str, Any]):
        self.observer, self.item = observer, item

    async def checks(self, files: dict[str, str]) -> list[ValidationCheck]:
        observed = await self.observer.observe(self.item, files)
        checks = [
            ValidationCheck(
                tool="terraform", category="terraform", status="failed", **c
            )
            for c in observed["failed_checks"]
            if c["check_id"] == "terraform.validate"
        ]
        if observed["terraform_unknown"] or observed["validation"] == "error":
            checks.append(
                ValidationCheck(
                    check_id="terraform.validate",
                    tool="terraform",
                    category="terraform",
                    status="skipped",
                    message="Offline verification unavailable",
                    skip_reason="tool_error",
                )
            )
        return checks


class ReplayScanner(Scanner):
    def __init__(self, observer: Observer, item: dict[str, Any]):
        super().__init__(ProcessToolRunner(60))
        self.observer, self.item = observer, item

    async def scan(
        self, files: dict[str, str], variant: Variant, *, iteration: int = 0
    ) -> ScanResult:
        observed = await self.observer.observe(self.item, files)
        if observed["scan_outcome"] == "unknown":
            raise ToolFailure("trivy", "verification_unavailable")
        return ScanResult(
            [
                Violation(
                    **f, tool="trivy", message="Offline blocking finding", blocking=True
                )
                for f in observed["blockers"]
            ],
            {"trivy": "ok", "checkov": "ok", "terraform": "ok"},
        )


CHANGES = {
    "equivalents": repair_equivalents,
    "addressing": repair_addressing,
    "formats": repair_formats,
    "defaults": repair_defaults,
}


async def replay_change(
    observer: Observer, item: dict[str, Any], files: dict[str, str], name: str
) -> tuple[dict[str, str], dict[str, Any]]:
    before = await observer.observe(item, files)
    if name in {"addressing", "defaults"}:
        rules = (
            {"CKV_AWS_130", "AWS-0164"}
            if name == "addressing"
            else {"AWS-0077", "CKV2_AWS_12"}
        )
        targets = {
            (str(Path(f["file_path"]).parent), f["resource"].split("[", 1)[0])
            for f in before["blockers"]
            if f["rule_id"] in rules
        }
        candidate, records = CHANGES[name](files, targets)
    else:
        candidate, records = CHANGES[name](files)
    after = before
    reason = "unchanged"
    introduced = []
    if candidate != files:
        after = await observer.observe(item, candidate)
        introduced = sorted(fingerprints(after) - fingerprints(before))
        verifier, scanner = (
            ReplayVerifier(observer, item),
            ReplayScanner(observer, item),
        )
        guard = CandidateGuard(
            verifier,
            scanner,
            Variant(item["variant"]),
            AgentBudget(120),
            {
                "terraform_verification_seconds": 0.0,
                "security_verification_seconds": 0.0,
            },
        )
        try:
            checked = await guard.evaluate(
                files,
                candidate,
                await verifier.checks(files),
                await scanner.scan(files, Variant(item["variant"])),
            )
            reason = checked.reason or "accepted"
            if reason == "accepted" and name in {"equivalents", "formats"}:
                if after["validation"] == "error":
                    reason = "verification_unavailable"
                elif len(after["failed_checks"]) >= len(before["failed_checks"]):
                    reason = "no_improvement"
        except (ToolFailure, TimeoutError):
            reason = "verification_unavailable"
    retained = candidate if reason == "accepted" else files
    observation = after if reason == "accepted" else before
    return retained, {
        "key": item["key"],
        "change": name,
        "reason": reason,
        "before": before,
        "candidate": after,
        "observed": observation,
        "introduced": introduced,
        "removed": sorted(fingerprints(before) - fingerprints(after)),
        "records": records,
        "before_sha256": digest(files),
        "candidate_sha256": digest(candidate),
        "retained_sha256": digest(retained),
    }


async def changes(
    output: Path, cache: Path, *, network_isolated: bool = False, workers: int = 1
) -> None:
    packages, manifest = inventory()
    assert json.loads((output / "input-manifest.json").read_text()) == manifest
    if not network_isolated or any(name != "lo" for _, name in socket.if_nameindex()):
        raise ValueError(
            "changes require an isolated network namespace with only loopback"
        )
    observer = Observer(cache, network_isolated=True)
    execution_manifest = code_manifest()
    manifest_path = output / "execution-evaluator-manifest.json"
    if manifest_path.exists():
        assert json.loads(manifest_path.read_text()) == execution_manifest
    manifest_path.write_text(json.dumps(execution_manifest, indent=2) + "\n")
    rows_by_stage: dict[str, list[dict[str, Any]]] = {}
    contexts = []
    semaphore = asyncio.Semaphore(workers)
    completed = 0

    async def process(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        async with semaphore:
            return await process_one(item)

    async def process_one(
        item: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        nonlocal completed
        rows: dict[str, Any] = {}
        original = item["package"]["files"]
        stored = item["package"]["profile_assessments"]
        original_assessments = assess(item["package"])
        assert all(
            original_assessments[name] == stored[name]
            for name in ("strict", "contextual-v1")
        ), item["key"]
        baseline_path = output / "baseline" / (item["key"].replace("/", "-") + ".json")
        frozen = json.loads(baseline_path.read_text())
        context = generation_context(DeploymentPlan.model_validate(item["plan"]))
        context_row = {
            "key": item["key"],
            "before": frozen["context"],
            "after": {
                "schema": context.schema_chars,
                "checklist": context.checklist_chars,
                "total": len(context.text),
                "truncated": context.truncated,
                "resource_types": context.resource_types,
            },
        }
        workspace = ValidationWorkspace()
        try:
            with workspace.activate():
                # A fresh baseline under the final validator separates diagnostic
                # reporting differences from infrastructure repair effects.
                initial = await observer.observe(item, original)
                for stage in ("schema_guidance", "contextual_v2"):
                    rows[stage] = {
                        "key": item["key"],
                        "observed": initial,
                        "reason": "no_infrastructure_change",
                    }
                current = original
                for name in CHANGES:
                    _, independent = await replay_change(observer, item, original, name)
                    rows["independent_" + name] = independent
                    current, cumulative = await replay_change(
                        observer, item, current, name
                    )
                    rows["cumulative_" + name] = cumulative
        finally:
            workspace.close()
        completed += 1
        print(f"replay {completed}/{len(packages)} {item['key']}", flush=True)
        # Checkpoint projections only; original and candidate source bytes never
        # enter the committed evidence directory.
        for stage, row in rows.items():
            row["provenance"] = {
                "evaluator_sha256": observer.evaluator,
                "files_sha256": digest(original),
                "plan_sha256": digest(item["plan"]),
                "variant": item["variant"],
                "versions": observer.versions,
                "scanner_versions": observer.scanner_versions,
                "network_isolated": True,
                "provider_manifest_sha256": observer.provider_manifest,
                "tool_timeout": 60,
                "validation_deadline": 120,
                "protocol": 2,
            }
            directory = output / stage
            directory.mkdir(exist_ok=True)
            (directory / (item["key"].replace("/", "-") + ".json")).write_text(
                json.dumps(row, indent=2) + "\n"
            )
        return rows, context_row

    for rows, context_row in await asyncio.gather(*(process(p) for p in packages)):
        contexts.append(context_row)
        for stage, row in rows.items():
            rows_by_stage.setdefault(stage, []).append(row)
    summaries = {}
    for stage, rows in rows_by_stage.items():
        summaries[stage] = {
            **aggregate(rows),
            "outcomes": dict(Counter(r["reason"] for r in rows)),
            "introduced_candidate_findings": sum(
                len(r.get("introduced", [])) for r in rows
            ),
        }
    (output / "change-summaries.json").write_text(
        json.dumps(summaries, indent=2) + "\n"
    )
    (output / "context-sizes.json").write_text(json.dumps(contexts, indent=2) + "\n")
    (output / "compatibility.json").write_text(
        json.dumps(
            {
                "packages": len(packages),
                "strict_v1_exact_match": True,
                "provider_manifest_sha256": observer.provider_manifest,
                "evaluator_sha256": observer.evaluator,
                "versions": observer.versions,
                "scanner_versions": observer.scanner_versions,
                "network_isolated": True,
                "llm_calls": 0,
            },
            indent=2,
        )
        + "\n"
    )
    assert inventory()[1] == manifest
    print(json.dumps(summaries), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/phase9i-replay")
    parser.add_argument("--mode", choices=("baseline", "changes"), default="baseline")
    parser.add_argument("--network-isolated", action="store_true")
    parser.add_argument("--workers", type=int, choices=range(1, 4), default=1)
    args = parser.parse_args()
    asyncio.run(
        baseline(args.output, args.cache)
        if args.mode == "baseline"
        else changes(
            args.output,
            args.cache,
            network_isolated=args.network_isolated,
            workers=args.workers,
        )
    )


if __name__ == "__main__":
    main()
