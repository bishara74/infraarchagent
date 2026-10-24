"""FR-S-04/08: contextual success never changes persisted readiness."""

from io import BytesIO
from unittest.mock import Mock
from zipfile import ZipFile

import pytest

from app.db.repositories.packages import PackageRepository
from app.db.repositories.runs import RunRepository
from app.domain.enums import Variant
from tests.integration.test_pipeline_review import client_for, pending_app, review_url
from tests.unit.test_policy_profiles import log_resources, package, source


@pytest.mark.req("FR-S-04", "FR-S-08", "FR-UI-06")
async def test_contextual_success_cannot_promote_label_and_is_archived(db_engines):
    app, run = await pending_app(db_engines[0], result="valid", blocking=True)
    files = source(log_resources())
    value = package(
        files, "AWS-0132", "aws_s3_bucket_server_side_encryption_configuration.logs"
    )
    async with app.state.session_factory() as session, session.begin():
        row = await RunRepository(session).get(run)
        row.policy_profile = "contextual-v1"
        await PackageRepository(session).save_security_results(
            run,
            Variant.COST,
            original_files=files,
            files=files,
            session_report={
                "kind": "automated",
                "final": value["security_report"]["final"],
            },
            iteration_count=1,
            policy_version="3",
            prompt_version="6",
            tools={},
        )
    async with client_for(app) as c:
        data = (await c.get(f"/api/pipeline/{run}/results")).json()
        item = data["packages"][0]
        assert data["run"]["policy_profile"] == "contextual-v1"
        assert item["readiness_label"] == "pending_review"
        assert not item["profile_assessments"]["strict"]["checks_passed"]
        assert item["profile_assessments"]["contextual-v1"]["checks_passed"]
        assert item["profile_assessments"]["contextual-v2"]["checks_passed"]
        assert not item["downloadable"]
        await c.post(
            review_url(run),
            json={
                "action": "approve",
                "reviewer_name": "Ada",
                "category": "other",
                "reason": "Reviewed strict blockers",
            },
        )
        item = (await c.get(f"/api/pipeline/{run}/results")).json()["packages"][0]
        assert item["readiness_label"] == "engineer_approved"
        assert len(item["security_report"]["final"]["remaining_blocking"]) == 1
        response = await c.get(f"/api/pipeline/{run}/download/cost")
        with ZipFile(BytesIO(response.content)) as z:
            text = z.read("INFRAARCHAGENT_READINESS.md").decode()
        for expected in [
            "# ENGINEER APPROVED",
            "contextual-v1",
            "contextual-v2",
            "s3-log-target-sse-s3",
            "excepted:",
            "AWS-0132",
        ]:
            assert expected in text


@pytest.mark.req("FR-S-04", "FR-I-04", "FR-P-04")
async def test_run_profile_is_persisted_and_in_acceptance_event(
    db_engines, monkeypatch
):
    app, _ = await pending_app(db_engines[0])
    monkeypatch.setattr(app.state.runner, "start", Mock())
    async with client_for(app) as c:
        response = await c.post(
            "/api/pipeline/run",
            json={
                "text": "Deploy an AWS application with Terraform",
                "config": {"provider": "stub", "policy_profile": "contextual-v1"},
            },
        )
        assert response.status_code == 202
        from uuid import UUID

        run = UUID(response.json()["run_id"])
        async with app.state.session_factory() as session:
            assert (
                await RunRepository(session).get(run)
            ).policy_profile == "contextual-v1"
        events = await app.state.event_log.list_after(run, None)
        assert events[0].payload["policy_profile"] == "contextual-v1"
        assert (
            await c.post(
                "/api/pipeline/run",
                json={
                    "text": "Deploy an AWS application with Terraform",
                    "config": {"policy_profile": "../unknown"},
                },
            )
        ).status_code == 400
    app.state.runner.release()
