"""Verify Phase 9i byte provenance and publish source-free replay comparisons."""

import argparse
import ast
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

from app.domain.plan import DeploymentPlan
from app.security.generation import generation_context
from app.security.profiles import assess
from app.validation.schema_context import schema_context
from scripts.phase9i_replay import (
    CHANGES,
    EVIDENCE,
    ROOT,
    SETS,
    aggregate,
    code_fingerprint,
    digest,
    fingerprints,
    inventory,
    reassess,
)

PROFILES = ("strict", "contextual-v1", "contextual-v2")
BASELINE_COMMIT = "e133ef6"


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def proposal(name: str, files: dict[str, str], observation: dict[str, Any]):
    if name not in {"addressing", "defaults"}:
        return CHANGES[name](files)
    rules = (
        {"CKV_AWS_130", "AWS-0164"}
        if name == "addressing"
        else {"AWS-0077", "CKV2_AWS_12"}
    )
    targets = {
        (str(Path(f["file_path"]).parent), f["resource"].split("[", 1)[0])
        for f in observation["blockers"]
        if f["rule_id"] in rules
    }
    return CHANGES[name](files, targets)


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    old, new = fingerprints(before), fingerprints(after)
    known = all(o.get("scan_outcome", "clean") != "unknown" for o in (before, after))
    if not known:
        old, new = set(), set()

    def blocker_delta(name: str) -> int | None:
        old_count = before["profiles"][name]["remaining_blocking"]
        new_count = after["profiles"][name]["remaining_blocking"]
        return (
            new_count - old_count
            if known and type(old_count) is int and type(new_count) is int
            else None
        )

    return {
        "validation_changed": before["validation"] != after["validation"],
        "failed_checks_before": len(before["failed_checks"]),
        "failed_checks_after": len(after["failed_checks"]),
        "removed": sorted(old - new),
        "introduced": sorted(new - old),
        "blocker_deltas": {name: blocker_delta(name) for name in PROFILES},
    }


def prompt_labels() -> dict[str, str]:
    # Reporting labels come from the recorded benchmark schedule, never from
    # prompt text or repair heuristics. PR-05 uses the complex ECS prompt.
    labels = {}
    for number, name in enumerate(SETS, 1):
        for run in read(ROOT / "docs/evals" / name / "results.json")["runs"]:
            label = {0: "ECS", 1: "EKS", 2: "static"}.get(
                run.get("prompt_index"), "ECS"
            )
            labels[f"{number}/{run['run_id']}"] = label
    return labels


