"""FR-S-07/FR-V-03: offline, source-free replay of frozen final-round evidence.

No settings, dotenv, model adapter, provider download or network client is used.
Counterfactuals are paired against recorded baselines, not a new LLM trajectory.
"""

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import UUID

from app.agents.budget import AgentBudget
from app.agents.security.verification import TerraformVerifier
from app.core.public_catalogue import digest
from app.domain.enums import Variant
from app.domain.models import Violation
from app.domain.paths import validate_relative_path
from app.domain.plan import DeploymentPlan
from app.domain.validation import ValidationCheck
from app.scanners.runner import ProcessToolRunner, ToolFailure, scanner_versions
from app.scanners.scan import Scanner, ScanResult
from app.security.acceptance import CandidateGuard
from app.security.catalogue import autofix
from app.security.kubernetes_render import repair_kubernetes
from app.security.plan_conformance import plan_regressions
from app.security.templates import build_template
from app.validation.engine import ValidationEngine
from app.validation.equivalents import repair_equivalents
from app.validation.formats import repair_formats
from app.validation.provider_repairs import repair_required_providers
from app.validation.provider_schema import DEFAULT_INDEX
from app.validation.repairs import repair_declarations
from app.validation.syntax import native_syntax, normalize_blocks
from app.validation.tools import report_versions
from app.validation.workspace import ValidationWorkspace
from scripts.phase9i_replay import code_manifest

ROOT = Path(__file__).resolve().parents[2]
COHORT = ROOT / "docs/evals/phase9-bench-broad-20261027T015443795826Z"
BASELINE = "95cdb9f"


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def source(path: Path) -> bytes:
    path = path.resolve()
    if not path.is_relative_to(ROOT) or any(p.startswith(".env") for p in path.parts):
        raise ValueError("Input must be a non-dotenv repository file")
    return path.read_bytes()


def previous_module(path: str) -> types.ModuleType:
    code = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
    module = types.ModuleType("phase10c_baseline_" + Path(path).stem)
    sys.modules[module.__name__] = module
    exec(compile(code, path, "exec"), module.__dict__)
    return module


def apply_diff(
    files: dict[str, str], patch: str, reverse: bool = False
) -> dict[str, str]:
    """Apply complete recorded hunks only, checking every context byte."""
    result = dict(files)
    lines = patch.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        if not lines[i].startswith("--- "):
            raise ValueError("Invalid recorded diff header")
        left, right = lines[i][4:].strip(), lines[i + 1][4:].strip()
        i += 2
        src, dst = (right, left) if reverse else (left, right)
        src = src[2:] if src.startswith(("a/", "b/")) else src
        dst = dst[2:] if dst.startswith(("a/", "b/")) else dst
        for name in (src, dst):
            if name != "/dev/null":
                validate_relative_path(name)
        original = result.get(src, "").splitlines(keepends=True)
        out: list[str] = []
        cursor = 0
        while i < len(lines) and not lines[i].startswith("--- "):
            match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[i])
            if match is None:
                raise ValueError("Invalid recorded diff hunk")
            oldn = int(match[3] if reverse else match[1])
            oldcount = int((match[4] if reverse else match[2]) or 1)
            index = oldn - 1 if oldcount else oldn
            if index < cursor or index > len(original):
                raise ValueError("Invalid recorded diff offset")
            out.extend(original[cursor:index])
            cursor = index
            i += 1
            newcount = int((match[2] if reverse else match[4]) or 1)
            consumed_old = consumed_new = 0
            while consumed_old < oldcount or consumed_new < newcount:
                if i >= len(lines):
                    raise ValueError("Truncated recorded diff hunk")
                row = lines[i]
                i += 1
                prefix, text = row[0], row[1:]
                if i < len(lines) and lines[i].startswith("\\ No newline"):
                    text = text[:-1]
                    i += 1
                if reverse:
                    if prefix not in {"+", "-", " "}:
                        raise ValueError("Invalid recorded diff line")
                    prefix = {"+": "-", "-": "+", " ": " "}[prefix]
                if prefix in (" ", "-"):
                    if cursor >= len(original) or original[cursor] != text:
                        raise ValueError("Recorded diff context mismatch")
                    cursor += 1
                    consumed_old += 1
                if prefix in (" ", "+"):
                    out.append(text)
                    consumed_new += 1
                elif prefix != "-":
                    raise ValueError("Invalid recorded diff line")
                if consumed_old > oldcount or consumed_new > newcount:
                    raise ValueError("Recorded diff count mismatch")
        out.extend(original[cursor:])
        result.pop(src, None)
        if dst != "/dev/null":
            result[dst] = "".join(out)
    return result


