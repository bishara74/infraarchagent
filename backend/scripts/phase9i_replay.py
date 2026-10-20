"""Immutable, offline Phase 9i observations. Never instantiate operator settings."""

import argparse
import asyncio
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.scanners.runner import ProcessToolRunner
from app.scanners.scan import Scanner
from app.security.generation import generation_context
from app.security.profiles import assess
from app.validation.engine import ValidationEngine
from app.validation.tools import report_versions

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


def code_fingerprint() -> str:
    paths = [
        *(ROOT / "backend/app/validation").glob("*.py"),
        *(ROOT / "backend/app/scanners").glob("*.py"),
        ROOT / "backend/app/security/policy.py",
        ROOT / "backend/app/domain/validation.py",
    ]
    return digest(
        {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths)
        }
    )


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
        "profiles": assess(package),
    }


class Observer:
    def __init__(self, cache: Path):
        self.cache = cache
        self.versions = report_versions()
        self.evaluator = code_fingerprint()

    async def observe(
        self, item: dict[str, Any], files: dict[str, str]
    ) -> dict[str, Any]:
        key = digest(
            {
                "files": files,
                "plan": item["plan"],
                "variant": item["variant"],
                "versions": self.versions,
                "evaluator": self.evaluator,
                "protocol": 1,
                "tool_timeout": 60,
                "validation_deadline": 120,
            }
        )
        path = self.cache / f"{key}.json"
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
        return projection({**package, "files": files})


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache/phase9i-replay")
    args = parser.parse_args()
    asyncio.run(baseline(args.output, args.cache))


if __name__ == "__main__":
    main()
