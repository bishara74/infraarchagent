"""Traceability extraction/reporting tests, without claiming requirement coverage."""

import json
import subprocess
import sys

import pytest

from scripts.phase9_common import BACKEND, ROOT, collection_environment
from scripts.phase9_report import statistics_for
from scripts.traceability import build_report, identifiers, playwright_tests


@pytest.mark.parametrize(
    "text,expected",
    [
        ("FR-A-01--05", {f"FR-A-{n:02}" for n in range(1, 6)}),
        ("FR-UI-01..07", {f"FR-UI-{n:02}" for n in range(1, 8)}),
        ("FR-UI-06/07 PR-03 UC-08", {"FR-UI-06", "FR-UI-07", "PR-03", "UC-08"}),
        ("FR-S-09–10", {"FR-S-09", "FR-S-10"}),
    ],
)
def test_id_expansion(text, expected):
    assert identifiers(text) == expected


def test_report_preserves_overlap_unknown_and_uncovered():
    tests = [
        {
            "framework": "pytest",
            "file": "a.py",
            "node_id": "a",
            "ids": ["FR-P-04", "PR-99"],
        }
    ]
    report = build_report(
        {"FR-P-04", "NFR-04"},
        tests * 2,
        json.loads((ROOT / "docs/traceability-map.json").read_text()),
    )
    covered = next(r for r in report["requirements"] if r["requirement"] == "FR-P-04")
    assert covered["counts"]["pytest"] == 1
    assert covered["tc_groups"] == ["TC-pipeline-01", "TC-ui-01"]
    assert report["uncovered"] == ["NFR-04"]
    assert report["invalid_annotations"]


def test_playwright_title_hierarchy_and_projects():
    rows = playwright_tests(
        [
            {
                "title": "PR-02",
                "suites": [
                    {
                        "title": "nested",
                        "specs": [
                            {
                                "id": "test",
                                "title": "FR-UI-01..02",
                                "file": "a.spec.ts",
                                "tests": [
                                    {"projectName": "chromium"},
                                    {"projectName": "firefox"},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    )
    assert len(rows) == 2
    assert rows[0]["ids"] == ["FR-UI-01", "FR-UI-02", "PR-02"]
    assert rows[0]["node_id"] != rows[1]["node_id"]


def test_real_pytest_collection_inherited_and_parameter_markers(tmp_path):
    source = tmp_path / "test_collection.py"
    source.write_text("""import pytest
pytestmark = pytest.mark.req("NFR-01")
@pytest.mark.req("FR-P-04")
class TestGroup:
    @pytest.mark.parametrize("value", [
        pytest.param(1, marks=pytest.mark.req("PR-03")), 2
    ])
    def test_value(self, value):
        raise RuntimeError("test body must not run")
""")
    output = tmp_path / "collected.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-p",
            "scripts.pytest_traceability",
            "--traceability-output",
            str(output),
            str(source),
        ],
        cwd=BACKEND,
        env=collection_environment(),
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == 0
    rows = json.loads(output.read_text())
    assert len(rows) == 2
    assert set(rows[0]["ids"]) == {"NFR-01", "FR-P-04", "PR-03"}
    assert set(rows[1]["ids"]) == {"NFR-01", "FR-P-04"}


def test_statistics_unknown_empty_even_and_nearest_rank():
    assert statistics_for([])["median"] is None
    assert statistics_for([1, 2, 3, 4]) == {
        "count": 4,
        "median": 2.5,
        "p90": 4,
        "max": 4,
    }
    assert statistics_for([float("nan"), 1, 3])["median"] == 2
