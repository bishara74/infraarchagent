"""Collect requirement links and disclose manual verification gaps."""

import argparse
import json
import re
from pathlib import Path

from scripts.phase9_common import ROOT, write_json
from scripts.traceability import build_report, collect, identifiers

EVIDENCE = {
    "PR-01": [
        "phase9-bench-real-20261020T010134093069Z",
        "phase9-bench-real-20261020T013911945957Z",
    ],
    "PR-03": [
        "phase9-bench-real-20261020T010134093069Z",
        "phase9-bench-real-20261020T013911945957Z",
    ],
    "PR-04": ["phase9-bench-stub-20261019T154457135290Z", "phase9b-download-quiet"],
    "PR-05": [
        "phase9-bench-real-20261020T010134093069Z",
        "phase9-bench-real-20261020T013911945957Z",
    ],
}


def render(report: dict, evidence: dict[str, list[str]]) -> str:
    lines = [
        "# Requirement traceability",
        "",
        (
            "Collection proves linkage, not test success or requirement "
            "satisfaction. Actual verification results are recorded separately"
            " in IMPLEMENTATION_LOG.md."
        ),
        "",
        "| ID | Linked tests | Performance evidence |",
        "|---|---|---|",
    ]
    for row in report["requirements"]:
        tests = sorted(
            {
                f"[{test['node_id']}]"
                f"({('../../../' + test['file']).replace(' ', '%20')})"
                for test in row["tests"]
            }
        )
        folders = evidence.get(row["requirement"], [])
        lines.append(
            f"| {row['requirement']} | "
            + "<br>".join(tests or ["UNLINKED"])
            + " | "
            + ", ".join(f"[{name}](../{name}/)" for name in folders)
            + " |"
        )
    lines += [
        "",
        "Unlinked requirements: " + (", ".join(report["uncovered"]) or "none"),
        "Collection failures: "
        + (", ".join(report.get("collection_failures", [])) or "none"),
        "",
        "## Manual verification and remaining gaps",
        "",
        (
            "NFR-02 requires replacing each agent without editing peers or the"
            " orchestrator. The six role-swap cases exercise contract "
            "dispatch, persistence and settlement through existing injection "
            "seams. Review the Architect parse_input/generate_plan, Generator "
            "generate(plan), SecurityStage.run and ValidationStage.run "
            "contracts against docs/spec/04-design.tex. Check that replacement"
            " implementations retain the documented error/output contracts and"
            " require no peer edits. Production recovery uses concrete-class "
            "checks, generator.last_run and private _last_run mutation; the "
            "contract-double tests do not establish unrestricted "
            "replaceability of those recovery/telemetry paths. This coupling "
            "remains an explicit architectural limitation; no broad refactor "
            "is included in Phase 9b."
        ),
        "",
        (
            "NFR-04 remains unlinked/unverified: manually provision a clean "
            "Ubuntu 24 environment using author-installed prerequisites, run "
            "the full stack and a stub pipeline, and exercise the UI in "
            "supported browsers without plugins. This session performs no "
            "installs/downloads. The spec's tfsec prerequisite is superseded "
            "by accepted D-31 Trivy usage; record actual versions and "
            "outcomes. Local tests are not a clean-deployment proof."
        ),
        "",
        (
            "PR-01 uses API settlement as the documented D-43 proxy for UI "
            "availability; PR-02 measures UI emission-to-DOM separately. PR-03"
            " and PR-04 failures remain failures. An annotation, stub timing "
            "or isolated PR-05 pass is not a real-provider or concurrent-"
            "workload compliance claim."
        ),
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    source = re.sub(
        r"(?<!\\)%[^\n]*", "", (ROOT / "docs/spec/03-requirements.tex").read_text()
    )
    tests, failures = collect(args.output_dir)
    report = build_report(
        identifiers(source),
        tests,
        json.loads((ROOT / "docs/traceability-map.json").read_text()),
    )
    report["collection_failures"] = failures
    evidence = dict(EVIDENCE)
    evidence["PR-02"] = sorted(
        p.name for p in (ROOT / "docs/evals").glob("phase9-pr02-*")
    )
    write_json(args.output_dir / "traceability.json", report)
    (args.output_dir / "traceability.md").write_text(render(report, evidence))
    print(
        f"Traceability: {len(report['requirements'])} requirements; "
        f"{len(report['uncovered'])} unlinked; {len(failures)} collection failures"
    )
    if failures or report["invalid_annotations"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
