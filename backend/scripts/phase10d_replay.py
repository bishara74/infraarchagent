"""FR-S-07/FR-P-04: paired offline observations of the frozen 59-package rerun."""

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any

from app.agents.budget import AgentBudget
from app.core.logging import RedactingFilter
from app.core.public_catalogue import digest
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.plan import DeploymentPlan
from app.scanners.runner import ToolFailure
from app.security.acceptance import CandidateGuard
from app.security.catalogue import autofix
from app.security.kubernetes_render import repair_kubernetes
from app.security.partial import RetainedCandidate, accept_groups
from app.security.plan_conformance import plan_regressions
from app.security.templates import build_template
from app.validation.equivalents import repair_equivalents
from app.validation.repairs import repair_declarations
from app.validation.syntax import normalize_blocks
from app.validation.workspace import ValidationWorkspace
from scripts.phase9d_quality import quality_snapshot
from scripts.phase10c_replay import (
    Observer,
    apply_diff,
    finding_keys,
    projection,
    write,
)
from scripts.phase10d_diagnosis import COHORT, ROOT, inventory

BASELINE = "d7f82a1"


def load_baseline(path: str) -> types.ModuleType:
    code = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
    module = types.ModuleType("phase10d_baseline_" + Path(path).stem)
    sys.modules[module.__name__] = module
    exec(compile(code, path, "exec"), module.__dict__)
    return module


def export_counts(packages: list[dict], snapshot) -> dict:
    counts: Counter = Counter()
    for package in packages:
        exported = snapshot(package, RedactingFilter())["phase9e"]
        for v in exported["security_iteration_repairs"]:
            if v["outcome"] == "rolled_back" and not v["reasons"]:
                counts["empty_rollback_attempts"] += 1
                counts["empty_rollback_error_classes"] += len(
                    v["error_classes"] or [None]
                )
        for r in exported["repair_rounds"]:
            if r["outcome"] == "rejected" and r["reason"] == "unknown":
                counts["unknown_repair_attempts"] += 1
                counts["unknown_repair_error_classes"] += len(
                    r["error_classes"] or [None]
                )
    return {
        k: counts[k]
        for k in (
            "empty_rollback_attempts",
            "empty_rollback_error_classes",
            "unknown_repair_attempts",
            "unknown_repair_error_classes",
        )
    }


