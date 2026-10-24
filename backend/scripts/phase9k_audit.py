"""Deterministic, source-free LB exposure evidence; never modifies IaC or policy."""

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from app.core.logging import RedactingFilter
from app.core.public_catalogue import digest
from app.security.instances import Instances, Unresolved
from app.validation.documents import blocks
from app.validation.provider_schema import provider_requirements
from scripts.phase9_common import ROOT, write_json
from scripts.phase9d_quality import quality_snapshot
from scripts.phase9k_catalogue import BASELINE_FOLDERS

LB_TYPES = {"aws_lb", "aws_alb", "aws_elb"}
LB_SERVICES = {
    "alb",
    "elb",
    "nlb",
    "elasticloadbalancing",
    "elasticloadbalancingv2",
    "loadbalancer",
    "applicationloadbalancer",
    "networkloadbalancer",
    "awsalb",
    "awselb",
    "awsnlb",
}
BASELINE_AUDIT = "docs/evals/phase9k-baseline-audit/audit.json"
DEFAULT_SOURCE = "https://github.com/hashicorp/terraform-provider-aws/blob/v6.68.0/website/docs/r/lb.html.markdown"


def classification(values: list[str], unknown=False) -> str:
    if unknown or "unknown" in values:
        return "unknown"
    kinds = set(values)
    return (
        "mixed"
        if {"public", "internal"} <= kinds
        else next(iter(kinds))
        if kinds
        else "absent"
    )


def plan_exposure(plan: dict | None) -> dict:
    if (
        not isinstance(plan, dict)
        or not isinstance(plan.get("services"), list)
        or not isinstance(plan.get("network"), dict)
    ):
        return {
            "classification": "unknown",
            "resources": [],
            "reason": "plan_unavailable",
        }
    network = plan["network"]
    public, private = network.get("public_services"), network.get("private_services")
    if not isinstance(public, list) or not isinstance(private, list):
        return {
            "classification": "unknown",
            "resources": [],
            "reason": "network_unavailable",
        }
    rows = []
    for service in plan["services"]:
        label = re.sub(r"[^a-z0-9]", "", str(service.get("aws_service", "")).lower())
        if label not in LB_SERVICES:
            continue
        name = service.get("name")
        view = (
            "public"
            if name in public and name not in private
            else "internal"
            if name in private and name not in public
            else "unknown"
        )
        rows.append(
            {
                "service": name,
                "aws_service": service.get("aws_service"),
                "classification": view,
                "evidence": "network.public_services/private_services",
            }
        )
    return {
        "classification": classification([r["classification"] for r in rows]),
        "resources": rows,
        "reason": "explicit_lb_services_only",
    }


def resource_line(document, resource) -> int | None:
    if document.tree is None:
        return None
    pattern = (
        r'\s*resource\s+"'
        + re.escape(resource.type)
        + r'"\s+"'
        + re.escape(resource.name)
        + r'"\s*\{'
    )
    for block in document.tree.find_data("block"):
        start = getattr(block.meta, "start_pos", None)
        if start is not None and re.match(pattern, document.source[start:]):
            return block.meta.line
    return None


def terraform_exposure(files: dict | None) -> dict:
    if not isinstance(files, dict):
        return {
            "classification": "unknown",
            "resources": [],
            "reason": "files_unavailable",
        }
    try:
        graph = Instances(files)
    except (ValueError, TypeError, KeyError):
        return {
            "classification": "unknown",
            "resources": [],
            "reason": "unparseable_package",
        }
    rows = []
    unknown = any(
        d.parse_error or blocks(d.data, "module")
        for d in graph.package.documents.documents.values()
    )
    modules = sorted({r.module for r in graph.package.resources})
    for module in modules:
        for resource in graph.unknown(module, LB_TYPES):
            rows.append(
                {
                    "file_path": resource.path,
                    "resource": resource.address,
                    "classification": "unknown",
                    "internal": "unresolved",
                    "line": resource_line(
                        graph.package.documents.documents[resource.path], resource
                    ),
                    "source_sha256": hashlib.sha256(
                        files[resource.path].encode()
                    ).hexdigest(),
                }
            )
        aws = provider_requirements(graph.package.documents, module).get("aws", {})
        known_provider = aws.get("source", "hashicorp/aws") in {
            "hashicorp/aws",
            "registry.terraform.io/hashicorp/aws",
        }
        for instance in sorted(graph.all(module, LB_TYPES), key=lambda i: i.address):
            defaulted = "internal" not in instance.resource.body
            # Documented AWS lb/alb default; classic ELB omission stays unknown.
            default = (
                False
                if known_provider and instance.type in {"aws_lb", "aws_alb"}
                else None
            )
            try:
                internal = graph.get(instance, "internal", default)
            except Unresolved:
                internal = None
            if not known_provider:
                internal = None
            view = (
                "internal"
                if internal is True
                else "public"
                if internal is False
                else "unknown"
            )
            rows.append(
                {
                    "file_path": instance.resource.path,
                    "resource": instance.address,
                    "classification": view,
                    "internal": internal if type(internal) is bool else "unresolved",
                    "defaulted": defaulted,
                    "default_source": DEFAULT_SOURCE
                    if defaulted and default is False
                    else None,
                    "line": resource_line(
                        graph.package.documents.documents[instance.resource.path],
                        instance.resource,
                    ),
                    "source_sha256": hashlib.sha256(
                        files[instance.resource.path].encode()
                    ).hexdigest(),
                }
            )
    return {
        "classification": classification(
            [r["classification"] for r in rows], bool(unknown)
        ),
        "resources": rows,
        "has_public": any(r["classification"] == "public" for r in rows),
        "has_internal": any(r["classification"] == "internal" for r in rows),
        "reason": "static_configuration_only",
    }


