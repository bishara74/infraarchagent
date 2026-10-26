"""Offline spec-alignment inventory and rates from committed real evidence only."""

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATOR_CORPORA = (
    "docs/evals/phase3-generators-20260930T045713473558Z",
    "docs/evals/phase3-generators-20260930T060923179316Z",
)
FIRST_SCAN = "docs/evals/phase5b-security-20261001T191131076470Z/results.json"


def committed(path: str, inputs: dict) -> bytes:
    data = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
    inputs[path] = hashlib.sha256(data).hexdigest()
    return data


def measure() -> dict:
    inputs, rows = {}, []
    for corpus in GENERATOR_CORPORA:
        cases = json.loads(committed(f"{corpus}/results.json", inputs))["cases"]
        names = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", f"{corpus}/packages"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        for case in cases:
            if not case["success"] or case["model"] == "stub":
                continue
            variant, plan = case["variant"], case["plan"]
            paths = [p for p in names if f"/{plan}/{variant}/" in p]
            sources = {p: committed(p, inputs).decode() for p in paths}
            contents = "\n".join(
                value
                for path, value in sources.items()
                if path.endswith((".tf", ".tf.json"))
            )
            workload = "\n".join(
                value
                for path, value in sources.items()
                if path.endswith((".tf", ".tf.json", ".yml", ".yaml"))
            )
            classes = re.findall(
                r'\b(?:instance_type|instance_class)\s*=\s*"([^"\n]+)"', contents
            )
            row = {
                "corpus": corpus,
                "model": case["model"],
                "plan": plan,
                "variant": variant,
                "literal_instance_classes": classes,
                "micro_literal_present": any(c.endswith(".micro") for c in classes),
                "literal_multi_az": bool(
                    re.search(r"\bmulti_az\s*=\s*true\b", contents)
                ),
                "autoscaling_declared": bool(
                    re.search(
                        r'resource\s+"aws_(?:autoscaling_group|appautoscaling_target)"|kind:\s*HorizontalPodAutoscaler',
                        workload,
                    )
                ),
                "stored_directive_checks": case.get("checks", []),
            }
            rows.append(row)
    first = json.loads(committed(FIRST_SCAN, inputs))
    security = [row for row in first["cases"] if row["variant"] == "security"]
    costs = [row for row in rows if row["variant"] == "cost"]
    performance = [row for row in rows if row["variant"] == "performance"]
    return {
        "method": (
            "Literal source observations, not deployment or Free Tier "
            "eligibility proof; original real generator corpus, "
            "not later retained packages."
        ),
        "inputs": inputs,
        "packages": rows,
        "rates": {
            "cost_micro_literal": {
                "numerator": sum(row["micro_literal_present"] for row in costs),
                "denominator": len(costs),
                "no_literal_class": sum(
                    not row["literal_instance_classes"] for row in costs
                ),
            },
            "performance_literal_multi_az": {
                "numerator": sum(row["literal_multi_az"] for row in performance),
                "denominator": len(performance),
            },
            "performance_autoscaling": {
                "numerator": sum(row["autoscaling_declared"] for row in performance),
                "denominator": len(performance),
            },
            "performance_both": {
                "numerator": sum(
                    row["literal_multi_az"] and row["autoscaling_declared"]
                    for row in performance
                ),
                "denominator": len(performance),
            },
            "security_zero_first_checkov_high_or_critical": {
                "numerator": sum(
                    row.get("first_scan_checkov_high_or_critical") == 0
                    for row in security
                ),
                "denominator": sum(
                    isinstance(row.get("first_scan_checkov_high_or_critical"), int)
                    for row in security
                ),
                "unknown": sum(
                    not isinstance(row.get("first_scan_checkov_high_or_critical"), int)
                    for row in security
                ),
            },
        },
        "first_scan_security": [
            {
                "model": row["generator_model"],
                "plan": row.get("plan", row.get("scenario")),
                "high_or_critical": row.get("first_scan_checkov_high_or_critical"),
            }
            for row in security
        ],
    }


def inventory() -> tuple[list[tuple[str, str, str]], list[str]]:
    endpoints = []
    for source in sorted((ROOT / "backend/app/api").glob("*.py")):
        tree = ast.parse(source.read_text())
        prefix = ""
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "APIRouter"
            ):
                for item in node.keywords:
                    if item.arg == "prefix" and isinstance(item.value, ast.Constant):
                        prefix = item.value.value
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Attribute)
                    and decorator.func.attr in {"get", "post", "put", "delete", "patch"}
                    and decorator.args
                    and isinstance(decorator.args[0], ast.Constant)
                ):
                    path = prefix + decorator.args[0].value
                    if path.startswith("/api/"):
                        endpoints.append(
                            (decorator.func.attr.upper(), path, source.stem)
                        )
    tables = re.findall(
        r'__tablename__\s*=\s*"([^"]+)"',
        (ROOT / "backend/app/db/models.py").read_text(),
    )
    return sorted(endpoints), tables


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = measure()
    (args.output / "generator-rates.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    endpoints, tables = inventory()
    deviations = {
        "auth": "D-49/D-50/D-58",
        "providers": "D-51",
        "models": "D-52/D-58",
        "preferences": "D-53",
        "benchmark": "D-43/D-59",
        "lessons": "D-60",
        "review_history": "D-58/D-60",
        "health": "D-35/D-61",
    }
    lines = [
        "# Final API and data-model inventory",
        "",
        "Static source inventory; framework documentation/static routes are excluded.",
        "",
        f"{len(endpoints)} method/path definitions versus the chapter's "
        "four REST endpoints and one SSE stream.",
        "",
        "| Method | Endpoint | Introducing / extending deviation |",
        "|---|---|---|",
    ]
    for method, path, module in endpoints:
        deviation = deviations.get(
            module,
            "D-58"
            if path.endswith("download-all")
            else "Original interface; D-18/D-37/D-47 extend contracts",
        )
        lines.append(f"| {method} | `{path}` | {deviation} |")
    lines += [
        "",
        f"{len(tables)} application tables versus the original three. "
        "Alembic's revision table is migration metadata.",
        "",
        "| Table | Introducing deviation |",
        "|---|---|",
    ]
    for table in tables:
        deviation = (
            "Original model; D-01–06/D-23/D-38/D-47/D-48 extend columns"
            if table in {"pipeline_runs", "generated_packages", "agent_events"}
            else "D-49"
            if table == "auth_sessions"
            else "D-50"
            if table == "users"
            else "D-51/D-52"
            if table in {"provider_credentials", "llm_settings"}
            else "D-53"
            if table.startswith("user_")
            else "D-60; Phase 10 additive provenance migration 0015"
        )
        lines.append(f"| `{table}` | {deviation} |")
    (args.output / "api-and-tables.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(report["rates"], indent=2))


if __name__ == "__main__":
    main()
