"""FR-A-01 / PR-01 / NFR-01: deterministic audit, denominators and diagnostics."""

from copy import deepcopy

import httpx2
import pytest

from app.core.telemetry import safe_records
from app.llm.base import RetryPolicy
from app.llm.errors import LLMRetryExhausted
from app.llm.openai import OpenAIAdapter
from scripts.phase9k_audit import package_audit, plan_exposure, terraform_exposure
from scripts.phase9k_report import architect_diagnostics, group_experiment, pool
from tests.unit.test_phase9i_broad_report import fixture_benchmark

pytestmark = pytest.mark.req("FR-A-01", "FR-P-04", "PR-01", "NFR-01")


def plan(public=True):
    return {
        "services": [
            {
                "name": "ingress",
                "aws_service": "alb",
                "purpose": "Not used by classification",
            }
        ],
        "network": {
            "public_services": ["ingress"] if public else [],
            "private_services": [] if public else ["ingress"],
        },
    }


@pytest.mark.parametrize(
    "source,expected",
    [
        ('resource "aws_lb" "app" { internal = false }', "public"),
        ('resource "aws_lb" "app" { internal = true }', "internal"),
        ('resource "aws_alb" "app" {}', "public"),
        ('resource "aws_elb" "app" {}', "unknown"),
        ('resource "aws_lb" "app" { internal = var.internal }', "unknown"),
        (
            "locals { internal = true }\n"
            'resource "aws_lb" "app" { internal = local.internal }',
            "internal",
        ),
        ('resource "aws_lb" "app" { count = 0 }', "absent"),
        (
            'resource "aws_lb" "app" { internal = false }\n'
            'resource "aws_lb" "private" { internal = true }',
            "mixed",
        ),
        ('resource "aws_lb" "app" {', "unknown"),
        ('module "app" { source = "./module" }', "unknown"),
    ],
)
def test_terraform_scheme_classifier_is_bounded_and_conservative(source, expected):
    assert (
        terraform_exposure({"terraform/main.tf": source})["classification"] == expected
    )


def test_json_terraform_and_plan_classification_and_source_hashes():
    files = {
        "terraform/main.tf.json": '{"resource":{"aws_lb":{"app":{"internal":true}}}}'
    }
    view = terraform_exposure(files)
    assert view["classification"] == "internal"
    assert view["resources"][0]["resource"] == "aws_lb.app"
    assert len(view["resources"][0]["source_sha256"]) == 64
    assert plan_exposure(plan())["classification"] == "public"
    assert plan_exposure(plan(False))["classification"] == "internal"
    ambiguous = plan()
    ambiguous["network"]["private_services"] = ["ingress"]
    assert plan_exposure(ambiguous)["classification"] == "unknown"
    assert plan_exposure(None)["classification"] == "unknown"
    no_explicit_lb = {
        "services": [
            {"name": "app", "aws_service": "ecs", "purpose": "Public load balancer"}
        ],
        "network": {"public_services": ["app"], "private_services": []},
    }
    assert plan_exposure(no_explicit_lb)["classification"] == "absent"


def test_original_retained_disagreement_is_never_collapsed():
    audit = package_audit(
        plan(),
        {
            "variant": "cost",
            "original_files": {
                "terraform/main.tf": 'resource "aws_lb" "app" { internal = false }'
            },
            "files": {
                "terraform/main.tf": 'resource "aws_lb" "app" { internal = true }'
            },
        },
    )
    assert audit["original"]["classification"] == "public"
    assert audit["retained"]["classification"] == "internal"
    assert audit["plan_retained_disagreement"]
    assert audit["original_files_sha256"] != audit["retained_files_sha256"]


def test_groups_report_specific_blockers_profile_exceptions_and_plan_run_unit():
    benchmark = fixture_benchmark()
    for package in benchmark["packages"]:
        package["remaining_findings"] = {"AWS-0053": 2, "CKV_AWS_91": 1}
        package["profile_assessments"]["contextual-v2"]["excepted"] = [
            {"rule_id": "AWS-0053"}
        ]
    audits = [
        {
            "run_id": p["run_id"],
            "variant": p["variant"],
            "plan": {"classification": "public"},
            "original": {"classification": "public"},
            "retained": {"classification": "internal"},
        }
        for p in benchmark["packages"]
    ]
    rows = group_experiment(benchmark, audits)
    strict = next(
        r
        for r in rows
        if r["dimension"] == "scenario" and r["group"] == 2 and r["profile"] == "strict"
    )
    assert strict["plan_public"] == 1  # two packages share this plan
    assert strict["plan_unknown"] == 1  # second settled run has no generated package
    assert strict["retained_internal"] == 2
    assert strict["AWS-0053_packages"] == 2 and strict["AWS-0053_findings"] == 4
    assert strict["CKV_AWS_91_packages"] == 2
    v2 = next(
        r
        for r in rows
        if r["dimension"] == "scenario"
        and r["group"] == 2
        and r["profile"] == "contextual-v2"
    )
    assert v2["AWS-0053_findings"] == 2
    for package in benchmark["packages"]:
        del package["profile_assessments"]["contextual-v2"]
    assert all(
        r["AWS-0053_packages"] is None
        for r in group_experiment(benchmark, audits)
        if r["dimension"] == "scenario"
        and r["group"] == 2
        and r["profile"] == "contextual-v2"
    )


