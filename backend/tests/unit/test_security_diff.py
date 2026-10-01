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
