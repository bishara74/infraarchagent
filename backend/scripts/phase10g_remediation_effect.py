"""FR-S-02/03/07: offline, source-free first-scan versus retained-file analysis."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COHORTS = (
    ("final_set_1", "real-20261020T010134093069Z", "final-1-results"),
    ("final_set_2", "real-20261020T013911945957Z", "final-2-results"),
    ("broad_1", "broad-20261020T234203035108Z", "broad-1-results"),
    ("broad_2", "broad-20261021T200436165739Z", "broad-2-results"),
    ("sonnet", "broad-20261024T233240471733Z", "broad-sonnet-results"),
    ("10b", "broad-20261027T015443795826Z", "broad-final-results"),
    ("10c", "broad-20261027T155607468680Z", "broad-final2-results"),
    ("10d", "broad-20261027T205119472235Z", "broad-final3-results"),
    ("10e_final", "broad-20261028T125056656606Z", "broad-final10e-results"),
)
CLASSES = ("reduced", "unchanged_nonzero", "already_zero", "increased", "unknown")
METRICS = ("blocking", "high_critical", "all")
HIGH = {"HIGH", "CRITICAL"}
TOOLS = {"checkov", "trivy"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: object) -> str:
    return sha(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )


def number(value: object) -> bool:
    return type(value) is int and value >= 0


def classify(before: int | None, after: int | None) -> str:
    if not number(before) or not number(after):
        return "unknown"
    if after < before:
        return "reduced"
    if after > before:
        return "increased"
    return "already_zero" if before == 0 else "unchanged_nonzero"


def code(value: object) -> str:
    return (
        value
        if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,99}", value)
        else "unknown"
    )


def rules(findings: list) -> list[str]:
    return sorted(
        {
            value
            for finding in findings
            if isinstance(finding, dict)
            and isinstance(value := finding.get("rule_id"), str)
            and re.fullmatch(r"[A-Z][A-Z0-9_-]{0,99}", value)
        }
    )


class Evidence:
    """Read immutable Git blobs; cache and output have separate trust boundaries."""

    def __init__(self, root: Path, revision: str):
        self.root = root
        self.revision = self.git("rev-parse", "--verify", revision + "^{commit}")
        self.revision = self.revision.decode().strip()
        self.paths = set(
            self.git("ls-tree", "-r", "--name-only", self.revision)
            .decode()
            .splitlines()
        )
        self.used = {}

    def git(self, *args: str) -> bytes:
        return subprocess.check_output(
            ["git", "-C", str(self.root), *args], stderr=subprocess.PIPE
        )

    def read(self, path: str) -> bytes:
        if path not in self.paths or not path.startswith("docs/"):
            raise ValueError("Input must be committed documentation evidence")
        data = self.git("show", f"{self.revision}:{path}")
        self.used[path] = sha(data)
        return data

    def json(self, path: str):
        return json.loads(self.read(path))


def pinned_exports(evidence: Evidence) -> dict[str, str]:
    pins = {}
    for path, key in (
        ("phase9b-supplement-inputs/source-manifest.json", "source_files"),
        ("phase9k-baseline-audit/audit.json", "sources"),
        ("phase10c-replay/manifest.json", "inputs"),
        ("phase10e-replay/manifest.json", "cohorts"),
    ):
        data = evidence.json("docs/evals/" + path)[key]
        records = (
            [row for cohort in data.values() for row in cohort["inputs"]]
            if key == "cohorts"
            else data
        )
        for row in records:
            if "source_directory" in row:
                name = f".cache/{row['source_directory']}/{row['source_file']}"
                expected = row["source_sha256"]
            else:
                name = row["path"]
                name = name if name.startswith(".cache/") else ".cache/" + name
                expected = row["sha256"]
            if name in pins and pins[name] != expected:
                raise ValueError("Conflicting committed export hashes")
            pins[name] = expected
    return pins


def verify_package(
    snapshot: dict, package: dict, quality: dict, architecture: dict | None
) -> list[str]:
    """Check committed identities/content and final finding/status projection."""
    errors = []
    if architecture:
        for key, value in (
            ("plan_sha256", snapshot.get("plan")),
            ("original_files_sha256", package.get("original_files")),
            ("retained_files_sha256", package.get("files")),
        ):
            if digest(value) != architecture.get(key):
                errors.append(key + "_mismatch")
    final = (package.get("security_report") or {}).get("final", {})
    remaining = final.get("remaining_blocking")
    if not isinstance(remaining, list):
        errors.append("missing_final_blocking")
        remaining = []
    checks = {
        "status": package.get("status") == quality.get("status"),
        "remaining_findings": dict(Counter(v["rule_id"] for v in remaining))
        == quality.get("remaining_findings"),
        "blocking_total": len(remaining)
        == quality.get("counts", {}).get("remaining_findings"),
        "review_reasons": sorted(package.get("review_reasons", []))
        == sorted(quality.get("review_reasons", [])),
        "validation_result": (package.get("validation_report") or {})
        .get("summary", {})
        .get("result")
        == quality.get("validation_result"),
    }
    errors.extend(
        "quality_" + key + "_mismatch" for key, ok in checks.items() if not ok
    )
    return errors


def scans(report: dict) -> tuple[dict | None, dict | None, dict, list[dict]]:
    sessions = report.get("sessions")
    sessions = sessions if isinstance(sessions, list) else [report]
    automated = [s for s in sessions if s.get("kind") in (None, "automated")]
    first_session = automated[0] if automated else {}
    first = next(
        (
            i["scan"]
            for i in first_session.get("iterations", [])
            if isinstance(i.get("scan"), dict)
        ),
        None,
    )
    if report.get("omitted_session_count", 0):
        first = None
    # A rejected candidate or the final session's first scan is never the endpoint.
    final = report.get("final_verification")
    final = final if isinstance(final, dict) else None
    return first, final, first_session.get("final", {}), sessions


def scan_counts(scan: dict | None) -> dict[str, int | None]:
    result = dict.fromkeys(METRICS)
    if not scan or not isinstance(scan.get("blocking"), list):
        return result
    status = scan.get("tool_status", {})
    if any(
        value not in {"ok", "syntax_limited", "file_input_blocked"}
        for value in status.values()
    ):
        return result
    blocking = scan["blocking"]
    result["blocking"] = len(blocking)
    advisory = scan.get("advisory_count")
    severities = scan.get("counts_by_severity")
    if number(advisory):
        result["all"] = len(blocking) + advisory
    if isinstance(severities, dict) and all(number(n) for n in severities.values()):
        if result["all"] is not None and sum(severities.values()) != result["all"]:
            return dict.fromkeys(METRICS)
        high = sum(severities.get(s, 0) for s in HIGH)
        listed = [*blocking, *scan.get("advisory_sample", [])]
        listed_high = [v for v in listed if v.get("severity") in HIGH]
        # Do not infer the tools/severities of omitted advisory identities.
        if len(listed_high) == high:
            result["high_critical"] = sum(v.get("tool") in TOOLS for v in listed_high)
    return result


def observed_delta(first: dict | None, final: dict | None) -> list[str] | None:
    """Positive rule-multiplicity deltas require complete identity lists."""
    if first is None or final is None:
        return None
    for scan in (first, final):
        if (
            not number(scan.get("advisory_count"))
            or len(scan.get("advisory_sample", [])) != scan["advisory_count"]
        ):
            return None

    def identities(scan):
        return Counter(
            (f.get("tool"), f.get("rule_id"))
            for f in [*scan.get("blocking", []), *scan.get("advisory_sample", [])]
        )

    return rules(
        [{"rule_id": rule} for _, rule in identities(final) - identities(first)]
    )


def reason_evidence(
    package: dict | None, quality: dict
) -> tuple[list[str], list[dict]]:
    reasons = {code(r) for r in quality.get("review_reasons", [])}
    records = []
    report = (package or {}).get("security_report") or {}
    _, _, _, sessions = scans(report)
    for session in sessions:
        final_reason = session.get("final", {}).get("reason")
        if final_reason == "iteration limit":
            reasons.add("iteration_limit")
        elif isinstance(final_reason, str) and "unsafe_file_input" in final_reason:
            reasons.add("unsafe_file_input")
        elif isinstance(final_reason, str) and "deadline" in final_reason:
            reasons.add("security_deadline")
        for iteration in session.get("iterations", []):
            verification = iteration.get("verification") or {}
            local = {code(r) for r in verification.get("reasons", [])}
            if iteration.get("stop_reason"):
                local.add(code(iteration["stop_reason"]))
            fixes = iteration.get("fixes", [])
            for fix in fixes:
                for attempt in fix.get("attempt_details", []):
                    if attempt.get("outcome") not in (None, "success"):
                        local.add("fixer_" + code(attempt.get("category")))
            if any(f.get("retained") is True for f in fixes):
                local.add("fix_marked_retained")
            local.update(code(f["reason"]) for f in fixes if f.get("reason"))
            entry = {
                "stage": "security",
                "iteration": iteration.get("index"),
                "outcome": code(verification.get("outcome"))
                if verification
                else "scan_only",
                "reasons": sorted(local),
                "fixes_marked_retained": sum(f.get("retained") is True for f in fixes),
                "fix_rule_ids": rules(
                    [{"rule_id": r} for f in fixes for r in f.get("rule_ids", [])]
                ),
                "introduced_rule_ids": [],
            }
            for field in ("catalogue", "templates", "partial_groups"):
                for proposal in verification.get(field, []):
                    if proposal.get("status") == "retained":
                        local.add(field + "_marked_retained")
                    if proposal.get("reason"):
                        local.add(code(proposal["reason"]))
                    introduced = rules(proposal.get("introduced_findings", []))
                    if introduced or proposal.get("status") in {"retained", "rejected"}:
                        records.append(
                            {
                                "stage": field,
                                "template": code(proposal.get("template"))
                                if field == "templates"
                                else None,
                                "iteration": iteration.get("index"),
                                "outcome": code(proposal.get("status")),
                                "introduced_rule_ids": introduced,
                            }
                        )
            reasons.update(local)
            entry["reasons"] = sorted(local)
            records.append(entry)
    remediation = ((package or {}).get("validation_report") or {}).get(
        "remediation", {}
    )
    for round_ in remediation.get("rounds", []):
        reason = code(round_.get("reason")) if round_.get("reason") else None
        if reason:
            reasons.add(reason)
        records.append(
            {
                "stage": "validation_" + code(round_.get("phase")),
                "outcome": code(round_.get("outcome")),
                "reasons": [reason] if reason else [],
                "introduced_rule_ids": rules(round_.get("introduced_findings", [])),
            }
        )
    if not package:
        reasons.add("export_unavailable_or_unverified")
    return sorted(reasons or {"unknown"}), records


def visibility(status: str, count: int | None, package: dict | None) -> str:
    if not number(count):
        return "unknown"
    if count == 0:
        return "no_recorded_blockers"
    if status != "pending_review":
        return "exception_status"
    if package is None:
        return "pending_review_visibility_unverified"
    report = package.get("security_report") or {}
    remaining = report.get("final", {}).get("remaining_blocking")
    if (
        not isinstance(remaining, list)
        or len(remaining) != count
        or len(rules(remaining)) == 0
        or "unresolved_security_findings" not in package.get("review_reasons", [])
        or package.get("review_available") is not True
    ):
        return "exception_visibility"
    return "pending_review_findings_visible"


def package_row(
    label: str, run: dict, variant: str, quality: dict, package: dict | None
) -> dict:
    report = (package or {}).get("security_report") or {}
    first, final, initial, _ = scans(report)
    before, after = scan_counts(first), scan_counts(final)
    # Tool-specific first counts are authoritative and exclude Terraform's findings.
    initial_tools = [
        initial.get("first_scan_" + t + "_high_or_critical") for t in sorted(TOOLS)
    ]
    if before["blocking"] is not None and all(number(n) for n in initial_tools):
        recorded_high = sum(initial_tools)
        before["high_critical"] = (
            recorded_high if before["high_critical"] in (None, recorded_high) else None
        )
    committed_final = quality.get("counts", {}).get("remaining_findings")
    if after["blocking"] is not None and after["blocking"] != committed_final:
        before, after = dict.fromkeys(METRICS), dict.fromkeys(METRICS)
    final_scan_available = after["blocking"] is not None
    # Final blockers remain independently available from committed quality evidence.
    after["blocking"] = committed_final if number(committed_final) else None
    reasons, records = reason_evidence(package, quality)
    row = {
        "round": label,
        "run_id": run["run_id"],
        "variant": variant,
        "scenario_id": run.get("scenario_id"),
        "complexity": quality.get("complexity", run.get("complexity")),
        "status": quality.get("status"),
        "reasons": reasons,
        "reason_evidence": records,
        "first_rule_ids": rules((first or {}).get("blocking", [])),
        "final_rule_ids": sorted(quality.get("remaining_findings", {})),
        "first_sample_rule_ids": rules((first or {}).get("advisory_sample", [])),
        "final_sample_rule_ids": rules((final or {}).get("advisory_sample", [])),
        "new_observed_rule_ids": observed_delta(first, final),
        "first_advisory_omitted": (first or {}).get("advisory_omitted_count"),
        "final_advisory_omitted": (final or {}).get("advisory_omitted_count"),
        "first_tool_status": (first or {}).get("tool_status", {}),
        "final_tool_status": (final or {}).get("tool_status", {}),
        "visibility": visibility(quality.get("status"), committed_final, package),
        "advisory_only": after["blocking"] == 0
        and number(after["all"])
        and after["all"] > 0,
    }
    for metric in METRICS:
        row[metric + "_first"] = before[metric]
        row[metric + "_final"] = after[metric]
        comparable_after = (
            after[metric] if metric != "blocking" or final_scan_available else None
        )
        row[metric + "_class"] = classify(before[metric], comparable_after)
    return row


def inventory(evidence: Evidence, cache: Path) -> tuple[list[dict], list[dict]]:
    pins = pinned_exports(evidence)
    rows, exports = [], []
    for label, suffix, directory in COHORTS:
        folder = "docs/evals/phase9-bench-" + suffix
        runs = evidence.json(folder + "/results.json")["runs"]
        for run in runs:
            run_id = run.get("run_id")
            if not run_id:
                continue
            path = cache / directory / (run_id + ".json")
            relative = f".cache/{directory}/{run_id}.json"
            packages, snapshot = {}, {}
            export = {"path": relative, "round": label, "packages": []}
            try:
                if path.is_symlink() or not path.resolve().is_relative_to(
                    cache.resolve()
                ):
                    raise ValueError("unsafe_export_path")
                raw = path.read_bytes()
                export["sha256"] = sha(raw)
                pin = pins.get(relative)
                export["previously_pinned_sha256"] = pin
                if pin is not None and sha(raw) != pin:
                    raise ValueError("export_hash_mismatch")
                snapshot = json.loads(raw)
                if snapshot.get("run", {}).get("id") != run_id:
                    raise ValueError("export_run_mismatch")
                packages = {p["variant"]: p for p in snapshot.get("packages", [])}
                if len(packages) != len(snapshot.get("packages", [])):
                    raise ValueError("duplicate_export_variant")
                export["verification"] = (
                    "whole_export_hash" if pin else "content_projection"
                )
            except (OSError, ValueError, KeyError):
                export["verification"] = "unverified"
                packages = {}
            for variant in ("cost", "performance", "security"):
                quality_path = f"{folder}/quality/{run_id}/{variant}.json"
                if quality_path not in evidence.paths:
                    continue
                quality = evidence.json(quality_path)
                package = packages.get(variant)
                architecture_path = f"{folder}/architecture/{run_id}/{variant}.json"
                architecture = (
                    evidence.json(architecture_path)
                    if architecture_path in evidence.paths
                    else None
                )
                errors = (
                    verify_package(snapshot, package, quality, architecture)
                    if package
                    else ["export_unavailable_or_unverified"]
                )
                if package and pins.get(relative) is None and architecture is None:
                    errors.append("no_committed_content_hashes")
                export["packages"].append({"variant": variant, "errors": errors})
                row = package_row(
                    label, run, variant, quality, None if errors else package
                )
                row["quality_source"] = quality_path
                row["export_source"] = relative
                row["provenance"] = (
                    export["verification"] if not errors else "unverified"
                )
                row["verification_errors"] = errors
                rows.append(row)
            exports.append(export)
    return rows, exports


def summary(rows: list[dict], metric: str) -> dict:
    counts = Counter(row[metric + "_class"] for row in rows)
    comparable = len(rows) - counts["unknown"]
    not_increased = sum(
        counts[c] for c in ("reduced", "unchanged_nonzero", "already_zero")
    )
    return {
        "packages": len(rows),
        **{c: counts[c] for c in CLASSES},
        "comparable": comparable,
        "not_increased": not_increased,
        "reduced_fraction_of_comparable": counts["reduced"] / comparable
        if comparable
        else None,
        "not_increased_fraction_of_comparable": not_increased / comparable
        if comparable
        else None,
    }


def groups(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    result = [("pooled (nine rounds)", rows)]
    result += [
        (label, [r for r in rows if r["round"] == label]) for label, _, _ in COHORTS
    ]
    result += [
        (f"pooled level {level}", [r for r in rows if r["complexity"] == level])
        for level in range(1, 6)
    ]
    result.append(
        ("legacy complexity unassigned", [r for r in rows if r["complexity"] is None])
    )
    result += [
        (
            f"{label} level {level}",
            [r for r in rows if r["round"] == label and r["complexity"] == level],
        )
        for label, _, _ in COHORTS
        for level in range(1, 6)
        if any(r["round"] == label and r["complexity"] == level for r in rows)
    ]
    return result


def thesis_wording(rows: list[dict]) -> str:
    pooled = summary(rows, "blocking")
    final = summary([r for r in rows if r["round"] == "10e_final"], "blocking")
    unresolved = [
        r for r in rows if number(r["blocking_final"]) and r["blocking_final"] > 0
    ]
    visible = sum(
        r["visibility"] == "pending_review_findings_visible" for r in unresolved
    )
    all_pooled = summary(rows, "all")
    all_final = summary([r for r in rows if r["round"] == "10e_final"], "all")
    return (
        "The universal criterion of reducing violations on every generated "
        "package was not met. "
        f"Across nine development rounds ({pooled['packages']} generated packages), "
        "recorded strict blocking findings decreased in "
        f"{pooled['reduced']} of {pooled['comparable']} comparable packages, "
        f"were unchanged and non-zero in {pooled['unchanged_nonzero']}, "
        f"were zero at both endpoints in {pooled['already_zero']}, "
        f"and increased in {pooled['increased']}; "
        f"{pooled['unknown']} packages lacked a usable comparison. "
        "In the final round, the "
        f"corresponding counts were {final['reduced']}, {final['unchanged_nonzero']}, "
        f"{final['already_zero']} and {final['increased']} out of {final['packages']} "
        f"({final['unknown']} unknown). All {visible} of {len(unresolved)} "
        "packages with recorded unresolved blockers were pending_review "
        "with the blocking findings visible in their exported reports. "
        "Advisory findings are a separate policy category and may remain on "
        "packages labelled checks_passed. When advisory findings are included, "
        f"totals increased on {all_pooled['increased']} packages overall and "
        f"{all_final['increased']} in the final round, so a blanket claim "
        "that violations never increased is not supported. "
        "These are observed scan counts on "
        "retained files, with scanner limitations disclosed; repeated "
        "scenarios and shared plans make the pooled result descriptive "
        "rather than a causal or deployment-security guarantee."
    )


def render(rows: list[dict], exports: list[dict], revision: str) -> str:
    lines = [
        "# Phase 10g — does remediation reduce violations on every package?",
        "",
        thesis_wording(rows),
        "",
        "## Inputs and method",
        "",
        f"Committed evidence revision: `{revision}`. "
        "[Package CSV](packages.csv) contains "
        "one row for each generated package; [input "
        "manifest](input-manifest.json) pins "
        "committed blobs, cache export bytes, verification outcomes and the "
        "analysis script.",
        "",
        "The nine agreed rounds are included once each. Missing variants are "
        "not generated "
        "packages and are excluded; schedule slots are not observations. The "
        "aborted first "
        "10e attempt (27 settled packages, 8 checks_passed) is excluded as in "
        "Phase 10f. "
        "No smoke/stub samples or earlier development rounds enter this pool. "
        "The 504 scheduled variant slots comprise 491 generated packages and "
        "13 missing variants, distinct from the three unknown comparisons.",
        "",
        "The first endpoint is the earliest recorded automated security scan, "
        "after any "
        "pre-security generation/validation repair. The endpoint is "
        "final_verification on "
        "retained files after validation repair. Candidate "
        "after_failed/retained_failed are "
        "Terraform validation-check counts and are never scanner finding "
        "counts. Canonical "
        "sessions take precedence over legacy iteration aliases; omitted "
        "original sessions "
        "make the first endpoint unknown. No rescans, native tools, model "
        "calls or external "
        "services are used by this analysis.",
        "",
        "Strict means recorded strict blocking flags, including existing "
        "variant exemptions; "
        "contextual-v1/v2 reclassification is not applied. HIGH/CRITICAL "
        "counts include only "
        "Checkov + Trivy, retaining cross-tool duplicate detections. The "
        "stored combined first "
        "count can include Terraform and is deliberately not used. All "
        "findings = blocking "
        "+ complete advisory_count. Severity totals cross-check totals; "
        "omitted advisory "
        "samples do not become invented rule identities or tool attributions.",
        "",
        "Classes: reduced means strictly fewer; unchanged_nonzero means equal positive "
        "counts; already_zero means both endpoints are zero; increased "
        "includes zero to "
        "positive; unknown means missing/unverified/inconsistent data. Not increased = "
        "reduced + unchanged_nonzero + already_zero. Class percentages use "
        "all generated "
        "packages in that row; the final two rates use comparable packages "
        "only. Counts "
        "are per package, not numbers of distinct rule IDs.",
        "",
        "### Cache verification coverage",
        "",
        "| Round | Generated | Missing variants | Verified exports | "
        "Whole-export pin / content "
        "projection |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, _, _ in COHORTS:
        subset = [r for r in rows if r["round"] == label]
        selected = [e for e in exports if e["round"] == label]
        modes = Counter(r["provenance"] for r in subset)
        verified = sum(e["verification"] != "unverified" for e in selected)
        lines.append(
            f"| {label} | {len(subset)} | {3 * len(selected) - len(subset)} | "
            f"{verified}/{len(selected)} | "
            f"{modes['whole_export_hash']} / {modes['content_projection']} packages |"
        )
    lines += [
        "",
        "Earlier exports match previously committed whole-file SHA-256 "
        "values. Sonnet and "
        "final 10e instead match committed plan/original/retained canonical "
        "hashes plus "
        "status, final rule multiplicities, blocking totals, review reasons "
        "and validation "
        "result. This corroborates package content and final state; their first-scan "
        "metadata has no independent historical whole-export attestation. "
        "Newly recording "
        "export hashes makes this analysis reproducible but does not create "
        "that attestation. "
        "Any failed verification invalidates the export-derived comparison, "
        "while independently "
        "committed final blocker counts remain available.",
        "",
        "## Counts and percentages",
    ]
    for metric in METRICS:
        lines += [
            "",
            f"### {metric}",
            "",
            "| Group | N | Reduced | Unchanged non-zero | Already zero | "
            "Increased | Unknown | Reduced/comparable | Not "
            "increased/comparable |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for name, subset in groups(rows):
            if not subset:
                continue
            s = summary(subset, metric)
            cells = [f"{s[c]} ({s[c] / len(subset):.2%})" for c in CLASSES]
            rates = [
                f"{s[k]}/{s['comparable']} ({s[k] / s['comparable']:.2%})"
                if s["comparable"]
                else "unknown"
                for k in ("reduced", "not_increased")
            ]
            lines.append(
                f"| {name} | {len(subset)} | " + " | ".join([*cells, *rates]) + " |"
            )
    lines += [
        "",
        "## Unchanged, increased and unknown cases",
        "",
        "Every package with an unchanged non-zero, increased or unknown result for any "
        "metric is listed below. The CSV includes all three before/after "
        "counts, per-metric "
        "classes, first/final blocker IDs, advisory sample IDs, scanner "
        "statuses and structured "
        "reason_evidence. Proposal retained flags describe local actions, not "
        "final retention when a later guard rolls back. Reasons are recorded "
        "observations with overlap, not "
        "exclusive causal "
        "assignments. Proposed/introduced findings and rolled-back candidates "
        "are labelled "
        "separately in reason_evidence; they do not establish a retained "
        "regression. No "
        "unrecorded explanation is inferred from an unchanged count.",
        "",
        "| Round / run / variant | Blocking / HIGH-CRITICAL / all | Recorded "
        "reasons | Final blocker IDs |",
        "|---|---|---|---|",
    ]
    for r in rows:
        if any(
            r[m + "_class"] in {"unchanged_nonzero", "increased", "unknown"}
            for m in METRICS
        ):
            cells = [
                f"{r[m + '_first']}→{r[m + '_final']} ({r[m + '_class']})"
                for m in METRICS
            ]
            lines.append(
                f"| {r['round']} / {r['run_id']} / {r['variant']} | "
                f"{' / '.join(cells)} | {', '.join(r['reasons'])} | "
                f"{', '.join(r['final_rule_ids']) or 'none recorded'} |"
            )
    lines += ["", "## Review visibility and literal-criterion qualifications", ""]
    for name, subset in groups(rows)[:10]:
        unresolved = [
            r for r in subset if number(r["blocking_final"]) and r["blocking_final"] > 0
        ]
        visible = sum(
            r["visibility"] == "pending_review_findings_visible" for r in unresolved
        )
        advisory_only = [r for r in subset if r["advisory_only"]]
        passed_advisory = sum(r["status"] == "checks_passed" for r in advisory_only)
        lines.append(
            f"- {name}: {visible}/{len(unresolved)} unresolved-blocker packages "
            "have pending_review, full recorded blocker IDs, "
            "unresolved_security_findings and review_available=true; "
            f"{len(advisory_only)} advisory-only packages, of which "
            f"{passed_advisory} are checks_passed."
        )
    exceptions = [
        r
        for r in rows
        if r["visibility"].startswith("exception")
        or r["visibility"] == "pending_review_visibility_unverified"
    ]
    lines += ["", f"Blocking-status/visibility exceptions: **{len(exceptions)}**."]
    for r in exceptions:
        lines.append(
            f"- {r['round']} / {r['run_id']} / {r['variant']}: "
            f"{r['visibility']}; {', '.join(r['final_rule_ids'])}."
        )
    lines += [
        "",
        "Advisory-only packages outside pending_review are exceptions to a "
        "literal requirement "
        "that every remaining finding forces review, although strict "
        "readiness deliberately "
        "permits advisories. Their identifiers and sample-only visibility "
        "limits follow:",
        "",
    ]
    for r in rows:
        if r["advisory_only"] and r["status"] != "pending_review":
            lines.append(
                f"- {r['round']} / {r['run_id']} / {r['variant']}: "
                f"{r['status']}, {r['all_final']} advisories; recorded sample IDs "
                f"{', '.join(r['final_sample_rule_ids'])}; omitted identities "
                f"{r['final_advisory_omitted']}."
            )
    lines += [
        "",
        "### All-finding increases and observed added rule IDs",
        "",
        "Positive rule-multiplicity deltas require complete first/final "
        "identity lists. Truncated samples leave added identities unknown. "
        "Retained template/Fixer records identify recorded actions, not an "
        "exclusive causal explanation for each advisory. Rejected template "
        "introduced_findings are candidate-only, never retained deltas.",
        "",
        "| Round / run / variant | All findings | Added rule IDs | Recorded actions |",
        "|---|---:|---|---|",
    ]
    for r in rows:
        if r["all_class"] == "increased":
            added = r["new_observed_rule_ids"]
            added_text = (
                ", ".join(added) if added is not None else "unknown (sample truncated)"
            )
            actions = sorted(
                {
                    e["stage"] + ":" + str(e.get("template") or "") + ":" + e["outcome"]
                    for e in r["reason_evidence"]
                    if e.get("outcome") in {"retained", "accepted"}
                }
            )
            lines.append(
                f"| {r['round']} / {r['run_id']} / {r['variant']} | "
                f"{r['all_first']}→{r['all_final']} | {added_text} | "
                f"{', '.join(actions) or 'unknown'} |"
            )
    lines += [
        "",
        "## Limitations and thesis interpretation",
        "",
        "Legacy final sets use three prompt texts rather than registered "
        "complexity levels; "
        "their complexity remains unassigned instead of being invented from "
        "later anchors. "
        "Later levels 1–5 are ordinal registered scenario labels. Packages "
        "share plans and "
        "scenarios repeat across changed code/models; pooling is a "
        "descriptive inventory, "
        "not the matched-cohort readiness pooling in D-55 or a causal "
        "improvement estimate.",
        "",
        "Syntax-limited scans and refused file inputs describe observed "
        "findings only, not "
        "complete security coverage. The three 10b exports with "
        "unsafe_file_input have no "
        "usable scan pair; empty stored blockers in such a failure do not "
        "establish cleanliness. "
        "Pre-security repairs are outside the first-to-final interval. "
        "Post-security repairs "
        "are included, so the difference is a retained pipeline outcome "
        "rather than attribution "
        "to the LLM Fixer alone. Advisory samples omit identities but retain "
        "total counts. "
        "Visibility is proven at the recorded API/presentation level, not by "
        "a fresh browser "
        "session. Zero blockers alone does not prove validation, plan "
        "conformance or deployment.",
        "",
        "### Proposed thesis paragraph",
        "",
        thesis_wording(rows),
        "",
        "## Reproduction",
        "",
        "From the repository root, using the same cache folders and a new "
        "output directory:",
        "",
        "```bash",
        "backend/.venv/bin/python backend/scripts/phase10g_remediation_effect.py \\",
        "  --revision " + revision + " \\",
        "  --output-dir docs/evals/phase10g-remediation-effect-reproduced",
        "```",
        "",
        "Run the module from the root with PYTHONPATH=backend, or use "
        "Python's script path "
        "`backend/scripts/phase10g_remediation_effect.py`. Only the standard "
        "library is "
        "required. Existing output directories are refused. No dotenv is "
        "read. Verification "
        "results are recorded in the implementation log and adjacent "
        "verification.json.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "docs/evals/phase10g-remediation-effect",
    )
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output.exists() or not output.is_relative_to((ROOT / "docs/evals").resolve()):
        raise SystemExit("Output must be a new evaluation report directory")
    evidence = Evidence(ROOT, args.revision)
    rows, exports = inventory(evidence, args.cache)
    for path in (
        "docs/spec/01-introduction.tex",
        "docs/design-deviations.md",
        "docs/prompts/phase10g.md",
        "docs/evals/phase10f-final-report/README.md",
        "docs/evals/phase10f-final-report/calculations.json",
        "docs/evals/phase10f-final-report/input-manifest.json",
    ):
        evidence.read(path)
    output.mkdir()
    with (output / "packages.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, sort_keys=True, separators=(",", ":"))
                    if isinstance(v, (dict, list))
                    else v
                    for k, v in row.items()
                }
            )
    (output / "README.md").write_text(render(rows, exports, evidence.revision))
    manifest = {
        "evidence_revision": evidence.revision,
        "analysis_sha256": sha(Path(__file__).read_bytes()),
        "committed_inputs": evidence.used,
        "cache_exports": exports,
        "outputs": {p.name: sha(p.read_bytes()) for p in sorted(output.iterdir())},
        "method": "Immutable Git inputs; whole-export pins or canonical "
        "content/quality corroboration; no source content exported",
    }
    (output / "input-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "pooled": summary(rows, "blocking"),
                "final": summary(
                    [r for r in rows if r["round"] == "10e_final"], "blocking"
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