class Replay:
    def __init__(self, observer: Observer):
        self.observer = observer
        old_plan = load_baseline("backend/app/security/plan_conformance.py")
        old_verifier = load_baseline("backend/app/agents/security/verification.py")
        old_acceptance = load_baseline("backend/app/security/acceptance.py")
        old_acceptance.plan_regressions = old_plan.plan_regressions
        old_acceptance.failure_count = old_verifier.failure_count
        self.old_guard = old_acceptance.CandidateGuard
        self.old_plan = old_plan.plan_regressions
        self.rows: list[dict] = []
        self.groups: list[dict] = []
        self.missing: list[dict] = []
        self.retained: list[dict] = []
        self.context: dict[str, Any] = {}
        self.final_keys: set[tuple[str, str, str]] = set()
        self.cache: dict[str, dict] = {}

    async def candidate(
        self,
        before: dict,
        proposed: dict,
        action: str,
        findings: list[Violation],
        *,
        validation=False,
    ) -> None:
        if proposed == before:
            return
        key = digest(
            {
                "before": before,
                "candidate": proposed,
                "context": {k: v for k, v in self.context.items() if k != "iteration"},
                "action": action,
            }
        )
        if key in self.cache:
            row = {**self.cache[key], **self.context, "cached_identical_pair": True}
            self.rows.append(row)
            for group in row["groups"]:
                self.groups.append({**self.context, "action": action, **group})
            return
        observer = self.observer
        row = {
            **self.context,
            "action": action,
            "before_sha256": digest(before),
            "candidate_sha256": digest(proposed),
            "removed_still_open": [],
            "groups": [],
        }
        baseline = await observer.observe(before)
        row["baseline"] = projection(baseline)
        for name, guard_class in (
            ("before", self.old_guard),
            ("after", CandidateGuard),
        ):
            record = {
                "terraform_verification_seconds": 0.0,
                "security_verification_seconds": 0.0,
            }
            guard = guard_class(
                observer,
                observer,
                observer.variant,
                AgentBudget(600),
                record,
                plan=observer.plan,
                targeted=findings,
            )
            reason = "verification_unavailable"
            try:
                checked = await guard.evaluate(
                    before,
                    proposed,
                    await observer.checks(before),
                    await observer.scan(before, observer.variant),
                )
                reason = checked.reason
                if validation and reason is None:
                    a, b = (
                        baseline["validation"]["summary"],
                        (await observer.observe(proposed))["validation"]["summary"],
                    )
                    if b["result"] == "error":
                        reason = "verification_unavailable"
                    elif b["failed"] >= a["failed"]:
                        reason = "no_improvement"
                row[name] = reason or "accepted"
                # This is a derived group replay, not missing historical Fixer bodies.
                records: list[dict] = []
                checkpoint = RetainedCandidate(
                    before, await observer.scan(before, observer.variant)
                )
                await accept_groups(
                    guard,
                    before,
                    proposed,
                    await observer.checks(before),
                    checkpoint.scan,
                    6,
                    records,
                    checkpoint,
                )
                for index, group in enumerate(records):
                    if name == "before":
                        row["groups"].append(
                            {
                                "index": index,
                                "changes": group["changes"],
                                "before": group["status"],
                                "before_reason": group["reason"],
                            }
                        )
                    else:
                        if index >= len(row["groups"]):
                            row["groups"].append(
                                {
                                    "index": index,
                                    "changes": group["changes"],
                                    "before": "unavailable",
                                    "before_reason": "verification_unavailable",
                                }
                            )
                        # Accepted earlier groups can affect subsequent groups' results;
                        # fixed original change-group identities still align by index.
                        row["groups"][index].update(
                            after=group["status"], after_reason=group["reason"]
                        )
            except (ToolFailure, TimeoutError):
                row[name] = "verification_unavailable"
        if row.get("after") == "accepted":
            candidate = await observer.observe(proposed)
            row["candidate"] = projection(candidate)
            removed = finding_keys(row["baseline"]["blockers"]) - finding_keys(
                row["candidate"]["blockers"]
            )
            row["removed_still_open"] = [
                list(v) for v in sorted(removed & self.final_keys)
            ]
        self.rows.append(row)
        self.cache[key] = row
        self.groups.extend(
            {**self.context, "action": action, **g} for g in row["groups"]
        )

    async def retained_observation(self, files: dict) -> dict | None:
        return projection(await self.observer.observe(files))

    async def package(self, item: dict) -> dict:
        p, observer = item["package"], self.observer
        observer.plan = DeploymentPlan.model_validate(item["plan"])
        observer.variant = Variant(item["variant"])
        observer.memory.clear()
        self.context = {k: item[k] for k in ("run_id", "scenario", "round", "variant")}
        self.final_keys = finding_keys(
            p["security_report"]["final"].get("remaining_blocking", [])
        )
        row = {
            **self.context,
            "retained_sha256": digest(p["files"]),
            "reconstruction": "complete",
        }
        workspace = ValidationWorkspace()
        try:
            with workspace.activate():
                row["retained_native"] = await self.retained_observation(p["files"])
                normalized, _ = normalize_blocks(p["original_files"])
                declared, _ = await repair_declarations(normalized)
                snapshots = [declared, normalized, p["original_files"], p["files"]]
                sessions = p["security_report"].get("sessions", [])
                iterations = [
                    it
                    for s in sessions
                    for it in s.get("iterations", [])
                    if it.get("verification")
                ]
                for it in iterations:
                    if it["verification"].get("outcome") == "rolled_back":
                        self.missing.append(
                            {
                                **self.context,
                                "iteration": it["index"],
                                "kind": "rejected_fixer_body",
                                "reasons": it["verification"].get("reasons", []),
                            }
                        )
                post = p["validation_report"]["remediation"].get("rounds", [])
                for repair in post:
                    if repair["outcome"] == "rejected":
                        self.missing.append(
                            {
                                **self.context,
                                "kind": "rejected_validation_fixer_body",
                                "phase": repair["phase"],
                                "iteration": repair["index"],
                                "reasons": [repair["reason"]],
                            }
                        )
                if any(
                    r["phase"] == "after_security" and r["outcome"] == "accepted"
                    for r in post
                ):
                    row["reconstruction"] = "post_security_patch_unavailable"
                    self.missing.append(
                        {**self.context, "kind": "accepted_post_security_patch"}
                    )
                else:
                    files = dict(p["files"])
                    for session in reversed(sessions):
                        if session.get("diff_omitted_chars"):
                            raise ValueError("Truncated session diff")
                        files = apply_diff(files, session["diff"], True)
                    for it in iterations:
                        self.context["iteration"] = it["index"]
                        start = dict(files)
                        snapshots.append(start)
                        verification = it["verification"]
                        findings = [
                            Violation.model_validate(v)
                            for kind in ("blocking", "advisory")
                            for v in it.get("scan", {}).get(kind, [])
                        ]
                        automatic, _ = autofix(files, findings)
                        if any(p.startswith(("helm/", "k8s/")) for p in automatic):
                            automatic, _ = await repair_kubernetes(automatic)
                        if any(
                            r.get("reason")
                            in {
                                "plan_conformance_regression",
                                "terraform_verification_unavailable",
                            }
                            for r in verification.get("catalogue", [])
                        ):
                            await self.candidate(
                                files, automatic, "catalogue", findings
                            )
                        if any(
                            r.get("status") == "retained"
                            for r in verification.get("catalogue", [])
                        ):
                            files = automatic
                            snapshots.append(files)
                        for template in verification.get("templates", []):
                            automatic, _ = build_template(
                                files,
                                findings,
                                template["module"],
                                template["template"],
                            )
                            if template.get("reason") in {
                                "plan_conformance_regression",
                                "terraform_verification_unavailable",
                            }:
                                await self.candidate(
                                    files,
                                    automatic,
                                    "template:" + template["template"],
                                    findings,
                                )
                            if template.get("status") == "retained":
                                files = automatic
                                snapshots.append(files)
                        if it.get("diff_omitted_chars"):
                            raise ValueError("Truncated iteration diff")
                        retained = apply_diff(start, it.get("diff", ""))
                        if retained != start:
                            self.retained.append(
                                {
                                    **self.context,
                                    "before_sha256": digest(start),
                                    "retained_sha256": digest(retained),
                                    "guard_before": bool(
                                        self.old_plan(
                                            observer.plan, start, retained, findings
                                        )
                                    ),
                                    "guard_after": bool(
                                        plan_regressions(
                                            observer.plan, start, retained, findings
                                        )
                                    ),
                                }
                            )
                        files = retained
                    if files != p["files"]:
                        raise ValueError("Retained reconstruction differs")
                self.context.pop("iteration", None)
                for record_index, record in enumerate(
                    p["validation_report"]["remediation"].get(
                        "deterministic_repairs", []
                    )
                ):
                    if (
                        record.get("kind") != "eip_v6_domain"
                        or record.get("reason") != "plan_conformance_regression"
                    ):
                        continue
                    matched = False
                    for files in snapshots:
                        path = record["file"]
                        if hashlib.sha256(
                            files.get(path, "").encode()
                        ).hexdigest() != record.get("before_hash"):
                            continue
                        candidate, records = repair_equivalents(files)
                        if not any(
                            r["kind"] == record["kind"]
                            and r.get("after_hash") == record.get("after_hash")
                            for r in records
                        ):
                            continue
                        self.context["repair_record"] = record_index
                        await self.candidate(
                            files,
                            candidate,
                            "validation:eip_v6_domain",
                            [
                                Violation.model_validate(v)
                                for v in p["security_report"]["final"].get(
                                    "remaining_blocking", []
                                )
                            ],
                            validation=True,
                        )
                        matched = True
                        break
                    if not matched:
                        self.missing.append(
                            {
                                **self.context,
                                "kind": "deterministic_context_hash_unmatched",
                                "repair_record": record_index,
                            }
                        )
                    self.context.pop("repair_record", None)
        finally:
            workspace.close()
        return row


