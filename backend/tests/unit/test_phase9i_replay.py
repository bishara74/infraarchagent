"""FR-V-01/FR-S-04/NFR-01: replay projections contain evidence, not source."""

import pytest

from scripts.phase9i_replay import aggregate, digest, projection

pytestmark = pytest.mark.req("FR-V-01", "FR-S-04", "NFR-01")


def test_digest_is_content_bound_and_order_independent():
    assert digest({"a": 1, "b": 2}) == digest({"b": 2, "a": 1})
    assert digest({"a": 1}) != digest({"a": 2})


def test_projection_preserves_unknown_and_does_not_export_source():
    result = projection({"files": {"README.md": "PRIVATE_SOURCE_CANARY"}})
    assert result["scan_outcome"] == "unknown"
    assert not result["profiles"]["strict"]["checks_passed"]
    assert "PRIVATE_SOURCE_CANARY" not in str(result)
    summary = aggregate([{"observed": result}])
    assert summary["scan_unknown"] == 1
    assert summary["validation"] == {"error": 1}
