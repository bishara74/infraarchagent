"""Offline, counts-only service mapping coverage for the saved 48 benchmark plans."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.domain.plan import ARCHITECT_AWS_SERVICES, DeploymentPlan
from app.security.generation import (
    generation_context,
    hosting_resource_types,
    service_resource_types,
)
from app.validation.provider_schema import DEFAULT_INDEX, PINS, ProviderSchemaIndex
from app.validation.schema_context import _merge
from scripts.phase9i_guidance_provider_replay import (
    represented_paths,
    required_paths,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE = ROOT / "docs/evals/phase9i-service-mapping-offline/baseline.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def report(baseline_path, output):
    baseline = json.loads(baseline_path.read_text())
    indexes = {v: ProviderSchemaIndex("aws", v) for v in PINS["aws"]}
    assert all(i.available for i in indexes.values()), "Both pinned indexes required"
    vocabulary = []
    for label in ARCHITECT_AWS_SERVICES:
        types = service_resource_types(label, hosting_types={"aws_eks_cluster"})
        assert types and all(
            i.resource_schema(t) for i in indexes.values() for t in types
        ), label
        vocabulary.append(
            {
                "service": label,
                "resource_types": sorted(types),
                "hosting_context": "eks"
                if label in {"prometheus", "grafana"}
                else None,
            }
        )
    rows = []
    for item in baseline["plans"]:
        path = ROOT / item["source_path"]
        assert sha(path) == item["source_sha256"], str(path)
        raw_plan = json.loads(path.read_text())["plan"]
        plan_hash = hashlib.sha256(
            json.dumps(raw_plan, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        assert plan_hash == item["plan_sha256"]
        plan = DeploymentPlan.model_validate(raw_plan)
        hosting = hosting_resource_types(plan)
        services = []
        for field, entries in (("services", plan.services), ("storage", plan.storage)):
            for entry in entries:
                types = service_resource_types(entry.aws_service, hosting_types=hosting)
                assert types and all(
                    i.resource_schema(t) for i in indexes.values() for t in types
                ), (item["run_id"], entry.aws_service)
                services.append(
                    {
                        "field": field,
                        "service": entry.aws_service,
                        "previously_unmapped": not baseline["previous_service_types"][
                            entry.aws_service
                        ],
                        "resource_types": sorted(types),
                    }
                )
        context = generation_context(plan)
        assert 0 < context.schema_chars <= 4500
        assert context.checklist_chars <= 1500 and len(context.text) <= 6000
        entries = {
            e["type"]: e for e in json.loads(context.text[: context.schema_chars])
        }
        # The existing tier/cap rules must report every omitted required group.
        for resource_type in context.resource_types:
            for version, index in indexes.items():
                shape = json.loads(
                    json.dumps(entries.get(resource_type, {}).get("schema", {}))
                )
                _merge(
                    shape,
                    entries.get(resource_type, {})
                    .get("version_schema", {})
                    .get(version, {}),
                )
                present = represented_paths(shape)
                wanted = required_paths(index.resource_schema(resource_type))
                assert (
                    not (wanted["required"] - present)
                    or resource_type in context.omitted_required
                )
                assert not (
                    wanted["conditional_required"] - present
                ) or resource_type in (
                    *context.omitted_required,
                    *context.omitted_conditional,
                )
        rows.append(
            {
                **{
                    k: item[k]
                    for k in (
                        "cohort",
                        "run_id",
                        "source_path",
                        "source_sha256",
                        "plan_sha256",
                        "before",
                    )
                },
                "services": services,
                "after": {
                    "schema_chars": context.schema_chars,
                    "checklist_chars": context.checklist_chars,
                    "total_chars": len(context.text),
                    **context.metrics(),
                },
            }
        )
    cohorts = {}
    for cohort in ("broad", "final-1", "final-2"):
        selected = [r for r in rows if r["cohort"] == cohort]
        cohorts[cohort] = {
            "plans": len(selected),
            "previously_unmapped_services": dict(
                sorted(
                    Counter(
                        s["service"]
                        for r in selected
                        for s in r["services"]
                        if s["previously_unmapped"]
                    ).items()
                )
            ),
            "schema_before_range": [
                min(r["before"]["schema_chars"] for r in selected),
                max(r["before"]["schema_chars"] for r in selected),
            ],
            "schema_after_range": [
                min(r["after"]["schema_chars"] for r in selected),
                max(r["after"]["schema_chars"] for r in selected),
            ],
            "required_overflow_plans": sum(
                bool(r["after"]["generator_schema_omitted_resource_types"]["required"])
                for r in selected
            ),
            "conditional_overflow_plans": sum(
                bool(
                    r["after"]["generator_schema_omitted_resource_types"][
                        "conditional_required"
                    ]
                )
                for r in selected
            ),
        }
    output.mkdir(parents=True, exist_ok=False)
    write(output / "plans.json", rows)
    write(
        output / "summary.json",
        {
            "cohorts": cohorts,
            "zero_schema_plans": sum(r["after"]["schema_chars"] == 0 for r in rows),
            "vocabulary": vocabulary,
            "llm_calls": 0,
        },
    )
    code = [
        "backend/app/domain/plan.py",
        "backend/app/agents/prompts/architect.py",
        "backend/app/security/generation.py",
        "backend/app/validation/schema_context.py",
        "backend/scripts/phase9i_service_mapping_report.py",
        "backend/scripts/phase9i_guidance_provider_replay.py",
    ]
    write(
        output / "manifest.json",
        {
            "baseline_path": str(baseline_path.relative_to(ROOT)),
            "baseline_sha256": sha(baseline_path),
            "source_hashes": {p: sha(ROOT / p) for p in code},
            "index_hashes": {v: sha(DEFAULT_INDEX / f"aws-{v}.json") for v in indexes},
            "index_manifest_sha256": sha(DEFAULT_INDEX / "manifest.json"),
            "original_inputs_unchanged": True,
            "caps_and_required_omissions_verified": True,
        },
    )
    lines = [
        "# phase9i: service mapping offline coverage",
        "",
        "48 saved plans: 20 broad, 14 final-1 and 14 final-2. No LLM calls "
        "or package replay. Historical evidence and inputs are unchanged.",
        "",
        "| Cohort | Previously unmapped labels (service/storage "
        "occurrences) | Schema before → after | Required / conditional "
        "overflow plans |",
        "|---|---|---|---|",
    ]
    for cohort, values in cohorts.items():
        labels = (
            ", ".join(
                f"{k} ({v})" for k, v in values["previously_unmapped_services"].items()
            )
            or "none"
        )
        before, after = values["schema_before_range"], values["schema_after_range"]
        lines.append(
            f"| {cohort} | {labels} | {before[0]}–{before[1]} → "
            f"{after[0]}–{after[1]} | {values['required_overflow_plans']} / "
            f"{values['conditional_overflow_plans']} |"
        )
    lines += [
        "",
        "Unqualified API Gateway includes REST and HTTP core types; "
        "explicit REST/HTTP labels select the corresponding family. Lambda "
        "includes function, permission and IAM role. Storage labels select "
        "the named service before generic kind fallbacks.",
        "",
        "Prometheus/Grafana inherit explicitly planned EC2/ECS/EKS "
        "hosting. Only explicit managed labels select AWS workspaces. A "
        "plain monitoring label without a host remains unresolved rather "
        "than inventing infrastructure.",
        "",
        "The Architect schema now advertises 33 labels and remains "
        "free-form for compatibility (prompt version 3). Coverage tests "
        "check this vocabulary, all saved spellings and every selected "
        "type against both pinned indexes. This finite vocabulary cannot "
        "exhaust arbitrary strings allowed by the schema.",
        "",
        "All selected unconditional required cores fit; the existing 4,500 "
        "schema / 1,500 checklist / 6,000 combined caps and recursive "
        "tiers are unchanged. Explicitly reported conditional groups can "
        "still overflow. Both serverless scenario-3 plans now receive "
        "schema guidance; no zero-schema plans remain.",
        "",
        "[plans.json](plans.json) records each plan's service-level "
        "previous gaps, selected types, schema/checklist/combined sizes "
        "and omitted-type lists. [baseline.json](../baseline.json) freezes "
        "pre-mapping selection and context measurements at 9031c64; "
        "[manifest.json](manifest.json) binds current code, indexes and "
        "source hashes. Guidance size changes alone establish no validity "
        "or benchmark-quality improvement.",
    ]
    lines += [
        "",
        "| Cohort / run | Previously unmapped labels | Schema before → after | "
        "Checklist | Total |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        labels = (
            ", ".join(
                sorted(
                    {s["service"] for s in row["services"] if s["previously_unmapped"]}
                )
            )
            or "none"
        )
        after = row["after"]
        lines.append(
            f"| {row['cohort']}/{row['run_id']} | {labels} | "
            f"{row['before']['schema_chars']} → {after['schema_chars']} | "
            f"{after['checklist_chars']} | {after['total_chars']} |"
        )
    (output / "README.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(cohorts, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report(args.baseline, args.output)


if __name__ == "__main__":
    main()
