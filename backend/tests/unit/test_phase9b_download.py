"""PR-04: offline attribution summaries preserve the maximum threshold."""

import pytest


@pytest.mark.req("PR-04")
def test_download_attribution_uses_maximum_and_discloses_missing_conditions():
    from scripts.phase9b_download import summarize

    report = summarize(
        [
            {"condition": "session", "seconds": 1.0},
            {"condition": "session", "seconds": 2.1},
            {"condition": "shared_key", "seconds": 1.5},
        ]
    )
    assert report["session"]["median"] == 1.55
    assert report["session"]["verdict"] == "FAIL"
    assert report["shared_key"]["verdict"] == "PASS"
    assert report["prevalidated_session"]["verdict"] == "INCOMPLETE"