def iterations(package: dict) -> list[dict]:
    return [
        i
        for s in package["security_report"].get("sessions", [])
        for i in s.get("iterations", [])
        if "verification" in i
    ]


def finding_keys(findings: list[dict]) -> set[tuple[str, str, str]]:
    return {(v["rule_id"], v["resource"], v["file_path"]) for v in findings}


class Observer:
    def __init__(self, cache: Path):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.identity = {
            "code": code_manifest(),
            "validators": report_versions(),
            "scanners": scanner_versions(),
            "protocol": 1,
            "provider_schema": hashlib.sha256(
                source(DEFAULT_INDEX / "manifest.json")
            ).hexdigest(),
        }
        self.plan: DeploymentPlan
        self.variant: Variant
        self.memory: dict[str, dict] = {}

    async def observe(self, files: dict[str, str]) -> dict:
        key = digest(
            {
                "files": files,
                "plan": self.plan.model_dump(mode="json"),
                "variant": self.variant.value,
                "identity": self.identity,
            }
        )
        if key in self.memory:
            return self.memory[key]
        path = self.cache / f"{key}.json"
        if path.exists():
            observed = json.loads(source(path))
        else:
            report = await ValidationEngine(
                versions=self.identity["validators"]
            ).validate(self.plan, files)
            checks = await TerraformVerifier().checks(files)
            try:
                scan = await Scanner(ProcessToolRunner(120)).scan(files, self.variant)
                observed_scan = {
                    "violations": [v.model_dump(mode="json") for v in scan.violations],
                    "tools": scan.tool_status,
                    "syntax_limited": scan.syntax_limited,
                    "error": None,
                }
            except ToolFailure as error:
                observed_scan = {
                    "violations": [],
                    "tools": {},
                    "syntax_limited": False,
                    "error": {"tool": error.tool, "category": error.category},
                }
            observed = {
                "files_sha256": digest(files),
                "scan": observed_scan,
                "terraform_checks": [c.model_dump(mode="json") for c in checks],
                "validation": report.model_dump(mode="json"),
            }
            write(path, observed)
        self.memory[key] = observed
        return observed

    async def checks(self, files):
        return [
            ValidationCheck.model_validate(c)
            for c in (await self.observe(files))["terraform_checks"]
        ]

    async def scan(self, files, variant):
        assert variant == self.variant
        scan = (await self.observe(files))["scan"]
        if scan["error"]:
            raise ToolFailure(scan["error"]["tool"], scan["error"]["category"])
        return ScanResult(
            [Violation.model_validate(v) for v in scan["violations"]],
            scan["tools"],
            scan["syntax_limited"],
        )


def projection(observed: dict) -> dict:
    validation, scan = observed["validation"], observed["scan"]
    return {
        "files_sha256": observed["files_sha256"],
        "validation_result": validation["summary"]["result"],
        "validation_failed": validation["summary"]["failed"],
        "failed_checks": [
            {k: c[k] for k in ("check_id", "file_path", "line_start", "message")}
            for c in validation["checks"]
            if c["status"] == "failed"
        ],
        "blockers": [
            {k: v[k] for k in ("rule_id", "resource", "file_path")}
            for v in scan["violations"]
            if v["blocking"]
        ],
        "scan_error": scan["error"],
        "tool_status": scan["tools"],
    }


