"""NFR-01: a self-confirmation cannot accidentally approve a different owner."""

import pytest

from tests.integration.test_phase9l_governance import (
    close,
    decision,
    proposal,
    workspace,
)


@pytest.mark.req("NFR-01", "FR-UI-07")
async def test_obsolete_confirmation_cannot_enable_self_approval(db_engines):
    app, run, users, clients = await workspace(
        db_engines, lessons_admin_direct_activation=False
    )
    try:
        own = (await proposal(clients[0], await decision(app, run, users[0]))).json()
        path = f"/api/lessons/{own['id']}"
        assert (await clients[0].post(path + "/confirmation")).status_code == 403
        assert (
            await clients[0].post(
                path + "/approve", json={"confirmation_token": "historical-token"}
            )
        ).status_code == 403
        assert (await clients[0].get(path)).json()["lesson"]["status"] == "proposed"
    finally:
        await close(clients)
