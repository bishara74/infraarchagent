"""FR-S-04/NFR-01: safe per-package metrics and valid-only near misses."""

import json

import pytest

from app.core.logging import RedactingFilter
from scripts.phase9d_quality import quality_snapshot, quality_table


def package(n=1, result="valid"):
    return {
        "status": "pending_review",
        "files": {"terraform/main.tf": "SOURCE_CANARY"},
        "security_report": {
            "final": {"remaining_blocking": [{"rule_id": "RULE"}] * n},
            "sessions": [
                {
                    "fixing_model": "anthropic/haiku-scripted",
                    "fixing_provider": "openai",
                    "fixing_reasoning_effort": "off",
                    "fix_max_findings": 12,
                    "fix_attempt_timeout_seconds": 45,
                    "iteration_timeout_seconds": 60,
                    "security_stage_timeout_seconds": 240,
                    "iterations": [
                        {
                            "source": "SOURCE_CANARY",
                            "verification": {
                                "catalogue": [
                                    {
                                        "control": "deletion",
                                        "resource": "aws_db_instance.db",
                                        "rule_ids": ["AWS-0177"],
                                        "status": "retained",
                                        "reason": "secure_default",
                                        "source": "SOURCE_CANARY",
                                    }
                                ],
                                "templates": [
                                    {
                                        "template": "access_logs",
                                        "status": "rejected",
                                        "reason": "new_blocking_findings",
                                        "introduced_findings": [
                                            {
                                                "rule_id": "CKV_AWS_18",
                                                "source": "SOURCE_CANARY",
                                            }
                                        ],
                                    }
                                ],
                                "partial_groups": [
                                    {"status": "kept"},
                                    {"status": "discarded"},
                                ],
                            },
                            "fixes": [
                                {
                                    "findings_sent": 11,
                                    "resources_sent": 2,
                                    "normalized_existing_paths": [
                                        "terraform/variables.tf"
                                    ],
                                    "recovered_existing_proposal": True,
                                    "summaries": ["SOURCE_CANARY"],
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        "validation_report": {
            "summary": {"result": result},
            "remediation": {
                "generator_security_context_chars": 1400,
                "generator_context_truncated": True,
            },
        },
    }


@pytest.mark.req("FR-S-04", "NFR-01")
def test_safe_metrics_round_trip_and_model_limits():
    source = package()
    source["validation_report"]["remediation"]["generation_syntax"] = {
        "path": "syntax_round_2",
        "normalizations": [{"source": "SOURCE_CANARY"}],
        "rounds": [{"diagnostic": "SOURCE_CANARY"}] * 2,
        "regeneration": "not_needed",
        "excerpt": "SOURCE_CANARY",
    }
    source["security_report"]["sessions"][0]["iterations"][0]["verification"].update(
        publication_seconds=0.25, cancellation_seconds=0.1
    )
    value = quality_snapshot(source, RedactingFilter())
    assert "SOURCE_CANARY" not in json.dumps(value)
    assert value["phase9f"]["generation_syntax"] == {
        "path": "syntax_round_2",
        "normalizations": 1,
        "rounds": 2,
        "regeneration": "not_needed",
    }
    assert value["phase9f"]["iteration_timings"][0]["publication_seconds"] == 0.25
    result, text = quality_table([json.loads(json.dumps(value))])
    metrics = result["phase9f"]
    assert metrics["catalogue_retained_by_rule"] == {"AWS-0177": 1}
    assert metrics["template_introduced_rules"] == {"CKV_AWS_18": 1}
    assert metrics["partial_groups"] == {"kept": 1, "discarded": 1}
    assert metrics["existing_file_proposals"] == {"normalized": 1, "retained": 1}
    assert metrics["generation_syntax_paths"] == {"syntax_round_2": 1}
    model = metrics["fixer_models"][0]
    assert model["model"] == "anthropic/haiku-scripted"
    assert model["fix_attempt_timeout_seconds"] == [45]
    assert model["iteration_timeout_seconds"] == [60]
    assert model["findings_per_call"]["max"] == 11
    assert "SOURCE_CANARY" not in text


@pytest.mark.req("FR-S-04")
def test_near_misses_require_final_validity_and_historical_metrics_stay_unknown():
    inputs = [package(n) for n in (1, 2, 3, 4)] + [package(1, "invalid")]
    old = {
        "status": "pending_review",
        "security_report": {"final": {"remaining_blocking": []}},
    }
    values = [quality_snapshot(p, RedactingFilter()) for p in [*inputs, old]]
    assert values[-1]["phase9f"]["existing_file_proposals"] is None
    assert values[-1]["phase9f"]["generation_syntax"]["path"] is None
    result, text = quality_table(values)
    assert result["phase9f"]["near_misses"] == {"1": 1, "2-3": 2, "4+": 1}
    assert result["phase9f"]["packages_unknown"] == 1
    assert result["phase9f"]["validation_unknown"] == 1
    assert result["phase9f"]["generation_syntax_paths"] == {"unknown": 6}
    assert "Valid package remaining blockers" in text
