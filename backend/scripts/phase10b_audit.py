"""Offline exposure counter-audit; historical evidence and profiles are read-only."""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from app.core.logging import RedactingFilter
from scripts.phase9_common import ROOT, write_json
from scripts.phase9b_report import Evidence
from scripts.phase9d_quality import quality_snapshot
from scripts.phase9k_audit import package_audit
from scripts.secret_scan import matches

PROFILES = ("strict", "contextual-v1", "contextual-v2")
AUDITS = (
    "docs/evals/phase9k-baseline-audit/audit.json",
    "docs/evals/phase9k-architect-report/experiment-architecture.json",
)
SUPPLEMENT = "docs/evals/phase9b-supplement/proposal-counts.json"


def exposure_flip(audit: dict | None) -> bool | None:
    if audit is None:
        return None
    planned = audit["plan"]["classification"]
    if planned in {"absent", "internal"}:
        return False
    if planned != "public":
        return None
    original = {r["resource"]: r for r in audit["original"]["resources"]}
    retained = {r["resource"]: r for r in audit["retained"]["resources"]}
    if any(
        r.get("classification") == "unknown"
        for r in [*original.values(), *retained.values()]
    ):
        return None
    if (
        audit["original"]["classification"] == "unknown"
        or audit["retained"]["classification"] == "unknown"
    ):
        return None
    return any(
        r["classification"] == "public"
        and retained.get(address, {}).get("classification") == "internal"
        for address, r in original.items()
    )


