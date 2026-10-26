"""NFR-01 / FR-UI-07: policy migration and decision-specific categories."""

import pytest
from pydantic import ValidationError

from app.api.schemas import ReviewRequest
from app.core.config import Settings
from app.domain.review_categories import APPROVAL_CATEGORIES, REJECTION_CATEGORIES

pytestmark = pytest.mark.req("NFR-01", "FR-UI-07")


@pytest.mark.parametrize(
    "action,allowed",
    [("approve", APPROVAL_CATEGORIES), ("reject", REJECTION_CATEGORIES)],
)
def test_categories_match_decision(action, allowed):
    for category in APPROVAL_CATEGORIES | REJECTION_CATEGORIES:
        body = dict(action=action, category=category, reason="Recorded judgement")
        if category in allowed:
            assert ReviewRequest(**body).category == category
        else:
            with pytest.raises(ValidationError):
                ReviewRequest(**body)


@pytest.mark.parametrize("old,new", [(True, False), (False, True)])
def test_legacy_policy_mapping_and_new_precedence(monkeypatch, caplog, old, new):
    from app.core import config

    monkeypatch.setattr(config, "_legacy_lesson_warning_emitted", False)
    keys = dict(
        database_url="unused",
        migration_database_url="unused",
        test_database_url="unused",
        test_migration_database_url="unused",
    )
    assert Settings(_env_file=None, **keys).lessons_admin_direct_activation
    first = Settings(_env_file=None, **keys, lessons_require_second_approver=old)
    assert first.lessons_admin_direct_activation is new
    override = Settings(
        _env_file=None,
        **keys,
        lessons_require_second_approver=old,
        lessons_admin_direct_activation=old,
    )
    assert override.lessons_admin_direct_activation is old
    assert caplog.text.count("is deprecated") == 1
    assert "LESSONS_ADMIN_DIRECT_ACTIVATION" in caplog.text