def legacy_context():
    """Reconstruct coverage with the frozen pre-repair code, never snapshots' text."""
    modules = {}
    for name, path in (
        ("schema", "validation/schema_context.py"),
        ("catalogue", "security/catalogue.py"),
        ("generation", "security/generation.py"),
    ):
        source = subprocess.run(
            ["git", "show", f"{BASELINE_COMMIT}:backend/app/{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        module = ModuleType("phase9i_baseline_" + name)
        sys.modules[module.__name__] = module
        exec(compile(source, f"{BASELINE_COMMIT}:{path}", "exec"), module.__dict__)
        modules[name] = module
    modules["generation"].generator_schema_context = modules[
        "schema"
    ].generator_schema_context
    modules["generation"].guidance = modules["catalogue"].guidance
    return modules["generation"].generation_context, modules["schema"].schema_context


def select_before_context(frozen, legacy, current):
    def sizes(context):
        return (
            context.schema_chars,
            context.checklist_chars,
            len(context.text),
            context.truncated,
        )

    expected = tuple(frozen[k] for k in ("schema", "checklist", "total", "truncated"))
    if sizes(legacy) == expected:
        return legacy, BASELINE_COMMIT
    if sizes(current) == expected:
        return current, "captured-current-guidance"
    raise ValueError("baseline guidance cannot be reconstructed")


def verify_and_report(output: Path) -> dict[str, Any]:
    packages, manifest = inventory()
    assert manifest == read(output / "input-manifest.json"), "historical input changed"
    execution_manifest = read(output / "execution-evaluator-manifest.json")
    evaluator = digest(execution_manifest)
    changed = {
        p
        for p, fingerprint in execution_manifest.items()
        if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != fingerprint
    }
    # Only the secondary evaluator can change without fresh tool observations.
    # Its outputs are recomputed, never reused from a different fingerprint.
    assert changed <= {
        "backend/app/security/profiles_v2.py",
        "backend/app/validation/schema_context.py",
    }, changed
    guidance_proof = None
    schema_path = "backend/app/validation/schema_context.py"
    if schema_path in changed:
        old_source = subprocess.run(
            ["git", "show", "9d1ffe8:" + schema_path],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert (
            hashlib.sha256(old_source.encode()).hexdigest()
            == execution_manifest[schema_path]
        )

        def validator_ast(source):
            tree = ast.parse(source)
            tree.body = [
                n
                for n in tree.body
                if not (
                    isinstance(n, ast.FunctionDef)
                    and n.name == "generator_schema_context"
                )
            ]
            return ast.dump(tree, include_attributes=False)

        before_ast = validator_ast(old_source)
        assert before_ast == validator_ast((ROOT / schema_path).read_text())
        guidance_proof = {
            "source_commit": "9d1ffe8",
            "excluded_generation_function": "generator_schema_context",
            "unchanged_validator_ast_sha256": digest(before_ast),
        }
    assessment_evaluator = code_fingerprint()
    assessment_cache = {}
    original_context, original_repair_context = legacy_context()

    def final_observation(observation, files):
        key = digest(
            {
                "files": files,
                "validation": observation["validation"],
                "scan_outcome": observation["scan_outcome"],
                "blockers": observation["blockers"],
            }
        )
        if key not in assessment_cache:
            assessment_cache[key] = reassess(observation, files)["profiles"]
        profiles = assessment_cache[key]
        assert all(profiles[p] == observation["profiles"][p] for p in PROFILES[:2])
        return {**observation, "profiles": profiles}

    labels = prompt_labels()
    stage_names = ["schema_guidance", "contextual_v2"] + [
        f"{mode}_{name}" for name in CHANGES for mode in ("independent", "cumulative")
    ]
    stages: dict[str, list[dict[str, Any]]] = {name: [] for name in stage_names}
    historical, baseline, discrepancies, details, contexts = [], [], [], [], []
    idempotent = 0
    for item in packages:
        key = item["key"]
        filename = key.replace("/", "-") + ".json"
        frozen = read(output / "baseline" / filename)
        original = item["package"]["files"]
        initial_row = read(output / "schema_guidance" / filename)
        initial = final_observation(initial_row["observed"], original)
        legacy = assess(item["package"])
        assert all(
            legacy[p] == item["package"]["profile_assessments"][p] for p in PROFILES[:2]
        ), key
        stored = reassess(frozen["stored"], original)
        historical.append({"observed": stored})
        baseline.append({"observed": initial})
        for label, before in (
            ("historical", stored),
            ("prechange_offline", reassess(frozen["observed"], original)),
        ):
            delta = compare(before, initial)
            if before != initial:
                discrepancies.append(
                    {
                        "key": key,
                        "comparison": label,
                        "differing_fields": sorted(
                            k
                            for k in before.keys() | initial.keys()
                            if k != "profiles" and before.get(k) != initial.get(k)
                        ),
                        **delta,
                        "failed_checks_before": before["failed_checks"],
                        "failed_checks_after": initial["failed_checks"],
                    }
                )
        context = generation_context(DeploymentPlan.model_validate(item["plan"]))
        old_context, context_origin = select_before_context(
            frozen["context"],
            original_context(DeploymentPlan.model_validate(item["plan"])),
            context,
        )
        old_entries = json.loads(old_context.text[: old_context.schema_chars] or "[]")
        repair_contexts = []
        for path in sorted(p for p in original if p.endswith((".tf", ".tf.json"))):
            findings = [
                SimpleNamespace(**f)
                for f in initial["blockers"]
                if f["file_path"] == path
            ]
            kwargs = {
                "failures": initial["failed_checks"],
                "findings": findings,
                "limit": 16000,
            }
            old_repair = original_repair_context(path, original, **kwargs)
            new_repair = schema_context(path, original, **kwargs)

            def coverage(text):
                entries = json.loads(text or "[]")
                return {
                    "chars": len(text),
                    "sha256": digest(text),
                    "resource_types": sorted(
                        {e["type"] for e in entries if "type" in e}
                    ),
                    "truncated_entries": sum(bool(e.get("truncated")) for e in entries),
                }

            repair_contexts.append(
                {
                    "file": path,
                    "limit": 16000,
                    "mode": "offline schema preview; no LLM request",
                    "before": coverage(old_repair),
                    "after": coverage(new_repair),
                }
            )
        entries = json.loads(context.text[: context.schema_chars] or "[]")
        contexts.append(
            {
                "key": key,
                "plan_sha256": digest(item["plan"]),
                "before": {
                    **frozen["context"],
                    "included_resource_types": sorted({e["type"] for e in old_entries}),
                    "schema_entries": old_entries,
                    "coverage_reconstructed_from_commit": context_origin,
                },
                "after": {
                    "schema": context.schema_chars,
                    "checklist": context.checklist_chars,
                    "total": len(context.text),
                    "truncated": context.truncated,
                    "requested_resource_types": context.resource_types,
                    "included_resource_types": sorted({e["type"] for e in entries}),
                    "truncated_resource_types": sorted(
                        {e["type"] for e in entries if e.get("truncated")}
                    ),
                    "schema_entries": entries,
                },
                "repair_schema_previews": repair_contexts,
            }
        )
        current = original
        for stage in stage_names:
            row = read(output / stage / filename)
            provenance = row["provenance"]
            assert provenance["evaluator_sha256"] == evaluator, (
                key,
                stage,
                "evaluator changed",
            )
            assert provenance["files_sha256"] == digest(original)
            assert provenance["plan_sha256"] == digest(item["plan"])
            assert (
                provenance["variant"] == item["variant"]
                and provenance["network_isolated"]
            )
            provenance["assessment_evaluator_sha256"] = assessment_evaluator
            provenance["secondary_assessment_recomputed"] = True
            if stage in {"schema_guidance", "contextual_v2"}:
                row["observed"] = final_observation(row["observed"], original)
                assert row["observed"] == initial
                write(output / stage / filename, row)
                stages[stage].append(row)
                continue
            mode, name = stage.split("_", 1)
            before_files = original if mode == "independent" else current
            candidate, _ = proposal(name, before_files, row["before"])
            retained = candidate if row["reason"] == "accepted" else before_files
            assert digest(before_files) == row["before_sha256"], (key, stage, "before")
            assert digest(candidate) == row["candidate_sha256"], (
                key,
                stage,
                "candidate",
            )
            assert digest(retained) == row["retained_sha256"], (key, stage, "retained")
            repeated, _ = proposal(name, candidate, row["candidate"])
            assert repeated == candidate, (key, stage, "not idempotent")
            idempotent += 1
            for observation, files in (
                ("before", before_files),
                ("candidate", candidate),
                ("observed", retained),
            ):
                row[observation] = final_observation(row[observation], files)
            for record in row["records"]:
                record.update(
                    kind=record.get("kind", record.get("control", name)),
                    outcome="accepted" if row["reason"] == "accepted" else "rejected",
                    rejection_reason=None
                    if row["reason"] == "accepted"
                    else row["reason"],
                    package_before_sha256=row["before_sha256"],
                    package_candidate_sha256=row["candidate_sha256"],
                )
            write(output / stage / filename, row)
            if mode == "cumulative":
                current = retained
            retained_delta = compare(row["before"], row["observed"])
            candidate_delta = compare(row["before"], row["candidate"])
            details.append(
                {
                    "key": key,
                    "prompt": labels[key.rsplit("/", 1)[0]],
                    "stage": stage,
                    "reason": row["reason"],
                    "before_validation": row["before"]["validation"],
                    "candidate_validation": row["candidate"]["validation"],
                    "retained_validation": row["observed"]["validation"],
                    "retained": retained_delta,
                    "candidate": candidate_delta,
                    "counts": {
                        p: {
                            o: row[o]["profiles"][p]["remaining_blocking"]
                            for o in ("before", "candidate", "observed")
                        }
                        for p in PROFILES
                    },
                }
            )
            stages[stage].append(row)
    summaries = {}
    for stage, rows in stages.items():
        comparisons = [d for d in details if d["stage"] == stage]
        summaries[stage] = {
            **aggregate(rows),
            "outcomes": dict(Counter(r["reason"] for r in rows)),
            "retained_removed": sum(len(d["retained"]["removed"]) for d in comparisons),
            "retained_introduced": sum(
                len(d["retained"]["introduced"]) for d in comparisons
            ),
            "candidate_removed": sum(
                len(d["candidate"]["removed"]) for d in comparisons
            ),
            "candidate_introduced": sum(
                len(d["candidate"]["introduced"]) for d in comparisons
            ),
            "failed_checks": sum(len(r["observed"]["failed_checks"]) for r in rows),
            "candidate_scan_unknown": sum(
                r.get("candidate", r["observed"])["scan_outcome"] == "unknown"
                for r in rows
            ),
            "candidate_terraform_unknown": sum(
                r.get("candidate", r["observed"])["terraform_unknown"] for r in rows
            ),
            "by_prompt": {
                label: aggregate(
                    [r for r in rows if labels[r["key"].rsplit("/", 1)[0]] == label]
                )
                for label in ("ECS", "EKS", "static")
            },
        }
    result = {
        "historical": aggregate(historical),
        "fresh_baseline": aggregate(baseline),
        "stages": summaries,
        "legacy_golden_packages": len(packages),
        "idempotence_checks": idempotent,
        "input_manifest_unchanged": True,
        "evaluator_sha256": evaluator,
        "assessment_evaluator_sha256": assessment_evaluator,
        "non_tool_changed_paths": sorted(changed),
        "guidance_only_change_proof": guidance_proof,
        "llm_calls": 0,
    }
    write(output / "verified-summary.json", result)
    write(output / "baseline-discrepancies.json", discrepancies)
    write(output / "per-package-deltas.json", details)
    write(output / "context-sizes.json", contexts)
    with (output / "per-package.csv").open("w") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "package",
                "prompt",
                "stage",
                "outcome",
                "valid_before",
                "valid_candidate",
                "valid_retained",
                "failed_before",
                "failed_candidate",
                "failed_retained",
                *[p + "_delta" for p in PROFILES],
                *[
                    p + "_" + o
                    for p in PROFILES
                    for o in ("before", "candidate", "retained")
                ],
                "removed_retained",
                "introduced_retained",
                "introduced_candidate",
            ]
        )
        for d in details:
            writer.writerow(
                [
                    d["key"],
                    d["prompt"],
                    d["stage"],
                    d["reason"],
                    d["before_validation"],
                    d["candidate_validation"],
                    d["retained_validation"],
                    d["retained"]["failed_checks_before"],
                    d["candidate"]["failed_checks_after"],
                    d["retained"]["failed_checks_after"],
                    *d["retained"]["blocker_deltas"].values(),
                    *[
                        d["counts"][p][o]
                        for p in PROFILES
                        for o in ("before", "candidate", "observed")
                    ],
                    len(d["retained"]["removed"]),
                    len(d["retained"]["introduced"]),
                    len(d["candidate"]["introduced"]),
                ]
            )
    markdown(output, result, contexts, discrepancies)
    return result


def markdown(
    output: Path, result: dict[str, Any], contexts: list, discrepancies: list
) -> None:
    lines = [
        "# Phase 9i offline replay",
        "",
        (
            "81 generated packages from 28 runs; three missing variants "
            "remain separate in [the immutable "
            "manifest](input-manifest.json). Original final sets, cached "
            "snapshots and final report are unchanged. Zero LLM calls."
        ),
        "",
        (
            "Strict controls repair acceptance, readiness and downloads. "
            "Both contextual assessments are experimental reporting only; "
            "run-profile selection and persistence remain unchanged. All "
            "81 stored strict/v1 assessments match exactly."
        ),
        "",
        "## Retained outcomes",
        "",
        (
            "| Stage | Valid / 81 | Strict blockers | v1 blockers | v2 "
            "blockers | Strict / v1 / v2 passes |"
        ),
        "|---|---:|---:|---:|---:|---|",
    ]
    for stage, value in (
        ("Stored historical", result["historical"]),
        ("Fresh isolated baseline", result["fresh_baseline"]),
        *result["stages"].items(),
    ):
        p = value["profiles"]
        lines.append(
            f"| {stage} | {value['validation'].get('valid', 0)} | "
            + " | ".join(str(p[n]["blockers"]) for n in PROFILES)
            + " | "
            + " / ".join(str(p[n]["passes"]) for n in PROFILES)
            + " |"
        )
    lines += [
        "",
        (
            "The schema-guidance and contextual-v2 rows use original "
            "bytes. Guidance receives zero attributed package "
            "improvement. Any strict-to-v2 difference is policy "
            "classification, not an infrastructure security improvement. "
            "Independent changes start from original packages; cumulative "
            "changes retain the preceding accepted candidate."
        ),
        "",
        "## Candidates and guards",
        "",
        (
            "| Stage | Accepted | Unchanged | Rejected | Findings removed "
            "(retained) | New findings (candidate / retained) | Unknown "
            "scan outcomes |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for stage, value in result["stages"].items():
        if stage in {"schema_guidance", "contextual_v2"}:
            continue
        o = value["outcomes"]
        lines.append(
            f"| {stage} | {o.get('accepted', 0)} | {o.get('unchanged', 0)} | "
            f"{81 - o.get('accepted', 0) - o.get('unchanged', 0)} | "
            f"{value['retained_removed']} | {value['candidate_introduced']} / "
            f"{value['retained_introduced']} | {value['scan_unknown']} |"
        )
    lines += [
        "",
        (
            "Each stage directory preserves every "
            "before/candidate/retained assessment, failed check, blocker, "
            "exception, rejection reason, repair record and byte hash. "
            "[Per-package deltas](per-package-deltas.json) include "
            "rejected candidates; [CSV](per-package.csv) supports "
            "comparisons. Finding identity is rule, package-relative file "
            "and resource; duplicate counts remain in assessment totals. "
            "No candidate with new strict blockers is retained."
        ),
        "",
        "## Context measurements",
        "",
        "| Component | Before min–max | After min–max |",
        "|---|---:|---:|",
    ]
    for field in ("schema", "checklist", "total"):
        old = [r["before"][field] for r in contexts]
        new = [r["after"][field] for r in contexts]
        lines.append(
            f"| {field} characters | {min(old)}–{max(old)} | {min(new)}–{max(new)} |"
        )
    lines += [
        "",
        (
            f"Truncated context: "
            f"{sum(r['before']['truncated'] for r in contexts)}/81 before; "
            f"{sum(r['after']['truncated'] for r in contexts)}/81 after. "
            f"[Every saved plan's sizes and resource "
            f"coverage](context-sizes.json) include requested/included "
            f"types and the exact source-free schema entries. Caps remain "
            f"4,500 schema / 1,500 checklist / 6,000 total characters; "
            f"configured repair-context cap is unchanged."
        ),
        "",
        "## Baseline and verification limits",
        "",
        (
            f"[Baseline discrepancies](baseline-discrepancies.json) "
            f"contain {len(discrepancies)} package/comparison records, "
            f"with check details and finding deltas. Stored historical "
            f"results, pre-change fresh offline results and "
            f"final-validator isolated results remain distinct. The "
            f"pre-change baseline used tool offline flags and dead "
            f"proxies; the final-validator baseline and all final "
            f"candidates also ran in a Linux user/network namespace "
            f"containing only loopback."
        ),
        "",
        (
            "Tool versions, provider schema manifest, evaluator hash, "
            "package/plan/variant hashes and timeout configuration are "
            "recorded with every final row. Cached observations require "
            "matching fingerprints; isolated and nonisolated caches "
            "cannot collide. Providers use only the local filesystem "
            "mirror; remote chart dependencies are not fetched; "
            "Checkov/Trivy updates, uploads and telemetry are disabled. "
            "Terraform validates configuration; nothing is planned "
            "against AWS or deployed. Offline replay does not measure "
            "live pipeline deadline success or LLM generation quality."
        ),
        "",
        (
            f"All {result['idempotence_checks']} independent/cumulative "
            f"transformations were reconstructed against the final "
            f"implementation, checked idempotent and matched to observed "
            f"candidate/retained hashes. Unknown expressions, external "
            f"modules, ambiguous references and resolver limits "
            f"(64/declaration, 1,024/module, 16 local levels) remain "
            f"conservative omissions."
        ),
        "",
        "## Security interpretation and deferred work",
        "",
        (
            "Documented argument equivalents and lossless Grafana/Helm "
            "repairs improve validity; they do not by themselves harden "
            "deployed infrastructure. Seven-day RDS retention improves "
            "recovery. Disabling inherited public addresses reduces "
            "accidental exposure only where consumers prove connectivity "
            "is preserved. Managing a proven-unused VPC default SG "
            "removes latent permissive defaults. Longer backups, explicit "
            "public-IP choices, live SG rules and unknown dependencies "
            "are preserved."
        ),
        "",
        (
            "Ranks 4, 6, 7 and 8 remain future work: workload/container "
            "hardening (including KSV-0125), compatible logging and "
            "log-destination controls, broader schema-grounded repair of "
            "unsupported security/availability intent, and architectural "
            "isolation. The main architectural option is CloudFront VPC "
            "origins to an internal ALB, supported by the mirrored AWS "
            "providers' aws_cloudfront_vpc_origin schemas. None is "
            "implemented or credited with reductions here. D-56 and "
            "thesis notes describe the remaining evidence limits."
        ),
        "",
    ]
    lines += [
        "## Final retained packages by prompt",
        "",
        "| Prompt | Packages | Valid | Strict / v1 / v2 blockers | Strict passes |",
        "|---|---:|---:|---|---:|",
    ]
    for label, value in result["stages"]["cumulative_defaults"]["by_prompt"].items():
        p = value["profiles"]
        counts = " / ".join(str(p[n]["blockers"]) for n in PROFILES)
        lines.append(
            f"| {label} | {value['packages']} | "
            f"{value['validation'].get('valid', 0)} | {counts} | "
            f"{p['strict']['passes']} |"
        )
    eq, address, formats, defaults = (
        result["stages"]["cumulative_" + n] for n in CHANGES
    )
    initial = result["fresh_baseline"]
    valid_gain = eq["validation"].get("valid", 0) - initial["validation"].get(
        "valid", 0
    )

    def accepted(stage):
        return stage["outcomes"].get("accepted", 0)

    format_records = [read(p) for p in (output / "cumulative_formats").glob("*.json")]
    envelopes = sum(
        r.get("kind") == "grafana_envelope"
        for row in format_records
        for r in row["records"]
    )
    rejected_envelopes = sum(
        r.get("kind") == "grafana_envelope"
        for row in format_records
        if row["reason"] != "accepted"
        for r in row["records"]
    )
    lines += [
        "",
        "## Approved rank outcomes and risk",
        "",
        "| Rank | Measured effect | Risk / security meaning |",
        "|---|---|---|",
        (
            f"| 1 | {accepted(eq)} equivalent candidates retained; "
            f"{valid_gain} more valid packages; {eq['retained_removed']} "
            f"strict findings removed | Low semantic risk for documented "
            f"equivalents. Validity gain; no hardening claim. Guidance "
            f"alone has no measured generation gain. |"
        ),
        (
            f"| 2 | {accepted(address)} packages retained addressing "
            f"changes; {address['retained_removed']} strict findings "
            f"removed | Connectivity risk requires complete parsed "
            f"consumer evidence. Explicit public IP overrides survive; "
            f"safer defaults reduce accidental future exposure. |"
        ),
        (
            f"| 3 | {accepted(formats)} format candidates retained; "
            f"{formats['outcomes'].get('new_blocking_findings', 0)} "
            f"rejected with {formats['candidate_introduced']} newly "
            f"observable strict findings; "
            f"{formats['outcomes'].get('no_improvement', 0)} rejected "
            f"without validity improvement | Standard helpers can expose "
            f"workload checks when charts render. No hardening claim; "
            f"guards preserve all rejected originals. |"
        ),
        (
            f"| 5 | {accepted(defaults)} default candidates retained; "
            f"{defaults['retained_removed']} strict findings removed | "
            f"Seven-day backups improve recovery. Unknown consumers "
            f"preserve connectivity. Empty default SG rules are tested "
            f"separately; this corpus supplies no safe default-SG "
            f"proposal. |"
        ),
        "",
        (
            f"Original-byte v2 reclassifies "
            f"{initial['profiles']['contextual-v2']['exceptions']} "
            f"strict findings, versus "
            f"{initial['profiles']['contextual-v1']['exceptions']} in "
            f"v1. After repairs, v2 reclassifies "
            f"{defaults['profiles']['contextual-v2']['exceptions']} "
            f"residual strict findings, versus "
            f"{defaults['profiles']['contextual-v1']['exceptions']} in "
            f"v1. Exceptions are reporting classifications and do not "
            f"change infrastructure. Canonical route repairs can also "
            f"make existing routing evidence understandable to an "
            f"evaluator; that contextual delta is distinct from removing "
            f"a strict finding."
        ),
        "",
        (
            f"Grafana and helper changes in the same proposed format "
            f"candidate share its acceptance decision. "
            f"{rejected_envelopes} of {envelopes} envelope unwrappings "
            f"therefore roll back alongside helper proposals; retained "
            f"unwrappings can still leave other validation errors. "
            f"Candidate findings are preserved individually; rendering "
            f"can reveal pre-existing workload risks rather than "
            f"introduce new vulnerabilities. KSV-0125 in the saved "
            f"results means an untrusted image registry, and image "
            f"references remain unchanged."
        ),
        "",
        (
            "The primary execution manifest is preserved. Secondary "
            "assessments were recomputed from those exact scans under "
            "the final v2 policy. A source-AST proof isolates the "
            "generator-only schema compaction from every validator "
            "function; final generation context sizes are refreshed "
            "independently. No changed tool evaluation or candidate "
            "bytes are reused under a mismatched fingerprint. Policy "
            "lookup follows the checked-in mapping sourced from [AWS's "
            "NLB protocol "
            "tables](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/describe-ssl-policies.html)."
        ),
        "",
        (
            "Repair-schema previews in context-sizes.json are "
            "calculated offline at the existing 16,000-character "
            "default cap; they are not actual LLM requests. Historical "
            "configured overrides are not inferable from a package "
            "snapshot. Generation context coverage is bounded and "
            "truncated, even after common version fields are compacted; "
            "full mirrors remain available to schema-grounded repair."
        ),
        "",
        (
            "Independent/cumulative replay applies these approved "
            "changes to saved final bytes; it does not replay an entire "
            "live agent loop or reapply every legacy catalogue control. "
            "A live combined proposal can have different acceptance and "
            "timing. Static consumer analysis cannot observe "
            "out-of-band cloud resources. Review and actual deployment "
            "validation remain necessary before applying "
            "infrastructure."
        ),
        "",
    ]
    fields = Counter(tuple(r.get("differing_fields", [])) for r in discrepancies)
    historical = [r for r in discrepancies if r["comparison"] == "historical"]
    diagnostic_changes = sum(
        "failed_checks" in r.get("differing_fields", []) for r in historical
    )
    order_changes = sum("blockers" in r.get("differing_fields", []) for r in historical)
    validity_changes = sum(r["validation_changed"] for r in discrepancies)
    removed = sum(len(r["removed"]) for r in discrepancies)
    introduced = sum(len(r["introduced"]) for r in discrepancies)
    lines += [
        "## Baseline discrepancy interpretation",
        "",
        f"Validity changes across comparisons: {validity_changes}; "
        f"removed finding identities: {removed}; "
        f"introduced finding identities: {introduced}. "
        f"Historical diagnostic changes: {diagnostic_changes} packages; "
        f"historical finding-order differences: {order_changes} packages. "
        "The explicit terraform_unknown flag was absent in the original "
        "projection; its false value is recorded as a representation change. "
        "Helm locations/messages are more specific. Raw comparisons remain available.",
        "",
        "Field-change combinations (both comparisons): "
        + "; ".join(
            f"{', '.join(names)}: {count}" for names, count in sorted(fields.items())
        )
        + ".",
        "",
    ]
    if (output / "verification.json").exists():
        lines += [
            "## Verification",
            "",
            "[Verification evidence](verification.json) includes logs, exact "
            "counts and remaining limits. Verification used "
            "dotenv-disabled Python and disposable PostgreSQL with synthetic "
            "credentials. No real LLM calls, .env reads, new database migration "
            "or push was performed by Phase 9i.",
            "",
            "| Command | Result |",
            "|---|---|",
        ]
        for command in read(output / "verification.json")["commands"]:
            outcome = f"{command['passed']} passed" if "passed" in command else "passed"
            if command.get("perf_deselected"):
                outcome += (
                    f"; {command['perf_deselected']} performance tests deselected"
                )
            lines.append(f"| `{command['command']}` | {outcome} |")
    (output / "README.md").write_text("\n".join(lines))


def refresh_guidance(output: Path) -> None:
    """Refresh unexecuted generation guidance without reusing a tool evaluation."""
    result = read(output / "verified-summary.json")
    tree = ast.parse((ROOT / "backend/app/validation/schema_context.py").read_text())
    tree.body = [
        n
        for n in tree.body
        if not (isinstance(n, ast.FunctionDef) and n.name == "generator_schema_context")
    ]
    if result["guidance_only_change_proof"]:
        assert (
            digest(ast.dump(tree, include_attributes=False))
            == result["guidance_only_change_proof"]["unchanged_validator_ast_sha256"]
        )
    else:
        assert (
            hashlib.sha256(
                (ROOT / "backend/app/validation/schema_context.py").read_bytes()
            ).hexdigest()
            == read(output / "execution-evaluator-manifest.json")[
                "backend/app/validation/schema_context.py"
            ]
        )
    packages, manifest = inventory()
    assert manifest == read(output / "input-manifest.json")
    contexts = read(output / "context-sizes.json")
    items = {p["key"]: p for p in packages}
    discrepancies = read(output / "baseline-discrepancies.json")
    for row in discrepancies:
        filename = row["key"].replace("/", "-") + ".json"
        frozen = read(output / "baseline" / filename)
        before = frozen["stored" if row["comparison"] == "historical" else "observed"]
        observed = read(output / "schema_guidance" / filename)["observed"]
        row["differing_fields"] = sorted(
            k
            for k in before.keys() | observed.keys()
            if k != "profiles" and before.get(k) != observed.get(k)
        )
    for row in contexts:
        context = generation_context(
            DeploymentPlan.model_validate(items[row["key"]]["plan"])
        )
        assert context.schema_chars <= 4500 and len(context.text) <= 6000
        entries = json.loads(context.text[: context.schema_chars] or "[]")
        row["after"] = {
            "schema": context.schema_chars,
            "checklist": context.checklist_chars,
            "total": len(context.text),
            "truncated": context.truncated,
            "requested_resource_types": context.resource_types,
            "included_resource_types": sorted({e["type"] for e in entries}),
            "truncated_resource_types": sorted(
                {e["type"] for e in entries if e.get("truncated")}
            ),
            "schema_entries": entries,
        }
    result["guidance_source_sha256"] = hashlib.sha256(
        (ROOT / "backend/app/validation/schema_context.py").read_bytes()
    ).hexdigest()
    result["secondary_policy_source_sha256"] = hashlib.sha256(
        (ROOT / "backend/app/security/profiles_v2.py").read_bytes()
    ).hexdigest()
    write(output / "context-sizes.json", contexts)
    write(output / "verified-summary.json", result)
    write(output / "baseline-discrepancies.json", discrepancies)
    markdown(output, result, contexts, discrepancies)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    parser.add_argument("--refresh-guidance", action="store_true")
    args = parser.parse_args()
    if args.refresh_guidance:
        refresh_guidance(args.output)
        return
    result = verify_and_report(args.output)
    print(
        json.dumps(
            {
                "packages": result["legacy_golden_packages"],
                "idempotence_checks": result["idempotence_checks"],
                "input_manifest_unchanged": True,
            }
        )
    )


if __name__ == "__main__":
    main()