def summarize(rows: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[row["folder"]].append(row)
    result = []
    for folder, packages in sorted(groups.items()):
        profiles = {}
        for profile in PROFILES:
            known = [r for r in packages if type(r["passes"].get(profile)) is bool]
            passed = sum(r["passes"][profile] for r in known)
            affected_passes = sum(
                r["passes"][profile] and r["affected"] is True for r in known
            )
            unknown_passes = sum(
                r["passes"][profile] and r["affected"] is None for r in known
            )
            profiles[profile] = {
                "recorded_packages": len(known),
                "published_passes": passed if known else None,
                "affected_passes": affected_passes if known else None,
                "corrected_passes": passed - affected_passes if known else None,
                "corrected_pass_range": [
                    passed - affected_passes - unknown_passes,
                    passed - affected_passes,
                ]
                if known
                else None,
                "unknown_passing_packages": unknown_passes,
            }
        result.append(
            {
                "folder": folder,
                "packages": len(packages),
                "audited": sum(r["audit"] is not None for r in packages),
                "confirmed_affected": sum(r["affected"] is True for r in packages),
                "unknown": sum(r["affected"] is None for r in packages),
                "profiles": profiles,
            }
        )
    return result


def historical_profiles(evidence, path: str, saved: dict) -> dict:
    if saved.get("profile_assessments"):
        return saved["profile_assessments"]
    cohorts = {
        "phase9-bench-real-20261018T213645241170Z": "A3",
        "phase9-bench-real-20261018T231027886459Z": "B",
    }
    folder = cohorts.get(Path(path).parts[2])
    if folder:
        alternative = (
            f"docs/evals/phase9g-reclassification-20261019/{folder}/quality/"
            f"{Path(path).parent.name}/{Path(path).name}"
        )
        if alternative in evidence.paths:
            frozen = evidence.json(alternative)
            for field in ("validation_result", "remaining_findings"):
                if frozen.get(field) != saved.get(field):
                    raise ValueError("Historical reclassification identity mismatch")
            return frozen.get("profile_assessments", {})
    return {}


def inventory(evidence: Evidence, cache: Path) -> tuple[list[dict], list[dict]]:
    observations = {}
    sources = []

    def add(folder, row, source):
        key = folder, row["run_id"], row["variant"]
        projection = {
            k: row[k]
            for k in (
                "plan",
                "original",
                "retained",
                "plan_sha256",
                "original_files_sha256",
                "retained_files_sha256",
            )
        }
        if key in observations and observations[key][0] != projection:
            raise ValueError("Conflicting exposure evidence")
        observations[key] = projection, source

    for path in AUDITS:
        if path not in evidence.paths:
            continue
        data = evidence.json(path)
        for row in data["packages"] if isinstance(data, dict) else data:
            add(row["folder"], row, path)
    for path in sorted(evidence.paths):
        if (
            path.startswith("docs/evals/phase9-bench-")
            and "/architecture/" in path
            and path.endswith(".json")
        ):
            row = evidence.json(path)
            if row.get("variant") and "original" in row:
                add(Path(path).parts[2], row, path)
    quality_paths = [
        p
        for p in sorted(evidence.paths)
        if p.startswith("docs/evals/phase9-bench-")
        and len(Path(p).parts) == 6
        and Path(p).parts[3] == "quality"
        and p.endswith(".json")
    ]
    by_run = defaultdict(list)
    for path in quality_paths:
        by_run[Path(path).parent.name].append(path)
    # These exact source hashes were committed by the earlier counts-only audit.
    # No arbitrary cache file or operator settings are read.
    if SUPPLEMENT in evidence.paths:
        records = evidence.json(SUPPLEMENT)["records"]
        snapshots = {
            (r["source_directory"], r["source_file"]): r["source_sha256"]
            for r in records
        }
        for (directory, filename), expected in sorted(snapshots.items()):
            path = cache / directory / filename
            if not path.is_file() or path.is_symlink() or path.suffix != ".json":
                continue
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("Cached snapshot does not match committed hash")
            snapshot = json.loads(raw)
            run_id = snapshot["run"]["id"]
            for quality_path in by_run[run_id]:
                folder, variant = Path(quality_path).parts[2], Path(quality_path).stem
                package = next(
                    (
                        p
                        for p in snapshot.get("packages", [])
                        if p["variant"] == variant
                    ),
                    None,
                )
                if package is None:
                    raise ValueError("Cached package identity mismatch")
                saved = evidence.json(quality_path)
                measured = quality_snapshot(package, RedactingFilter())
                for field in ("status", "validation_result", "remaining_findings"):
                    if saved.get(field) != measured.get(field) and not (
                        field == "status"
                        and saved.get(field) == package.get("status")
                        and saved.get(field)
                        in {"production_ready", "not_production_ready"}
                    ):
                        raise ValueError(
                            f"Cached quality mismatch: {quality_path}:{field}"
                        )
                for profile, view in saved.get("profile_assessments", {}).items():
                    if view != measured.get("profile_assessments", {}).get(profile):
                        raise ValueError(
                            "Cached profile does not match historical record"
                        )
                audit = package_audit(snapshot.get("plan"), package)
                add(
                    folder,
                    {"run_id": run_id, **audit},
                    f"verified-cache:{directory}/{filename}",
                )
            sources.append({"path": f"{directory}/{filename}", "sha256": expected})
    rows = []
    for path in quality_paths:
        saved = evidence.json(path)
        folder, run_id, variant = (
            Path(path).parts[2],
            Path(path).parent.name,
            Path(path).stem,
        )
        observation = observations.get((folder, run_id, variant))
        audit, source = observation if observation else (None, None)
        profiles = historical_profiles(evidence, path, saved)
        rows.append(
            {
                "folder": folder,
                "run_id": run_id,
                "variant": variant,
                "status": saved.get("status"),
                "passes": {
                    p: profiles.get(p, {}).get("checks_passed") for p in PROFILES
                },
                "affected": exposure_flip(audit),
                "audit": audit,
                "source": source,
            }
        )
    return rows, sources


def render(report: dict) -> str:
    lines = [
        "# Phase 10b exposure counter-audit",
        "",
        (
            "Counts concern explicit plan-public load balancers that were "
            "public in original files and internal in retained files. Profiles "
            "and historical labels are unchanged. This is static configuration "
            "evidence, not proof of deployment reachability."
        ),
        "",
        (
            "Adjusted rates subtract confirmed affected passes only. When "
            "exposure evidence is missing or unresolved, the true corrected "
            "rate remains unknown; the JSON preserves a pass-count range. "
            "Missing historical profiles remain unavailable. Stub, smoke, "
            "final and broad cohorts are never pooled together."
        ),
        "",
        (
            "| Benchmark folder | Packages / audited | Confirmed affected / "
            "unknown | Strict published → adjusted | v1 published → adjusted | "
            "v2 published → adjusted |"
        ),
        "|---|---:|---:|---|---|---|",
    ]

    def rate(view):
        if not view["recorded_packages"]:
            return "unavailable"
        n = view["recorded_packages"]
        a, b = view["published_passes"], view["corrected_passes"]
        return f"{a}/{n} ({100 * a / n:.1f}%) → {b}/{n} ({100 * b / n:.1f}%)" + (
            "; incomplete" if view["unknown_passing_packages"] else ""
        )

    for row in report["folders"]:
        views = [rate(row["profiles"][p]) for p in PROFILES]
        lines.append(
            f"| {row['folder']} | {row['packages']} / {row['audited']} | "
            f"{row['confirmed_affected']} / {row['unknown']} | "
            + " | ".join(views)
            + " |"
        )
    baseline_names = {
        "phase9-bench-broad-20261020T234203035108Z",
        "phase9-bench-broad-20261021T200436165739Z",
    }
    baseline = [r for r in report["folders"] if r["folder"] in baseline_names]
    if len(baseline) == 2:
        view = [r["profiles"]["strict"] for r in baseline]
        total = sum(r["recorded_packages"] for r in view)
        published = sum(r["published_passes"] for r in view)
        adjusted = sum(r["corrected_passes"] for r in view)
        low = sum(r["corrected_pass_range"][0] for r in view)
        lines += [
            "",
            (
                f"Pooled matched broad baseline: published {published}/{total}; "
                f"confirmed-only adjustment {adjusted}/{total}; unresolved exposure "
                f"leaves a corrected pass-count range of {low}–{adjusted}/{total}. "
                "All three profiles have the same result. The unresolved passing "
                "package is identified in packages.json; "
                "no original exposure is guessed."
            ),
        ]
    lines += [
        "",
        "## Confirmed affected packages",
        "",
        "| Folder | Run | Variant | Stored status |",
        "|---|---|---|---|",
    ]
    for row in report["packages"]:
        if row["affected"]:
            lines.append(
                f"| {row['folder']} | {row['run_id']} | "
                f"{row['variant']} | {row['status']} |"
            )
    lines += [
        "",
        (
            "Rates above are grouped by their original benchmark folder. Plans "
            "without an explicit load balancer are outside this definition; an "
            "incidental generated public LB is not retroactively inferred to "
            "be plan-public."
        ),
        "",
        (
            "Earlier folders without enough source or exposure projection "
            "remain unknown. `packages.json` is a source-free projection with "
            "resource locations and hashes. Raw cache source is never "
            "exported. All consulted committed blobs and verified cache inputs "
            "are hashed in `input-manifest.json`."
        ),
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = (ROOT / args.output_dir).resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError("Choose a fresh repository-local report directory")
    evidence = Evidence(ROOT, args.revision)
    rows, sources = inventory(evidence, args.cache)
    folders = summarize(rows)
    # Include empty/rehearsal benchmark folders without inventing packages.
    listed = {row["folder"] for row in folders}
    for path in sorted(evidence.paths):
        if (
            len(Path(path).parts) == 4
            and path.startswith("docs/evals/phase9-bench-")
            and path.endswith("/results.json")
            and Path(path).parts[2] not in listed
        ):
            folder = Path(path).parts[2]
            folders.append(
                {
                    "folder": folder,
                    "packages": 0,
                    "audited": 0,
                    "confirmed_affected": 0,
                    "unknown": 0,
                    "profiles": {p: {"recorded_packages": 0} for p in PROFILES},
                }
            )
    report = {
        "schema_version": 1,
        "folders": sorted(folders, key=lambda r: r["folder"]),
        "packages": rows,
    }
    content = render(report)
    encoded = json.dumps(report).encode()
    if matches(encoded, set()) or matches(content.encode(), set()):
        raise ValueError("Exposure projection secret scan failed")
    output.mkdir(parents=True)
    write_json(output / "packages.json", report)
    write_json(
        output / "input-manifest.json",
        {
            "evidence_revision": evidence.revision,
            "inputs": [
                {"path": p, "sha256": h} for p, h in sorted(evidence.used.items())
            ],
            "verified_cache": sources,
            "analysis_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    )
    (output / "README.md").write_text(content)
    with (output / "rates.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "folder",
                "profile",
                "recorded_packages",
                "published_passes",
                "affected_passes",
                "corrected_passes",
                "unknown_passing_packages",
            ]
        )
        for folder in report["folders"]:
            for profile, view in folder["profiles"].items():
                writer.writerow(
                    [
                        folder["folder"],
                        profile,
                        *(
                            view.get(k)
                            for k in [
                                "recorded_packages",
                                "published_passes",
                                "affected_passes",
                                "corrected_passes",
                                "unknown_passing_packages",
                            ]
                        ),
                    ]
                )
    print(
        json.dumps(
            {
                "folders": len(folders),
                "packages": len(rows),
                "audited": sum(r["audit"] is not None for r in rows),
                "confirmed_affected": sum(r["affected"] is True for r in rows),
                "unknown": sum(r["affected"] is None for r in rows),
                "secret_findings": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
