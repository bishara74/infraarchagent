"""Render the reviewed requirement statuses; collection never determines status."""

import json
from collections import Counter
from pathlib import Path

from scripts.traceability import identifiers

ROOT = Path(__file__).resolve().parents[2]
STATUSES = {"met", "partly met", "not met", "unverified"}


def validate(data: dict, requirements: set[str], root: Path) -> None:
    rows = data["rows"]
    if {row["id"] for row in rows} != requirements or len(rows) != len(requirements):
        raise ValueError("Evidence index must cover each specification ID exactly once")
    for row in rows:
        if row["status"] not in STATUSES or not row["finding"] or not row["evidence"]:
            raise ValueError("Every status needs a finding and evidence")
        for value in row["evidence"]:
            path = (root / value).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError(
                    "Evidence paths must identify existing repository files"
                )
    by_id = {row["id"]: row for row in rows}
    if by_id["PR-03"]["status"] != "not met" and not data.get("approved_pr03_target"):
        raise ValueError("PR-03 cannot pass without approved revised-target evidence")
    if by_id["NFR-04"]["status"] != "unverified" and not data.get(
        "author_clean_deployment_evidence"
    ):
        raise ValueError("NFR-04 needs committed author clean-deployment evidence")


def render(data: dict) -> str:
    counts = Counter(row["status"] for row in data["rows"])
    deployment = next(row for row in data["rows"] if row["id"] == "NFR-04")
    deployment_links = ", ".join(
        f"[{Path(path).name}](../../{path})" for path in deployment["evidence"]
    )
    lines = [
        "# Requirement evidence index",
        "",
        "; ".join(
            f"**{counts[status]} {status}**"
            for status in ("met", "partly met", "not met", "unverified")
        )
        + f" — {len(data['rows'])} specification requirements/use cases.",
        "",
        data["scope"],
        "",
        (
            "Execution results: [Phase 10b verification]"
            "(phase10b-verification/README.md); prior [Phase 10 verification]"
            "(phase10-verification/README.md). "
            "Test linkage: [three-framework collection]"
            "(phase10b-traceability/traceability.md), "
            "[TC mapping](../requirement-test-map.md). "
            "An annotation or collection count is not a passing test "
            "or a status decision."
        ),
        "",
        "| ID | Status | Test types | Evidence | Deviations / qualification |",
        "|---|---|---|---|---|",
    ]
    for row in data["rows"]:
        links = ", ".join(
            f"[{Path(path).name}](../../{path})" for path in row["evidence"]
        )
        detail = (
            ", ".join(row["deviations"])
            + ("; " if row["deviations"] else "")
            + row["finding"]
        )
        lines.append(
            f"| {row['id']} | {row['status']} | "
            f"{', '.join(row['test_types'])} | {links} | {detail} |"
        )
    lines += [
        "",
        (
            "PR-03 uses the existing ≤1.5× isolated-baseline target; "
            "its draft revision is unapproved. "
            f"NFR-04: **{deployment['status']}** — {deployment['finding']} "
            f"Evidence: {deployment_links}. "
            "Proposed additions are [awaiting author/supervisor approval]"
            "(../phase10-proposed-requirements.md) and do not enter these counts."
        ),
        "",
        (
            "Statuses are reviewed findings in [the machine-readable register]"
            "(phase10-requirements.json); reproduce with "
            "`cd backend && .venv/bin/python -m scripts.phase10_evidence`. "
            "Performance evidence is revision/cohort-specific. "
            "No static or human label proves cloud deployment."
        ),
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    data = json.loads((ROOT / "docs/evals/phase10-requirements.json").read_text())
    requirements = identifiers((ROOT / "docs/spec/03-requirements.tex").read_text())
    validate(data, requirements, ROOT)
    (ROOT / "docs/evals/EVIDENCE.md").write_text(render(data))
    print(dict(Counter(row["status"] for row in data["rows"])))


if __name__ == "__main__":
    main()
