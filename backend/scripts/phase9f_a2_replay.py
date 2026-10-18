"""Read-only A2 declaration replay and additional historical PR-05 workload views."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from app.validation.documents import PackageDocuments
from app.validation.references import reference_checks
from app.validation.repairs import repair_declarations
from app.validation.syntax import native_syntax
from app.validation.workspace import ValidationWorkspace
from scripts.benchmark import timings
from scripts.phase9_common import ROOT
from scripts.phase9f_workloads import pr05_workloads


def variable_failures(files):
    return [
        c
        for c in reference_checks(PackageDocuments.parse(files))
        if c.check_id == "terraform.var_ref" and c.status == "failed"
    ]


async def replay(directory: Path, benchmark: Path) -> dict:
    inputs = sorted(directory.glob("*.json"))
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    cases = []
    for path in inputs:
        run = json.loads(path.read_bytes())
        for package in run["packages"]:
            workspace = ValidationWorkspace()
            try:
                with workspace.activate():
                    before = variable_failures(package["files"])
                    if not before:
                        continue
                    _, original_actions = await repair_declarations(
                        package["original_files"]
                    )
                    repaired, records = await repair_declarations(package["files"])
                    cases.append(
                        {
                            "run_id": path.stem,
                            "variant": package["variant"],
                            "checkpoint": "saved parsable final files; no model replay",
                            "original_declaration_actions": len(original_actions),
                            "before_variable_failures": len(before),
                            "added_declarations": sum(
                                r["kind"] == "missing_variable" for r in records
                            ),
                            "after_variable_failures": len(variable_failures(repaired)),
                            "native_syntax_errors": len(await native_syntax(repaired)),
                            "idempotent": await repair_declarations(repaired)
                            == (repaired, []),
                        }
                    )
            finally:
                workspace.close()
    results = json.loads((benchmark / "results.json").read_bytes())
    events = json.loads((benchmark / "events.json").read_bytes())
    agents = [
        row
        for run in results["runs"]
        for row in timings(
            run["run_id"], [e for e in events if e["run_id"] == run["run_id"]]
        )
    ]
    return {
        "mode": "offline_native_no_llm",
        "input_hashes": hashes,
        "input_files_unchanged": all(
            hashlib.sha256(p.read_bytes()).hexdigest() == hashes[p.name] for p in inputs
        ),
        "cases": cases,
        "variable_failures_before": sum(c["before_variable_failures"] for c in cases),
        "variable_failures_after": sum(c["after_variable_failures"] for c in cases),
        "pr05_workloads": pr05_workloads(results["runs"], agents),
        "aggregate_pr05": "FAIL"
        if any(
            r.get("pass") is False
            for r in agents
            if r.get("threshold_seconds") is not None
        )
        else "PASS",
        "readiness_recomputed": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=ROOT / ".cache/phase9f-a2-results"
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=ROOT / "docs/evals/phase9-bench-real-20261018T163731511036Z",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = asyncio.run(replay(args.input, args.benchmark))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"input_hashes", "cases", "pr05_workloads"}
            }
        )
    )


if __name__ == "__main__":
    main()