async def run(output: Path, cache: Path) -> None:
    if output.exists() or not output.is_relative_to(ROOT / "docs/evals"):
        raise ValueError("Output must be a fresh evidence directory")
    if not cache.is_relative_to(ROOT / ".cache"):
        raise ValueError("Cache must remain under repository .cache")
    items, inputs = inventory(COHORT, ROOT / ".cache/broad-final2-results")
    if len(items) != 59:
        raise ValueError("Rerun must contain 59 packages")
    old_metrics = load_baseline("backend/scripts/phase9e_metrics.py")
    current_metrics = sys.modules["scripts.phase9e_metrics"]
    try:
        sys.modules["scripts.phase9e_metrics"] = old_metrics
        old_quality = load_baseline("backend/scripts/phase9d_quality.py")
    finally:
        sys.modules["scripts.phase9e_metrics"] = current_metrics
    exported = {
        "before": export_counts(
            [i["package"] for i in items], old_quality.quality_snapshot
        ),
        "after": export_counts([i["package"] for i in items], quality_snapshot),
    }
    output.mkdir(parents=True)
    observer = Observer(cache)
    replay = Replay(observer)
    write(
        output / "manifest.json",
        {
            "baseline": BASELINE,
            "inputs": inputs,
            "runtime": observer.identity,
            "canonical_hash_checks": 177,
        },
    )
    rows = []
    for item in items:
        print(
            f"Replay {len(rows) + 1}/59 scenario "
            f"{item['scenario']}/{item['round']} {item['variant']}",
            flush=True,
        )
        rows.append(await replay.package(item))
        for name, value in (
            ("packages", rows),
            ("candidates", replay.rows),
            ("groups", replay.groups),
            ("missing", replay.missing),
            ("retained-diff-audit", replay.retained),
        ):
            write(output / (name + ".json"), value)
    resolved = {
        (r["run_id"], r["variant"], *v)
        for r in replay.rows
        if r["after"] == "accepted"
        for v in r["removed_still_open"]
    }
    summary = {
        "packages": len(rows),
        "export_projection": exported,
        "candidate_occurrences": len(replay.rows),
        "candidate_decisions": {
            side: dict(Counter(r[side] for r in replay.rows))
            for side in ("before", "after")
        },
        "derived_partial_groups": {
            side: dict(Counter(g.get(side, "unavailable") for g in replay.groups))
            for side in ("before", "after")
        },
        "conditionally_resolved_findings": len(resolved),
        "conditional_rules": dict(Counter(v[2] for v in resolved)),
        "reconstruction": dict(Counter(r["reconstruction"] for r in rows)),
        "missing": dict(Counter(r["kind"] for r in replay.missing)),
        "retained_diff_new_conformance_rejections": sum(
            not r["guard_before"] and r["guard_after"] for r in replay.retained
        ),
        "limitation": (
            "Independent paired available proposals; derived groups are not missing "
            "historical Fixer bodies. EIP contexts match recorded per-file hashes. "
            "No new pass rate, cumulative remediation or historical deadline claim."
        ),
    }
    write(output / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--cache", type=Path, default=ROOT / ".cache/phase10d-observations"
    )
    args = parser.parse_args()
    asyncio.run(run(args.output_dir.resolve(), args.cache.resolve()))


if __name__ == "__main__":
    main()
