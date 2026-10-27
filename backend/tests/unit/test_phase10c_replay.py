"""FR-P-04/NFR-01: replay requires exact retained bytes and trusted input scope."""

import pytest

from app.security.diff import package_diff
from scripts.phase10c_replay import apply_diff, finding_keys, source

pytestmark = pytest.mark.req("FR-P-04", "FR-S-07", "NFR-01")


@pytest.mark.parametrize(
    "before,after",
    [
        ({"terraform/main.tf": "a\nb\nc\n"}, {"terraform/main.tf": "a\nc\n"}),
        ({"terraform/main.tf": "no newline"}, {"terraform/main.tf": "different\n"}),
        (
            {"terraform/main.tf": "a\n"},
            {"terraform/main.tf": "a\n", "terraform/new.tf": "new"},
        ),
        (
            {"terraform/main.tf": "a\n", "terraform/old.tf": "old"},
            {"terraform/main.tf": "a\n"},
        ),
        ({"terraform/main.tf": ""}, {"terraform/main.tf": "new\n"}),
        ({"README.md": "-- header\n"}, {"README.md": "++ header\n"}),
    ],
)
def test_recorded_diff_round_trip(before, after):
    patch = package_diff(before, after)
    assert apply_diff(before, patch) == after
    assert apply_diff(after, patch, True) == before


def test_wrong_baseline_is_never_silently_patched():
    patch = package_diff(
        {"terraform/main.tf": "before\n"}, {"terraform/main.tf": "after\n"}
    )
    with pytest.raises(ValueError, match="context mismatch"):
        apply_diff({"terraform/main.tf": "different\n"}, patch)


def test_diff_cannot_escape_package_paths():
    with pytest.raises(ValueError):
        apply_diff({}, "--- /dev/null\n+++ b/../escape\n@@ -0,0 +1 @@\n+new\n")


def test_dotenv_input_refused_without_opening(monkeypatch):
    from pathlib import Path

    from scripts.phase10c_replay import ROOT

    def forbidden(*args, **kwargs):
        raise AssertionError("dotenv read")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(ValueError, match="non-dotenv"):
        source(ROOT / ".env")


def test_findings_keep_rule_resource_and_path_identity():
    assert finding_keys(
        [
            {
                "rule_id": "X",
                "resource": "aws_lb.edge[0]",
                "file_path": "terraform/main.tf",
            }
        ]
    ) == {("X", "aws_lb.edge[0]", "terraform/main.tf")}
