import json
from pathlib import Path

import pytest

from app.core.config import Settings
from scripts.eval_generators import _prices, run_evaluation


def settings() -> Settings:
    url = "postgresql+asyncpg://unused:unused@localhost/unused"
    return Settings(
        _env_file=None,
        database_url=url,
        migration_database_url=url,
        test_database_url=url,
        test_migration_database_url=url,
        llm_provider="stub",
        llm_api_key="sk-ant-api03-CANARY-7f3c9e2a1b4d5e6f",
    )


@pytest.mark.req("FR-G-01", "FR-G-02", "FR-G-03", "FR-G-04", "FR-G-05")
async def test_stub_evaluation_has_six_results_correction_and_reports(
    tmp_path: Path,
) -> None:
    output = await run_evaluation(
        settings(),
        models=["stub"],
        price_in={"stub": 1},
        price_out={"stub": 2},
        output_root=tmp_path,
    )
    data = json.loads((output / "results.json").read_text())
    summary = (output / "summary.md").read_text()
    assert len(data["cases"]) == 6
    assert all(row["success"] for row in data["cases"])
    assert len(data["triples"]) == 2
    assert all(row["mode"] == "parallel" for row in data["triples"])
    corrected = next(
        row
        for row in data["cases"]
        if row["plan"] == "kubernetes_monitoring" and row["variant"] == "cost"
    )
    assert corrected["package_attempts"] == 2
    assert corrected["structure_error_counts"] == [4, 0]
    assert any(not check["passed"] for row in data["cases"] for check in row["checks"])
    assert any(check["passed"] for row in data["cases"] for check in row["checks"])
    assert all(row["notes"] for row in data["cases"])
    assert data["totals"]["stub"]["estimated_cost"] == pytest.approx(0.035)
    assert "Notes: Cost uses small" in summary
    assert "PASS:" in summary and "FAIL:" in summary
    assert "three-variant parallel wall time" in summary
    assert "CANARY" not in summary
    assert "<deployment_plan>" not in summary
    assert not (output / "packages").exists()


@pytest.mark.req("FR-G-01", "NFR-01")
async def test_sequential_comparison_and_saved_paths(tmp_path: Path) -> None:
    output = await run_evaluation(
        settings(),
        models=["stub", "comparison"],
        plans=["three_tier"],
        mode="sequential",
        save_packages=True,
        output_root=tmp_path,
    )
    data = json.loads((output / "results.json").read_text())
    assert len(data["cases"]) == 6
    assert all(row["mode"] == "sequential" for row in data["triples"])
    assert data["totals"]["stub"]["estimated_cost"] is None
    assert len(list((output / "packages").rglob("main.tf"))) == 6
    summary = (output / "summary.md").read_text()
    assert "stub outcome" in summary and "comparison outcome" in summary


def test_price_argument_validation() -> None:
    assert _prices("a=1,b=2.5") == {"a": 1.0, "b": 2.5}
    for invalid in ("a", "=1", "a=-1", "a=nan", "a=inf"):
        with pytest.raises(ValueError):
            _prices(invalid)