class Replay:
    def __init__(self, observer: Observer):
        self.observer = observer
        self.before = previous_module(
            "backend/app/security/plan_conformance.py"
        ).plan_regressions
        self.old_scanner = previous_module("backend/app/scanners/scan.py").Scanner
        self.rows: list[dict] = []
        self.cache: dict[str, dict] = {}
        self.final_findings: set[tuple[str, str, str]] = set()
        self.context: dict = {}

    async def candidate(
        self,
        before: dict,
        candidate: dict,
        action: str,
        findings: list[Violation],
        *,
        validation_repair: bool = False,
    ) -> dict:
        key = digest(
            {
                "before": before,
                "candidate": candidate,
                "context": {k: v for k, v in self.context.items() if k != "iteration"},
                "action": action,
                "validation_repair": validation_repair,
            }
        )
        if key in self.cache:
            row = {
                **self.cache[key],
                **self.context,
                "reused_identical_observation": True,
            }
            self.rows.append(row)
            return row
        observer = self.observer
        old = self.before(observer.plan, before, candidate, findings)
        new = plan_regressions(observer.plan, before, candidate, findings)
        row = {
            **self.context,
            "action": action,
            "before_sha256": digest(before),
            "candidate_sha256": digest(candidate),
            "before_conflicts": len(old),
            "after_conflicts": len(new),
            "guard_before": bool(old),
            "guard_after": bool(new),
            "changed_paths": sorted(
                p
                for p in before.keys() | candidate.keys()
                if before.get(p) != candidate.get(p)
            ),
            "removed_still_open": [],
            "acceptance": "guard_rejected" if new else "not_evaluated",
        }
        if not new and before != candidate:
            baseline, proposed = (
                await observer.observe(before),
                await observer.observe(candidate),
            )
            row["before_native"], row["candidate_native"] = (
                projection(baseline),
                projection(proposed),
            )
            if baseline["scan"]["error"] or proposed["scan"]["error"]:
                row["acceptance"] = "verification_unavailable"
            else:
                record = {
                    "terraform_verification_seconds": 0.0,
                    "security_verification_seconds": 0.0,
                }
                guard = CandidateGuard(
                    observer,
                    observer,
                    observer.variant,
                    AgentBudget(60),
                    record,
                    plan=observer.plan,
                    targeted=findings,
                )
                try:
                    async with asyncio.timeout(60):
                        checked = await guard.evaluate(
                            before,
                            candidate,
                            await observer.checks(before),
                            await observer.scan(before, observer.variant),
                        )
                    reason = checked.reason
                    if validation_repair and not reason:
                        if proposed["validation"]["summary"]["result"] == "error":
                            reason = "verification_unavailable"
                        elif (
                            proposed["validation"]["summary"]["failed"]
                            >= baseline["validation"]["summary"]["failed"]
                        ):
                            reason = "no_improvement"
                    row["acceptance"] = reason or "accepted"
                except (TimeoutError, ToolFailure):
                    row["acceptance"] = "verification_unavailable"
                if row["acceptance"] == "accepted":
                    removed = finding_keys(
                        row["before_native"]["blockers"]
                    ) - finding_keys(row["candidate_native"]["blockers"])
                    row["removed_still_open"] = [
                        list(k) for k in sorted(removed & self.final_findings)
                    ]
        self.cache[key] = row
        self.rows.append(row)
        return row

    async def package(self, item: dict, output: Path) -> dict:
        package, observer = item["package"], self.observer
        observer.plan, observer.variant = (
            DeploymentPlan.model_validate(item["plan"]),
            Variant(item["variant"]),
        )
        observer.memory.clear()
        self.context = {k: item[k] for k in ("run_id", "variant", "scenario", "round")}
        self.final_findings = finding_keys(
            package["security_report"]["final"].get("remaining_blocking", [])
        )
        row = {
            **self.context,
            "stored_status": package["status"],
            "original_sha256": digest(package["original_files"]),
            "retained_sha256": digest(package["files"]),
            "security_reconstruction": "not_applicable",
        }
        workspace = ValidationWorkspace()
        try:
            with workspace.activate():
                original = package["original_files"]
                normalized, normalizations = normalize_blocks(original)
                declared, declarations = await repair_declarations(normalized)
                row["repairs"] = {
                    "normalizations": len(normalizations),
                    "declarations": declarations,
                    "candidate_sha256": digest(declared),
                }
                for stage, files in (
                    ("original", original),
                    ("declarations", declared),
                    ("retained", package["files"]),
                ):
                    issues = await native_syntax(files)
                    row[stage + "_syntax"] = dict(
                        Counter(issue.message for issue in issues)
                    )
                row["retained_native"] = projection(
                    await observer.observe(package["files"])
                )
                if package["status"] == "scan_error":
                    try:
                        await self.old_scanner(ProcessToolRunner(120)).scan(
                            package["files"], observer.variant
                        )
                        row["old_refusal"] = "not_reproduced"
                    except ToolFailure as error:
                        row["old_refusal"] = {
                            "tool": error.tool,
                            "category": error.category,
                        }
                its = iterations(package)
                if its:
                    post = (
                        package["validation_report"]
                        .get("remediation", {})
                        .get("rounds", [])
                    )
                    if any(
                        r["phase"] == "after_security" and r["outcome"] == "accepted"
                        for r in post
                    ):
                        row["security_reconstruction"] = (
                            "post_security_patch_unavailable"
                        )
                    else:
                        files = dict(package["files"])
                        for session in reversed(
                            package["security_report"].get("sessions", [])
                        ):
                            if session.get("diff_omitted_chars"):
                                raise ValueError("Truncated session diff")
                            files = apply_diff(files, session["diff"], True)
                        for iteration in its:
                            self.context["iteration"] = iteration["index"]
                            if iteration.get("diff_omitted_chars"):
                                raise ValueError("Truncated iteration diff")
                            start = dict(files)
                            findings = [
                                Violation.model_validate(v)
                                for kind in ("blocking", "advisory")
                                for v in iteration.get("scan", {}).get(kind, [])
                            ]
                            verification = iteration["verification"]
                            automatic, _ = autofix(files, findings)
                            if any(p.startswith(("helm/", "k8s/")) for p in automatic):
                                automatic, _ = await repair_kubernetes(automatic)
                            if any(
                                c.get("reason") == "plan_conformance_regression"
                                for c in verification.get("catalogue", [])
                            ):
                                await self.candidate(
                                    files, automatic, "catalogue", findings
                                )
                            if any(
                                c.get("status") == "retained"
                                for c in verification.get("catalogue", [])
                            ):
                                files = automatic
                            for template in verification.get("templates", []):
                                candidate, _ = build_template(
                                    files,
                                    findings,
                                    template["module"],
                                    template["template"],
                                )
                                if (
                                    template.get("reason")
                                    == "plan_conformance_regression"
                                ):
                                    await self.candidate(
                                        files,
                                        candidate,
                                        "template:" + template["template"],
                                        findings,
                                    )
                                if template.get("status") == "retained":
                                    files = candidate
                            retained = apply_diff(start, iteration.get("diff", ""))
                            if retained != start:
                                await self.candidate(
                                    start,
                                    retained,
                                    "recorded_retained_fixer_diff",
                                    findings,
                                )
                            files = retained
                        if files != package["files"]:
                            raise ValueError("Reconstructed retained bytes differ")
                        row["security_reconstruction"] = "complete"
                # Hash-matched deterministic proposals only; no invented LLM result.
                self.context.pop("iteration", None)
                snapshots = [original, normalized, declared, package["files"]]
                used: set[tuple[str, str, str]] = set()
                for record in (
                    package["validation_report"]
                    .get("remediation", {})
                    .get("deterministic_repairs", [])
                ):
                    if record.get(
                        "reason"
                    ) != "plan_conformance_regression" or not record.get("before_hash"):
                        continue
                    for files in snapshots:
                        path = record["file"]
                        if (
                            hashlib.sha256(files.get(path, "").encode()).hexdigest()
                            != record["before_hash"]
                        ):
                            continue
                        for transform in (
                            repair_required_providers,
                            repair_equivalents,
                            repair_formats,
                        ):
                            candidate, records = transform(files)
                            match = next(
                                (
                                    r
                                    for r in records
                                    if r["kind"] == record["kind"]
                                    and r.get("after_hash") == record["after_hash"]
                                ),
                                None,
                            )
                            identity = (
                                record["kind"],
                                record["before_hash"],
                                record["after_hash"],
                            )
                            if match and identity not in used:
                                used.add(identity)
                                findings = [
                                    Violation.model_validate(v)
                                    for v in package["security_report"]["final"].get(
                                        "remaining_blocking", []
                                    )
                                ]
                                await self.candidate(
                                    files,
                                    candidate,
                                    "validation:" + record["kind"],
                                    findings,
                                    validation_repair=True,
                                )
            write(output / f"{item['run_id']}-{item['variant']}.json", row)
            return row
        finally:
            workspace.close()