def package_audit(plan: dict | None, package: dict) -> dict:
    planned = plan_exposure(plan)
    original = terraform_exposure(package.get("original_files"))
    retained = terraform_exposure(package.get("files"))
    return {
        "variant": package["variant"],
        "plan_sha256": digest(plan),
        "original_files_sha256": digest(package.get("original_files")),
        "retained_files_sha256": digest(package.get("files")),
        "plan": planned,
        "original": original,
        "retained": retained,
        "plan_retained_disagreement": planned["classification"]
        != retained["classification"]
        if "unknown" not in {planned["classification"], retained["classification"]}
        else None,
    }


def baseline_audit(evidence, cache: Path) -> dict:
    rows, sources, plans = [], [], []
    redactor = RedactingFilter()
    for number, folder in enumerate(BASELINE_FOLDERS, 1):
        base = "docs/evals/" + folder
        results = evidence.json(base + "/results.json")
        for run in results["runs"]:
            path = cache / f"broad-{number}-results" / (run["run_id"] + ".json")
            raw = path.read_bytes()
            snapshot = json.loads(raw)
            if (
                snapshot.get("run", {}).get("id") != run["run_id"]
                or snapshot["run"].get("status") != run["run_status"]
            ):
                raise ValueError("Cached snapshot run identity/status mismatch")
            if snapshot["run"].get("input_text") != run["prompt"]:
                raise ValueError("Cached snapshot scenario mismatch")
            expected_paths = {
                p
                for p in evidence.paths
                if p.startswith(base + "/quality/" + run["run_id"] + "/")
                and p.endswith(".json")
            }
            packages = snapshot.get("packages", [])
            if len(packages) != len(expected_paths) or len(
                {p["variant"] for p in packages}
            ) != len(packages):
                raise ValueError("Cached snapshot package identity mismatch")
            sources.append(
                {
                    "path": str(path.relative_to(cache)),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            plans.append(
                {
                    "folder": folder,
                    "run_id": run["run_id"],
                    "scenario_id": run["scenario_id"],
                    "complexity": run["complexity"],
                    "plan_sha256": digest(snapshot.get("plan")),
                    **plan_exposure(snapshot.get("plan")),
                }
            )
            for package in packages:
                saved = evidence.json(
                    base
                    + "/quality/"
                    + run["run_id"]
                    + "/"
                    + package["variant"]
                    + ".json"
                )
                measured = quality_snapshot(package, redactor)
                for field in (
                    "status",
                    "validation_result",
                    "remaining_findings",
                    "profile_assessments",
                ):
                    if measured.get(field) != saved.get(field):
                        raise ValueError(
                            "Cached quality differs from committed evidence"
                        )
                rows.append(
                    {
                        "folder": folder,
                        "run_id": run["run_id"],
                        "scenario_id": run["scenario_id"],
                        "complexity": run["complexity"],
                        **package_audit(snapshot.get("plan"), package),
                    }
                )
    return {
        "version": 1,
        "evidence_revision": evidence.revision,
        "sources": sources,
        "packages": rows,
        "plans": plans,
        "analysis_sources": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [
                Path(__file__),
                ROOT / "backend/app/security/instances.py",
                ROOT / "backend/app/security/terraform.py",
                ROOT / "backend/app/validation/documents.py",
            ]
        },
        "input_files": [
            {"path": p, "sha256": h} for p, h in sorted(evidence.used.items())
        ],
        "method": (
            "Explicit structured plan LB services and bounded static Terraform "
            "instances. Unresolved expressions/modules/parsing remain unknown; "
            "absent is not private. Original and retained files are distinct. "
            "Configured scheme does not establish reachability or deployment."
        ),
    }


def main():
    from scripts.phase9b_report import Evidence

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--cache", type=Path, default=ROOT / ".cache")
    parser.add_argument("--output", type=Path, default=ROOT / BASELINE_AUDIT)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Audit output already exists; choose a fresh destination.")
    result = baseline_audit(Evidence(ROOT, args.revision), args.cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, result)
    print(
        json.dumps(
            {
                "packages": len(result["packages"]),
                "sources": len(result["sources"]),
                "retained": dict(
                    Counter(r["retained"]["classification"] for r in result["packages"])
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
