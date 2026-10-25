"""NFR-01: a self-confirmation cannot accidentally approve a different owner."""

import pytest

from tests.integration.test_phase9l_governance import (
    close,
    decision,
    proposal,
    workspace,
)


@pytest.mark.req("NFR-01", "FR-UI-07")
async def test_confirmation_rejects_other_proposer_without_consuming_token(db_engines):
    app, run, users, clients = await workspace(
        db_engines, lessons_require_second_approver=False
    )
    admin, reviewer, _ = clients
    try:
        own = (await proposal(admin, await decision(app, run, users[0]))).json()
        other = (await proposal(reviewer, await decision(app, run, users[1]))).json()
        token = (await admin.post(f"/api/lessons/{own['id']}/confirmation")).json()[
            "confirmation_token"
        ]
        response = await admin.post(
            f"/api/lessons/{other['id']}/approve", json={"confirmation_token": token}
        )
        assert (
            response.status_code == 409
            and response.json()["error"] == "lesson_confirmation_mismatch"
        )
        assert (await admin.get(f"/api/lessons/{other['id']}")).json()["lesson"][
            "status"
        ] == "proposed"
        approved = await admin.post(
            f"/api/lessons/{own['id']}/approve", json={"confirmation_token": token}
        )
        assert approved.status_code == 200 and approved.json()["self_approved"]
    finally:
        await close(clients)
