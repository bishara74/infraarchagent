"""Sequential ArchitectAgent evaluation; writes plans and metrics, never prompts."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.agents.architect import (
    ArchitectAgent,
    ArchitectError,
    ArchitectLLMFailure,
    ArchitectRunInfo,
)
from app.agents.factory import AgentFactory
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.domain.enums import LLMProvider
from app.domain.plan import DeploymentPlan, plan_validation_errors
from app.domain.run_config import RunConfig
from app.llm.stub import StubAdapter

ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "docs/evals"


def _service(name: str, aws_service: str, purpose: str) -> dict[str, str]:
    return {"name": name, "aws_service": aws_service, "purpose": purpose}


def _storage(
    name: str, kind: str, aws_service: str, attached_to: list[str]
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": kind,
        "aws_service": aws_service,
        "attached_to": attached_to,
    }


def _plan(
    services: list[dict[str, str]],
    dependencies: list[tuple[str, str]],
    public: list[str],
    private: list[str],
    storage: list[dict[str, Any]],
    file_types: list[str],
    ambiguities: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "cloud_provider": "aws",
        "services": services,
        "dependencies": [
            {"source": source, "target": target, "description": "Application traffic"}
            for source, target in dependencies
        ],
        "network": {
            "public_services": public,
            "private_services": private,
            "ingress": ["HTTPS 443 from internet"] if public else [],
            "notes": "AWS VPC with private subnets for internal components",
        },
        "storage": storage,
        "file_types": file_types,
        "ambiguities": ambiguities or [],
    }


# These evaluation fixtures live outside app/ and exercise each specified PASS path.
CASES: tuple[tuple[str, str, dict[str, Any]], ...] = (
    (
        "three_tier",
        "Deploy a three-tier AWS web app with an ALB, two application services, "
        "RDS PostgreSQL, and S3 object storage.",
        _plan(
            [
                _service("alb", "Application Load Balancer", "Public ingress"),
                _service("api", "ECS Fargate", "Web API"),
                _service("worker", "ECS Fargate", "Background jobs"),
                _service("postgres", "RDS PostgreSQL", "Relational data"),
                _service("assets", "S3", "Object assets"),
            ],
            [
                ("alb", "api"),
                ("api", "postgres"),
                ("worker", "postgres"),
                ("api", "assets"),
            ],
            ["alb"],
            ["api", "worker", "postgres", "assets"],
            [
                _storage("database", "relational_db", "RDS PostgreSQL", ["postgres"]),
                _storage("objects", "object_storage", "S3", ["assets"]),
            ],
            ["terraform"],
        ),
    ),
    (
        "vague_web_app",
        "build a web app",
        _plan(
            [_service("web", "ECS Fargate", "Serve the web application")],
            [],
            ["web"],
            [],
            [],
            ["terraform"],
            [
                {
                    "topic": "runtime",
                    "detail": "Runtime was not specified",
                    "assumption": "Use a containerized web service",
                }
            ],
        ),
    ),
    (
        "static_site",
        "Deploy a static marketing website on AWS with a CDN and HTTPS.",
        _plan(
            [
                _service("cdn", "CloudFront", "Serve cached pages"),
                _service("origin", "S3", "Store site assets"),
            ],
            [("cdn", "origin")],
            ["cdn"],
            ["origin"],
            [_storage("site-assets", "object_storage", "S3", ["origin"])],
            ["terraform"],
        ),
    ),
    (
        "data_pipeline",
        "Deploy an API ingest pipeline with a message queue, worker services, "
        "and a data warehouse on AWS.",
        _plan(
            [
                _service("ingest", "API Gateway", "Receive events"),
                _service("queue", "SQS", "Buffer events"),
                _service("worker", "ECS Fargate", "Process events"),
                _service("warehouse", "Redshift", "Analyze data"),
            ],
            [("ingest", "queue"), ("worker", "queue"), ("worker", "warehouse")],
            ["ingest"],
            ["queue", "worker", "warehouse"],
            [_storage("analytics", "relational_db", "Redshift", ["warehouse"])],
            ["terraform"],
        ),
    ),
    (
        "kubernetes_monitoring",
        "Deploy containerized microservices on Kubernetes with Helm, Prometheus, "
        "and Grafana monitoring on AWS.",
        _plan(
            [
                _service("cluster", "EKS", "Run Kubernetes workloads"),
                _service("api", "EKS", "Serve the API"),
                _service("metrics", "EKS", "Collect Prometheus metrics"),
                _service("dashboards", "EKS", "Show Grafana dashboards"),
            ],
            [("api", "cluster"), ("metrics", "cluster"), ("dashboards", "metrics")],
            ["api"],
            ["cluster", "metrics", "dashboards"],
            [],
            ["terraform", "kubernetes", "helm", "prometheus", "grafana"],
        ),
    ),
)


def _checks(case: str, plan: DeploymentPlan | None) -> dict[str, bool]:
    checks = {"plan produced": plan is not None}
    if plan is None:
        checks["terraform included"] = False
        checks["dependency graph valid"] = False
        case_check = {
            "three_tier": ("RDS service", "object storage"),
            "vague_web_app": ("ambiguity recorded",),
            "static_site": ("CDN service",),
            "data_pipeline": ("queue service",),
            "kubernetes_monitoring": ("monitoring file types",),
        }
        checks.update({name: False for name in case_check[case]})
        return checks
    services = " ".join(service.aws_service.lower() for service in plan.services)
    kinds = {storage.kind.value for storage in plan.storage}
    types = {kind.value for kind in plan.file_types}
    checks["terraform included"] = "terraform" in types
    checks["dependency graph valid"] = not plan_validation_errors(
        plan.model_dump(mode="json")
    )
    if case == "three_tier":
        checks["RDS service"] = "rds" in services
        checks["object storage"] = "object_storage" in kinds
    elif case == "vague_web_app":
        checks["ambiguity recorded"] = len(plan.ambiguities) >= 1
    elif case == "static_site":
        checks["CDN service"] = "cloudfront" in services or "cdn" in services
    elif case == "data_pipeline":
        checks["queue service"] = "sqs" in services or "queue" in services
    elif case == "kubernetes_monitoring":
        checks["monitoring file types"] = {
            "kubernetes",
            "helm",
            "prometheus",
            "grafana",
        } <= types
    return checks


def _agent(
    settings: Settings,
    provider: LLMProvider,
    model: str | None,
    script: list[str] | None,
) -> ArchitectAgent:
    agent = AgentFactory(settings).create_architect(
        RunConfig(provider=provider, model=model)
    )
    if script is not None:
        assert isinstance(agent.llm_adapter, StubAdapter)
        agent.llm_adapter.load_script(script)
    return agent


def _failed_attempt_errors(info: ArchitectRunInfo | None) -> list[dict[str, Any]]:
    if info is None:
        return []
    return [
        {"attempt": index, "errors": list(errors[:10])}
        for index, errors in enumerate(info.validation_errors_by_attempt, start=1)
        if errors
    ]


def _case_json(
    plan: DeploymentPlan | None,
    checks: dict[str, bool],
    info: ArchitectRunInfo | None,
    *,
    error_category: str | None = None,
    llm_category: str | None = None,
) -> dict[str, Any]:
    return {
        "plan": plan.model_dump(mode="json") if plan is not None else None,
        "checks": checks,
        "error_category": error_category,
        "llm_category": llm_category,
        "validation_errors_by_attempt": _failed_attempt_errors(info),
        "metrics": (
            {
                "plan_attempts": info.plan_attempts,
                "llm_attempts": info.total_llm_attempts,
                "elapsed_seconds": info.elapsed_seconds,
                "input_tokens": info.input_tokens,
                "output_tokens": info.output_tokens,
                "prompt_version": info.prompt_version,
            }
            if info is not None
            else None
        ),
    }


def _append_failure_details(
    rows: list[str],
    errors_by_attempt: list[dict[str, Any]],
    llm_category: str | None,
) -> None:
    for attempt in errors_by_attempt:
        rows.append(f"- Validation errors, attempt {attempt['attempt']}:")
        rows.extend(f"  - {message}" for message in attempt["errors"])
    if llm_category is not None:
        rows.append(f"- LLM category: `{llm_category}`")


async def run_evaluation(
    settings: Settings,
    *,
    provider: LLMProvider,
    model: str | None = None,
    pause_seconds: float = 15,
    output_root: Path = EVALS,
) -> Path:
    if pause_seconds < 0:
        raise ValueError("pause_seconds must be nonnegative")
    if provider is LLMProvider.STUB and model is None:
        model = "stub"
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output = output_root / f"phase2-architect-{provider.value}-{timestamp}"
    output.mkdir(parents=True, exist_ok=False)
    rows: list[str] = [
        "# Phase 2 ArchitectAgent evaluation",
        "",
        f"Provider: `{provider.value}`",
        f"Model: `{model or settings.llm_model or 'stub'}`",
        "",
    ]
    for index, (name, description, fixture) in enumerate(CASES):
        if index and provider is not LLMProvider.STUB and pause_seconds:
            await asyncio.sleep(pause_seconds)
        script = [json.dumps(fixture)] if provider is LLMProvider.STUB else None
        agent = _agent(settings, provider, model, script)
        agent.parse_input(description)
        result: DeploymentPlan | None = None
        error_category: str | None = None
        llm_category: str | None = None
        try:
            result = await agent.generate_plan()
        except ArchitectError as error:
            error_category = error.category
            if isinstance(error, ArchitectLLMFailure):
                llm_category = error.llm_category
        checks = _checks(name, result)
        info = agent.last_run
        case_data = _case_json(
            result,
            checks,
            info,
            error_category=error_category,
            llm_category=llm_category,
        )
        (output / f"{name}.json").write_text(
            json.dumps(case_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        rows.extend([f"## {name}", ""])
        for check, passed in checks.items():
            rows.append(f"- {'PASS' if passed else 'FAIL'}: {check}")
        if error_category:
            rows.append(f"- Error category: `{error_category}`")
        _append_failure_details(
            rows, case_data["validation_errors_by_attempt"], llm_category
        )
        if info:
            rows.extend(
                [
                    f"- Plan attempts: {info.plan_attempts}",
                    f"- LLM attempts: {info.total_llm_attempts}",
                    f"- Elapsed seconds: {info.elapsed_seconds:.3f}",
                    f"- Input/output tokens: {info.input_tokens}/{info.output_tokens}",
                    f"- Prompt version: {info.prompt_version}",
                ]
            )
        rows.append("")

    if provider is LLMProvider.STUB:
        invalid = json.loads(json.dumps(CASES[0][2]))
        invalid["dependencies"][0]["target"] = "unknown-service"
        diagnostic = _agent(
            settings, provider, model, [json.dumps(invalid), json.dumps(CASES[0][2])]
        )
        diagnostic.parse_input(CASES[0][1])
        corrected = await diagnostic.generate_plan()
        assert diagnostic.last_run is not None
        passed = diagnostic.last_run.plan_attempts == 2 and not plan_validation_errors(
            corrected.model_dump(mode="json")
        )
        rows.extend(
            [
                "## correction diagnostic",
                "",
                f"- {'PASS' if passed else 'FAIL'}: invalid dependency corrected "
                "on second plan attempt",
                f"- Plan attempts: {diagnostic.last_run.plan_attempts}",
                f"- LLM attempts: {diagnostic.last_run.total_llm_attempts}",
            ]
        )
        diagnostic_data = _case_json(
            corrected,
            {"invalid dependency corrected": passed},
            diagnostic.last_run,
        )
        _append_failure_details(
            rows, diagnostic_data["validation_errors_by_attempt"], None
        )
        rows.append("")
        (output / "correction_diagnostic.json").write_text(
            json.dumps(diagnostic_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    (output / "summary.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider", choices=[provider.value for provider in LLMProvider]
    )
    parser.add_argument("--model")
    parser.add_argument("--pause-seconds", type=float, default=15)
    args = parser.parse_args()
    settings = get_settings()
    configure_logging(settings.model_copy(update={"log_level": "INFO"}))
    selected = LLMProvider(args.provider or settings.llm_provider)
    output = asyncio.run(
        run_evaluation(
            settings,
            provider=selected,
            model=args.model,
            pause_seconds=args.pause_seconds,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