def inventory(snapshots: Path) -> tuple[list[dict], list[dict]]:
    rows = json.loads(source(COHORT / "results.json"))["runs"]
    items, manifest = [], []
    for row in rows:
        run_id = str(UUID(row["run_id"]))
        path = snapshots / (run_id + ".json")
        raw = source(path)
        manifest.append(
            {
                "path": str(path.resolve().relative_to(ROOT)),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
        data = json.loads(raw)
        for package in data["packages"]:
            variant = Variant(package["variant"]).value
            expected = json.loads(
                source(COHORT / "architecture" / run_id / (variant + ".json"))
            )
            for key, value in (
                ("plan_sha256", data["plan"]),
                ("original_files_sha256", package["original_files"]),
                ("retained_files_sha256", package["files"]),
            ):
                if digest(value) != expected[key]:
                    raise ValueError("Snapshot does not match committed hashes")
            items.append(
                {
                    "run_id": run_id,
                    "variant": variant,
                    "scenario": row["scenario_id"],
                    "round": row["round"],
                    "plan": data["plan"],
                    "package": package,
                }
            )
    if len(rows) != 20 or len(items) != 60:
        raise ValueError("Final cohort must contain 20 runs and 60 packages")
    return items, manifest


async def run(args) -> None:
    output = args.output_dir.resolve()
    if not output.is_relative_to(ROOT / "docs/evals") or output.exists():
        raise ValueError("Output must be a fresh docs/evals directory")
    items, manifest = inventory(args.snapshots.resolve())
    cache = args.cache.resolve()
    if not cache.is_relative_to(ROOT / ".cache"):
        raise ValueError("Observation cache must remain inside repository .cache")
    output.mkdir(parents=True)
    observer = Observer(cache)
    replay = Replay(observer)
    write(
        output / "manifest.json",
        {"baseline": BASELINE, "inputs": manifest, "runtime": observer.identity},
    )
    rows = []
    for item in items:
        print(
            f"Replay {len(rows) + 1}/60 scenario "
            f"{item['scenario']}/{item['round']} {item['variant']}",
            flush=True,
        )
        rows.append(await replay.package(item, output))
        write(output / "candidates.json", replay.rows)
        write(output / "packages.json", rows)
    changed = [r for r in replay.rows if r["guard_before"] and not r["guard_after"]]
    removed = {
        (r["run_id"], r["variant"], *v)
        for r in changed
        if r["acceptance"] == "accepted"
        for v in r["removed_still_open"]
    }
    summary = {
        "packages": len(rows),
        "candidate_occurrences": len(replay.rows),
        "guard_conflicts_before": sum(r["guard_before"] for r in replay.rows),
        "guard_conflicts_after": sum(r["guard_after"] for r in replay.rows),
        "formerly_blocked_proposals_now_eligible": len(changed),
        "packages_with_eligible_proposal": len(
            {(r["run_id"], r["variant"]) for r in changed}
        ),
        "acceptance_after_guard_clearance": dict(
            Counter(r["acceptance"] for r in changed)
        ),
        "guard_only_resolvable_open_findings": len(removed),
        "reconstruction": dict(Counter(r["security_reconstruction"] for r in rows)),
        "limitation": (
            "Paired recorded/reconstructable proposals only. "
            "Rejected Fixer bodies are absent. No cumulative pipeline, pass rate, "
            "real rerun or deployment claim."
        ),
    }
    write(output / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshots", type=Path, default=ROOT / ".cache/broad-final-results"
    )
    parser.add_argument(
        "--cache", type=Path, default=ROOT / ".cache/phase10c-observations"
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
