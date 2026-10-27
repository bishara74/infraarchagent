"""Deterministic author lesson demonstration; scan first, no settings or inference."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.domain.lessons import content_hash, render_lessons
from app.security.instances import Instance, Instances, Ref, Unresolved
from app.security.terraform import TerraformPackage, objects
from scripts.phase9_common import ROOT, write_json
from scripts.secret_scan import matches

FOLDER = ROOT / "docs/evals/phase10b-author-lesson-runs"
NETWORK = {
    "aws_vpc",
    "aws_subnet",
    "aws_internet_gateway",
    "aws_nat_gateway",
    "aws_eip",
    "aws_route_table",
    "aws_default_route_table",
    "aws_main_route_table_association",
    "aws_route_table_association",
    "aws_route",
    "aws_vpc_endpoint",
    "aws_ecs_service",
}


def refs(value: Any) -> list[Ref]:
    if isinstance(value, Ref):
        return [value]
    if isinstance(value, dict):
        return [r for v in value.values() for r in refs(v)]
    return (
        [r for v in value for r in refs(v)] if isinstance(value, (list, tuple)) else []
    )


def route_table(graph: Instances, subnet: Instance) -> tuple[Instance, list[dict]]:
    matches = [
        graph.linked(i, "route_table_id")
        for i in graph.all(subnet.module, {"aws_route_table_association"})
        if graph.linked(i, "subnet_id") == subnet
    ]
    if len(matches) != 1 or matches[0] is None:
        raise Unresolved()
    table = matches[0]
    routes = objects(graph.get(table, "route", []))
    for item in graph.all(subnet.module, {"aws_route"}):
        if graph.linked(item, "route_table_id") == table:
            routes.append(
                {
                    k: graph.get(item, k)
                    for k in item.resource.body
                    if k not in {"count", "for_each", "provider"}
                }
            )
    return table, routes


def default_route(route: dict) -> bool:
    return any(
        route.get(k) == v
        for k, v in [
            ("cidr_block", "0.0.0.0/0"),
            ("destination_cidr_block", "0.0.0.0/0"),
            ("ipv6_cidr_block", "::/0"),
            ("destination_ipv6_cidr_block", "::/0"),
        ]
    )


def public_subnet(graph: Instances, subnet: Instance) -> bool:
    table, routes = route_table(graph, subnet)
    vpc = graph.linked(subnet, "vpc_id")
    if vpc is None or graph.linked(table, "vpc_id") != vpc:
        raise Unresolved()
    for route in routes:
        gateway = route.get("gateway_id")
        if default_route(route) and isinstance(gateway, Ref):
            igw = graph.find(gateway.module, gateway.address)
            if (
                igw
                and igw.type == "aws_internet_gateway"
                and graph.linked(igw, "vpc_id") == vpc
            ):
                return True
    return False


def outbound(graph: Instances) -> tuple[str, dict]:
    subnets = []
    unknown = False
    for module in {r.module for r in graph.package.resources}:
        unknown |= bool(graph.unknown(module, {"aws_ecs_service"}))
        for service in graph.all(module, {"aws_ecs_service"}):
            try:
                networks = objects(
                    service.resource.body.get("network_configuration", [])
                )
                for network in networks:
                    for reference in refs(
                        graph.value(
                            network.get("subnets", []), service.module, service.env
                        )
                    ):
                        subnet = graph.find(reference.module, reference.address)
                        if subnet is None:
                            raise Unresolved()
                        subnets.append(subnet)
            except (Unresolved, TypeError, ValueError):
                unknown = True
    unresolved_instances = sorted(
        r.address
        for r in graph.package.resources
        if graph.expanded.get((r.module, r.address)) is None
    )
    proven = 0
    for subnet in subnets:
        try:
            _, routes = route_table(graph, subnet)
            for route in routes:
                nat = route.get("nat_gateway_id")
                if not default_route(route) or not isinstance(nat, Ref):
                    continue
                instance = graph.find(nat.module, nat.address)
                placement = graph.linked(instance, "subnet_id") if instance else None
                if (
                    instance
                    and instance.type == "aws_nat_gateway"
                    and placement
                    and public_subnet(graph, placement)
                ):
                    proven += 1
                    break
        except (Unresolved, TypeError, ValueError):
            unknown = True
    nats = sum(r.type == "aws_nat_gateway" for r in graph.package.resources)
    endpoints = [r for r in graph.package.resources if r.type == "aws_vpc_endpoint"]
    services = {
        name: sum(name in str(r.body.get("service_name", "")) for r in endpoints)
        for name in ["ecr.api", "ecr.dkr", "logs", "secretsmanager"]
    }
    status = (
        "followed"
        if subnets and proven == len(subnets) and not unknown
        else "not_followed"
        if not nats and not all(services.values())
        else "not_followed"
        if subnets
        and not unknown
        and proven < len(subnets)
        and not all(services.values())
        else "unknown"
    )
    return status, {
        "nat_gateways": nats,
        "vpc_endpoints": len(endpoints),
        "endpoint_services": services,
        "task_subnets": len(subnets),
        "proven_nat_routes": proven,
        "resolution_unknown": unknown,
        "unresolved_instances": unresolved_instances,
    }


def az_identity(graph: Instances, subnet: Instance) -> str | None:
    for field in ("availability_zone", "availability_zone_id"):
        raw = subnet.resource.body.get(field)
        try:
            value = graph.get(subnet, field)
            if isinstance(value, str) and "${" not in value:
                return field + ":" + value
        except Unresolved:
            pass
        if isinstance(raw, str):
            if "count" in subnet.env:
                raw = raw.replace("count.index", str(subnet.env["count"]["index"]))
            match = re.fullmatch(
                r"\$\{(data\.aws_availability_zones\.[\w-]+)\.names\[([0-9]+)\]\}", raw
            )
            if match:
                return match[1] + ":" + match[2]
    return None


def inspect(files: dict[str, str]) -> dict:
    package = TerraformPackage(files)
    resources = list(package.resources)
    identities = Counter((r.module, r.address) for r in resources)
    lbs = [r for r in resources if r.type in {"aws_lb", "aws_alb", "aws_elb"}]
    lb_rows = [
        {
            "resource": r.address,
            "file_path": r.path,
            "internal": r.body.get("internal", "omitted"),
            "access_logs": bool(r.body.get("access_logs")),
            "access_logs_enabled": any(
                b.get("enabled") is True for b in objects(r.body.get("access_logs", []))
            ),
        }
        for r in lbs
    ]
    # Inspect only the network dependency subgraph. Unrelated duplicate logging/LB
    # blocks do not erase independent NAT evidence. Relevant duplicates, modules,
    # unknown count/for_each/variables and parse failures still remain unknown.
    package.resources = [r for r in resources if r.type in NETWORK]
    graph = Instances(files, package=package)
    outbound_status, outbound_facts = outbound(graph)
    duplicate_count = sum(n - 1 for n in identities.values() if n > 1)
    logs = (
        "followed"
        if len(lbs) == 1 and duplicate_count == 0 and lb_rows[0]["access_logs_enabled"]
        else "not_followed"
    )
    exposure = "unknown"
    placements = []
    zones = []
    if len(lbs) == 1:
        lb = lbs[0]
        flag = lb.body.get("internal", False if lb.type != "aws_elb" else None)
        if flag is True:
            exposure = "not_followed"
        elif flag is False:
            try:
                values = graph.value(lb.body.get("subnets", []), lb.module)
                attached = refs(values)
                if len(attached) != len(values):
                    raise Unresolved()
                for ref in attached:
                    subnet = graph.find(ref.module, ref.address)
                    if subnet is None:
                        raise Unresolved()
                    placements.append(public_subnet(graph, subnet))
                    zones.append(az_identity(graph, subnet))
                same_basis = (
                    len({z.rsplit(":", 1)[0] for z in zones if z is not None}) == 1
                )
                exposure = (
                    "not_followed"
                    if placements and not all(placements)
                    else "followed"
                    if len(placements) >= 2
                    and all(placements)
                    and None not in zones
                    and same_basis
                    and len(set(zones)) >= 2
                    else "unknown"
                )
            except (Unresolved, TypeError, ValueError):
                pass
    return {
        "outbound": outbound_status,
        "outbound_evidence": outbound_facts,
        "logging_and_no_duplicates": logs,
        "duplicate_resource_blocks": duplicate_count,
        "load_balancers": lb_rows,
        "public_lb_two_az": exposure,
        "public_subnet_evidence": placements,
        "az_identities": zones,
        "parse_errors": sum(
            d.parse_error for d in package.documents.documents.values()
        ),
    }


def analyse(snapshots: list[tuple[str, dict]]) -> dict:
    runs = []
    calls = []
    issues = []
    rows = []
    for filename, snapshot in snapshots:
        manifest = snapshot["run"]["lessons"]
        entries = manifest["entries"]
        if content_hash(entries) != manifest["set_hash"]:
            issues.append({"file": filename, "issue": "set_hash_mismatch"})
        seen = set()
        for call in snapshot.get("telemetry", []):
            if (
                call.get("kind") != "llm"
                or not call.get("call_id")
                or call["call_id"] in seen
            ):
                continue
            seen.add(call["call_id"])
            role = call.get("role", "")
            block, ids = render_lessons(entries, role)
            usage = call.get("lesson_usage") or {}
            expected = bool(block and manifest["lessons_enabled"])
            ok = bool(usage.get("enabled")) == expected
            if expected:
                ok &= (
                    usage.get("lesson_ids") == ids
                    and usage.get("block_hash") == content_hash(block)
                    and usage.get("set_hash") == manifest["set_hash"]
                )
            if not ok:
                issues.append(
                    {
                        "file": filename,
                        "call_id": call["call_id"],
                        "role": role,
                        "issue": "scope_or_hash_mismatch",
                    }
                )
            calls.append(
                {
                    "file": filename,
                    "call_id": call["call_id"],
                    "role": role,
                    "outcome": call.get("outcome"),
                    "enabled": bool(usage.get("enabled")),
                    "lesson_ids": usage.get("lesson_ids", []),
                    "block_hash": usage.get("block_hash"),
                    "verified": ok,
                }
            )
        run_name = filename.split("-")[0]
        lesson_ids = {}
        for entry in entries:
            text = entry["text"]
            number = (
                1
                if text.startswith("ECS tasks")
                else 2
                if text.startswith("Configure load balancer access logs")
                else 3
                if text.startswith("When users reach")
                else None
            )
            if number is None:
                raise ValueError("Unrecognized author lesson identity")
            lesson_ids[number] = entry
        for package in snapshot["packages"]:
            original = inspect(package["original_files"])
            final = inspect(package["files"])
            variant = package["variant"]
            role = "generator_" + variant
            results = {}
            for number, property_ in [
                (1, "outbound"),
                (2, "logging_and_no_duplicates"),
                (3, "public_lb_two_az"),
            ]:
                entry = lesson_ids.get(number)
                applicable = entry is not None and bool(
                    render_lessons([entry], role)[0]
                )
                results[str(number)] = (
                    original[property_] if applicable else "not_applicable"
                )
            rows.append(
                {
                    "run": run_name,
                    "variant": variant,
                    "lessons": results,
                    "original": original,
                    "final": final,
                    "status": package["status"],
                }
            )
        plan = snapshot["plan"]
        runs.append(
            {
                "run": run_name,
                "file": filename,
                "plan_sha256": content_hash(plan),
                "request_sha256": content_hash(snapshot["run"].get("input_text")),
                "set_version": manifest["set_version"],
                "service_names": [s["name"] for s in plan["services"]],
                "public_services": plan["network"]["public_services"],
                "private_services": plan["network"]["private_services"],
                "storage_entries": len(plan["storage"]),
            }
        )
    return {
        "schema_version": 1,
        "runs": runs,
        "rows": rows,
        "calls": calls,
        "telemetry_issues": issues,
        "method": (
            "Static configured network subgraph, exact original/retained "
            "maps, bounded resolver, no variable-default deployment "
            "assumptions. Distinct literal AZs or indices into the same AWS "
            "AZ-name data source are configured diversity only. Logging "
            "requires enabled access_logs and no duplicate resource blocks. "
            "Followed does not prove runtime startup or deployment."
        ),
    }


def render(report: dict) -> str:
    labels = {
        "followed": "followed",
        "not_followed": "not followed",
        "not_applicable": "not applicable",
        "unknown": "unknown",
    }
    lines = [
        "# Author lesson runs — deterministic analysis",
        "",
        (
            "One run per configuration demonstrates the lesson mechanism; it "
            "is not a measured lesson effect. Plans differ between runs. All "
            "judgments below use Generator original files; retained-file "
            "changes are reported separately. No LLM, provider request or "
            "deployment was performed."
        ),
        "",
        (
            "| Run | Variant | Lesson 1: outbound | Lesson 2: logging / "
            "duplicates | Lesson 3: public LB / two AZs |"
        ),
        "|---|---|---|---|---|",
    ]
    for row in report["rows"]:
        lines.append(
            "| "
            + row["run"]
            + " | "
            + row["variant"]
            + " | "
            + " | ".join(labels[row["lessons"][str(i)]] for i in [1, 2, 3])
            + " |"
        )
    request_hashes = {r["request_sha256"] for r in report["runs"]}
    lines += [
        "",
        (
            f"Exact request-text hashes: {len(request_hashes)} distinct across "
            f"{len(report['runs'])} runs; structured plan hashes: "
            f"{len({r['plan_sha256'] for r in report['runs']})} distinct."
        ),
    ]
    enabled = Counter(c["role"] for c in report["calls"] if c["enabled"])
    roles = Counter(c["role"] for c in report["calls"])
    lines += [
        "",
        "## Scope and provenance",
        "",
        (
            f"Telemetry contains {len(report['calls'])} distinct model attempts: "
            f"{dict(roles)}. Lesson-enabled attempts: {dict(enabled)}. "
            f"Scope/set/block-hash mismatches: {len(report['telemetry_issues'])}. "
            "All lesson-bearing calls are Generator calls; Architect/Fixer calls "
            "record no lesson use. The manifest call list omits calls without "
            "lesson usage, so telemetry is the comparison source."
        ),
        "",
        "## Original versus retained files",
        "",
        (
            "| Run / variant | Original → final LB flags | Original → final "
            "access-log blocks | Duplicate blocks, original → final | "
            "Outbound, original → final |"
        ),
        "|---|---|---|---:|---|",
    ]
    for row in report["rows"]:
        a, b = row["original"], row["final"]

        def flags(view):
            return (
                ", ".join(str(lb["internal"]).lower() for lb in view["load_balancers"])
                or "absent"
            )

        def logs(view):
            return sum(lb["access_logs"] for lb in view["load_balancers"])

        lines.append(
            f"| {row['run']} / {row['variant']} | {flags(a)} → {flags(b)} | "
            f"{logs(a)} → {logs(b)} | {a['duplicate_resource_blocks']} → "
            f"{b['duplicate_resource_blocks']} | {labels[a['outbound']]} → "
            f"{labels[b['outbound']]} |"
        )
    lines += [
        "",
        (
            "Lesson 1 reaches all three Generators in runs 2–4; the run-3 "
            "security Generator has two attempts. NAT declarations alone are "
            "insufficient: `analysis.json` records task-subnet default NAT "
            "routes and the NAT placement’s default Internet Gateway route. "
            "No VPC endpoint resources occur in these snapshots. Relevant "
            "ambiguous network bindings remain unknown."
        ),
        "",
        (
            "The run-2 performance original has a duplicate LB declaration "
            "containing access logs. After lesson 2, the run-3 performance "
            "original has no duplicate but also no access_logs block: that "
            "is not full instruction following. Run 4 performance restores "
            "access logs in its single LB. This coincidence is not "
            "attributed causally to the lesson. Other variants also change "
            "despite not receiving lesson 2."
        ),
        "",
        (
            "Run-3 cost/security and run-4 performance change internal=false "
            "to true during remediation. Run-3 cost and run-4 performance "
            "carry checks_passed. These are Fixer-stage changes, not "
            "evidence that the Generators ignored internet-facing intent. "
            "Run-1 cost also changes to internal=true, but its duplicated "
            "original LB prevents a unique static exposure classification."
        ),
        "",
        "Run 4 performance attaches its tasks to subnets with an IGW default "
        "route and disables public task IPs; its declared NAT has no task-subnet "
        "default route. Run 4 security has private NAT routes but its NAT subnet "
        "has no default IGW route. These do not establish working outbound access. "
        "Other unknown cases include input-dependent subnet instance counts; "
        "run 3 security references count.index in a route table without count. "
        "The analysis does not assume variable defaults are deployment inputs.",
        "",
        "## Plan differences and limits",
        "",
    ]
    for run in report["runs"]:
        lines.append(
            f"- {run['run']}: plan `{run['plan_sha256']}`, services "
            f"{', '.join(run['service_names'])}; public "
            f"{', '.join(run['public_services'])}; private "
            f"{', '.join(run['private_services'])}; "
            f"{run['storage_entries']} storage entries."
        )
    lines += [
        "",
        report["method"],
        "",
        (
            "Distinct configured AZ identities do not prove available "
            "capacity or successful deployment. Unknown does not mean "
            "followed or not followed. `not applicable` means the lesson was "
            "absent or not scoped to that Generator; baseline structural "
            "observations remain in the JSON."
        ),
        "",
        (
            "Run 4’s self-approved provenance is correct for the older "
            "active lesson copy. The author reports a later admin-direct "
            "duplicate that was retired. Legacy approval_actor=null was "
            "never an approval-time identity snapshot; current history "
            "display may join today’s user row (D-60/D-63)."
        ),
        "",
    ]
    return "\n".join(lines)


def main():
    paths = sorted(FOLDER.glob("run*.json"))
    allowed = set(
        json.loads((ROOT / "docs/secret-scan-allowlist.json").read_text())[
            "exact_values"
        ]
    )
    raw = [(p, p.read_bytes()) for p in paths]
    findings = [
        {"file": p.name, "line": line, "pattern": pattern}
        for p, data in raw
        for line, pattern in matches(data, allowed)
    ]
    if findings:
        raise ValueError("Author evidence secret scan failed; do not commit")
    report = analyse([(p.name, json.loads(data)) for p, data in raw])
    if report["telemetry_issues"]:
        raise ValueError("Author telemetry verification failed")
    markdown = render(report)
    if matches(json.dumps(report).encode(), allowed) or matches(
        markdown.encode(), allowed
    ):
        raise ValueError("Analysis secret scan failed")
    write_json(FOLDER / "analysis.json", report)
    write_json(
        FOLDER / "input-manifest.json",
        {
            "files": [
                {"path": p.name, "sha256": hashlib.sha256(data).hexdigest()}
                for p, data in raw
            ],
            "analysis_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "secret_scan": {"input_files": len(raw), "findings": 0, "scan_errors": 0},
        },
    )
    (FOLDER / "README.md").write_text(markdown)
    print(
        json.dumps(
            {
                "runs": len(report["runs"]),
                "rows": len(report["rows"]),
                "calls": len(report["calls"]),
                "enabled_calls": sum(c["enabled"] for c in report["calls"]),
                "telemetry_issues": len(report["telemetry_issues"]),
                "secret_findings": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