def test_diagnostics_preserve_unknowns_and_separate_transport_from_quality():
    truncated = {
        "kind": "llm",
        "call_id": "one",
        "role": "architect",
        "reasoning_tokens": 20,
        "input_tokens": 10,
        "output_tokens": 50,
        "elapsed_seconds": 2,
        "category": "truncated",
        "format_reason": "truncated",
        "finish_reason": "length",
    }
    timeout = {
        "kind": "llm",
        "call_id": "two",
        "role": "architect",
        "elapsed_seconds": 1,
        "category": "timeout",
    }
    row = {
        "run_id": "fake",
        "scenario_id": 6,
        "complexity": 4,
        "complete": True,
        "telemetry": [truncated, timeout, truncated],
    }
    view = architect_diagnostics(row, 4)
    assert view["architect_calls"] == 2
    assert view["architect_agent_seconds"] == 4 and view["architect_llm_seconds"] == 3
    assert view["reasoning_tokens"] is None and view["output_tokens"] is None
    assert view["truncated_calls"] == 1 and view["timeout_calls"] == 1
    assert view["unknown_finish_reasons"] == 1
    assert view["finish_reasons"] == {"length": 1, "unknown": 1}


def test_pool_rejects_registration_mismatch():
    a = fixture_benchmark()
    b = deepcopy(a)
    b["registration"]["version"] = "wrong"
    with pytest.raises(ValueError, match="registrations"):
        pool([a, b])


async def test_actual_adapter_attempt_retains_length_and_reasoning_on_truncation():
    def reply(request):
        return httpx2.Response(
            200,
            json={
                "id": "fake",
                "object": "chat.completion",
                "created": 1,
                "model": "test-only/model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "{}"},
                        "finish_reason": "length",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 50,
                    "completion_tokens_details": {"reasoning_tokens": 20},
                },
            },
        )

    adapter = OpenAIAdapter(
        "test-only/model",
        RetryPolicy(1, 1, 2, 0, 100),
        "synthetic-only",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(reply)),
    )
    attempts = []
    with pytest.raises(LLMRetryExhausted):
        await adapter.complete_json("fake", attempt_observer=attempts.append)
    await adapter.client.close()
    assert attempts[0].finish_reason == "length"
    assert attempts[0].reasoning_tokens == 20
    assert attempts[0].format_reason == "truncated"
    assert (
        safe_records([{"kind": "llm", "finish_reason": attempts[0].finish_reason}])[0][
            "finish_reason"
        ]
        == "length"
    )


def comparison_fixture():
    from app.domain.agent_selection import ROLES
    from scripts.phase9k_catalogue import BASELINE_FOLDERS

    datasets = {}
    audit = {"version": 1, "input_files": [], "packages": []}
    for prefix, folder in zip(
        ("a", "b", "e"), (*BASELINE_FOLDERS, "experiment-fixture"), strict=True
    ):
        benchmark = fixture_benchmark()
        benchmark["folder"] = folder
        mapping = {
            r["run_id"]: prefix + str(r["run_id"])
            for r in benchmark["rows"]
            if r.get("run_id")
        }
        for row in benchmark["rows"]:
            if row.get("run_id"):
                row["run_id"] = mapping[row["run_id"]]
        for package in benchmark["packages"]:
            package["run_id"] = mapping[package["run_id"]]
            row = next(
                r for r in benchmark["rows"] if r.get("run_id") == package["run_id"]
            )
            if prefix != "e":
                audit["packages"].append(
                    {
                        "folder": folder,
                        "run_id": package["run_id"],
                        "variant": package["variant"],
                        "scenario_id": row["scenario_id"],
                        "complexity": row["complexity"],
                        **{
                            stage: {"classification": "public"}
                            for stage in ("plan", "original", "retained")
                        },
                    }
                )
        benchmark["environment"]["resolved_agent_selections"] = {
            r["run_id"]: {
                role: {
                    "model": "test-only/architect"
                    if prefix == "e" and role == "architect"
                    else "test-only/baseline",
                    "thinking_mode": "low",
                }
                for role in ROLES
            }
            for r in benchmark["rows"]
            if r.get("run_id")
        }
        if prefix == "e":
            benchmark["environment"]["explicit_architect_model"] = "test-only/architect"
        datasets[folder] = benchmark
    return datasets, audit


