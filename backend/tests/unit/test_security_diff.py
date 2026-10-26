"""FR-S-06: only paths changed across passes enter cumulative diffs."""

import pytest

from app.security.diff import package_diff


@pytest.mark.req("FR-S-06")
def test_cumulative_diff_omits_byte_identical_files() -> None:
    before = {"terraform/a.tf": "a\n", "terraform/b.tf": "b\n"}
    after = dict(before)
    after["terraform/a.tf"] = "changed\n"
    after["terraform/c.tf"] = "new\n"
    diff = package_diff(before, after)
    assert "a/terraform/a.tf" in diff
    assert "b/terraform/c.tf" in diff
    assert "--- /dev/null" in diff
    assert "terraform/b.tf" not in diff
    assert before["terraform/b.tf"] == after["terraform/b.tf"]


@pytest.mark.req("FR-S-06", "UC-04")
def test_cumulative_diff_spans_changed_added_deleted_and_reverted_files():
    original = {
        "terraform/a.tf": "before\n",
        "terraform/deleted.tf": "old\n",
        "terraform/reverted.tf": "same\n",
    }
    final = {
        "terraform/a.tf": "after\n",
        "terraform/new.tf": "new\n",
        "terraform/reverted.tf": "same\n",
    }
    diff = package_diff(original, final)
    assert diff == (
        "--- a/terraform/a.tf\n+++ b/terraform/a.tf\n@@ -1 +1 @@\n-before\n+after\n"
        "--- a/terraform/deleted.tf\n+++ /dev/null\n@@ -1 +0,0 @@\n-old\n"
        "--- /dev/null\n+++ b/terraform/new.tf\n@@ -0,0 +1 @@\n+new\n"
    )


@pytest.mark.req("FR-S-06", "UC-04")
def test_missing_final_newline_has_standard_unified_diff_markers():
    assert package_diff({"terraform/a.tf": "before"}, {"terraform/a.tf": "after"}) == (
        "--- a/terraform/a.tf\n+++ b/terraform/a.tf\n@@ -1 +1 @@\n"
        "-before\n\\ No newline at end of file\n"
        "+after\n\\ No newline at end of file\n"
    )