def test_complete_comparison_writes_auditable_outputs_without_historical_changes(
    tmp_path, monkeypatch
):
    import json

    from scripts import phase9k_report

    datasets, audit = comparison_fixture()
    original = deepcopy(datasets)
    monkeypatch.setattr(
        phase9k_report,
        "load_broad",
        lambda evidence, folder: deepcopy(datasets[folder]),
    )

    class Evidence:
        paths = set()

        def json(self, path):
            return audit

    (tmp_path / "report.md").write_text("Historical prefix\n")
    phase9k_report.append_experiment_report(Evidence(), "experiment-fixture", tmp_path)
    assert (tmp_path / "report.md").read_text().startswith("Historical prefix\n")
    assert "Architect-model experiment" in (tmp_path / "report.md").read_text()
    report = json.loads((tmp_path / "experiment-comparison.json").read_text())
    assert len(report["groups"]) == 90
    assert len(json.loads((tmp_path / "experiment-architecture.json").read_text())) == 4
    assert (tmp_path / "architect-diagnostics.csv").exists()
    assert (tmp_path / "provider-routing.json").exists()
    assert datasets == original


@pytest.mark.parametrize(
    "failure", ["stub", "smoke", "sibling", "hash", "registration"]
)
def test_comparison_refuses_unmatched_or_unverifiable_evidence(
    tmp_path, monkeypatch, failure
):
    from scripts import phase9k_report

    datasets, audit = comparison_fixture()
    experiment = datasets["experiment-fixture"]
    if failure == "stub":
        experiment["environment"]["mode"] = "stub"
    if failure == "smoke":
        experiment["environment"]["broad_smoke"] = True
    if failure == "sibling":
        for roles in experiment["environment"]["resolved_agent_selections"].values():
            roles["fixer"]["model"] = "test-only/different-fixer"
    if failure == "hash":
        audit["input_files"] = [{"path": "source", "sha256": "0" * 64}]
    if failure == "registration":
        experiment["registration"]["version"] = "different"
    monkeypatch.setattr(
        phase9k_report, "load_broad", lambda evidence, folder: datasets[folder]
    )

    class Evidence:
        paths = set()

        def json(self, path):
            return audit

        def read(self, path):
            return b"changed"

    with pytest.raises(ValueError):
        phase9k_report.append_experiment_report(
            Evidence(), "experiment-fixture", tmp_path
        )


def test_finish_reason_surface_rejects_unrecognised_provider_text():
    from app.core.telemetry import safe_finish_reason

    assert safe_finish_reason("synthetic-secret-canary") is None
    assert safe_records(
        [{"kind": "llm", "finish_reason": "synthetic-secret-canary"}]
    ) == [{"kind": "llm", "finish_reason": None}]


def test_baseline_audit_validates_cached_identity_and_quality(tmp_path, monkeypatch):
    import json

    from app.core.logging import RedactingFilter
    from scripts import phase9k_audit
    from scripts.phase9d_quality import quality_snapshot

    monkeypatch.setattr(phase9k_audit, "BASELINE_FOLDERS", ("test-fixture",))
    package = {
        "variant": "cost",
        "status": "checks_passed",
        "files": {"terraform/main.tf": 'resource "aws_lb" "app" { internal = true }'},
        "original_files": {},
        "validation_report": {"summary": {"result": "valid"}},
    }
    run = {
        "run_id": "fake-run",
        "run_status": "success",
        "prompt": "fake prompt",
        "scenario_id": 1,
        "complexity": 1,
    }
    cached = {
        "run": {"id": "fake-run", "status": "success", "input_text": "fake prompt"},
        "plan": plan(False),
        "packages": [package],
    }
    path = tmp_path / "broad-1-results/fake-run.json"
    path.parent.mkdir()
    path.write_text(json.dumps(cached))

    class Evidence:
        revision = "test-revision"
        paths = {"docs/evals/test-fixture/quality/fake-run/cost.json"}
        used = {}

        def json(self, path):
            return (
                {"runs": [run]}
                if path.endswith("results.json")
                else quality_snapshot(package, RedactingFilter())
            )

    result = phase9k_audit.baseline_audit(Evidence(), tmp_path)
    assert len(result["packages"]) == len(result["plans"]) == 1
    assert result["packages"][0]["retained"]["classification"] == "internal"
    cached["run"]["id"] = "different-run"
    path.write_text(json.dumps(cached))
    with pytest.raises(ValueError, match="identity"):
        phase9k_audit.baseline_audit(Evidence(), tmp_path)
