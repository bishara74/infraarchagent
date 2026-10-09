"""FR-V-01–04: offline evaluation, complete outcomes and immutable inputs."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.domain.validation import ValidationCheck, ValidationReport
from scripts import eval_validation


class Reports:
    versions = {"terraform": "1.16.4", "helm": None}
    mirror = Path("/not-present")

    async def validate(self, plan, files):
        source = files["terraform/main.tf"]
        if source == "error":
            check = ValidationCheck(
                check_id="terraform.validate",
                category="terraform",
                tool="terraform",
                status=("skipped"),
                skip_reason=("mirror_missing"),
                message=("Provider mirror unavailable"),
            )
        else:
            failed = source == "invalid"
            check = ValidationCheck(
                check_id="terraform.validate",
                category="terraform",
                tool="terraform",
                status="failed" if failed else "passed",
                file_path="terraform/main.tf",
                line_start=1,
                message=("Invalid resource type")
                if failed
                else ("Configuration is valid"),
            )
        warning = ValidationCheck(
            check_id=("naming.unknown"),
            category=("naming"),
            tool=("builtin"),
            status=("warning"),
            file_path="terraform/main.tf",
            line_start=1,
            message="Unknown service name",
        )
        return ValidationReport.build(
            [check, warning], terraform_required=True, tool_versions=self.versions
        )


def package(tmp_path, variant, source):
    folder = tmp_path / "model/three_tier" / variant
    (folder / "terraform").mkdir(parents=True)
    (folder / "terraform/main.tf").write_text(source)
    return folder


@pytest.mark.req("FR-V-01", "FR-V-02", "FR-V-03", "FR-V-04", "NFR-01")
async def test_results_counts_versions_skips_and_original_files(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "canary-key")
    folders = [
        package(tmp_path, variant, source)
        for variant, source in zip(
            ["cost", "performance", "security"],
            ["valid", "invalid", "error"],
            strict=True,
        )
    ]
    before = {
        folder: eval_validation.source_digest(eval_validation.load_files(folder))
        for folder in folders
    }
    output = await eval_validation.run_evaluation(
        packages=folders, output_root=tmp_path, engine=Reports()
    )
    raw = (output / "results.json").read_text()
    data = json.loads(raw)
    assert data["totals"] == {"valid": 1, "invalid": 1, "error": 1}
    assert data["offline"] is True and data["mirror_present"] is False
    assert data["tool_versions"] == Reports.versions
    invalid = next(case for case in data["cases"] if case["result"] == "invalid")
    assert invalid["failed_by_category"] == {"terraform": 1}
    assert invalid["report"]["failed_checks_for_remediation"][0]["line_start"] == 1
    error = next(case for case in data["cases"] if case["result"] == "error")
    assert error["skip_reasons"] == {"mirror_missing": 1}
    assert all(
        case[("duration_seconds")] >= 0 and case[("warnings")] == 1
        for case in data[("cases")]
    )
    assert before == {
        folder: eval_validation.source_digest(eval_validation.load_files(folder))
        for folder in folders
    }
    assert "canary-key" not in raw and str(tmp_path) not in raw
    summary = (output / "summary.md").read_text()
    assert "Aurora cluster without database instances" in summary
    assert all(result in summary for result in ("valid", "invalid", "error"))


@pytest.mark.req("FR-V-03", "NFR-01")
def test_defaults_are_same_twelve_original_security_evaluator_packages():
    from scripts.eval_security import PHASE3, _default_packages

    assert eval_validation.PHASE3 == PHASE3
    assert eval_validation.default_packages() == _default_packages()
    assert len(eval_validation.default_packages()) == 12


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("unsafe", [".env", "terraform/external.tf"])
async def test_unsafe_input_refused_before_file_reads(tmp_path, monkeypatch, unsafe):
    folder = package(tmp_path, "security", "valid")
    target = folder / unsafe
    if unsafe == ".env":
        target.touch()  # Empty synthetic file; its contents are never read.
    else:
        target.symlink_to(tmp_path / "outside.tf")
        (tmp_path / "outside.tf").write_text("canary-key")
    original = Path.read_text

    def guarded(path, *args, **kwargs):
        assert not path.is_relative_to(folder), "No package content should be read"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded)
    output = await eval_validation.run_evaluation(
        packages=[folder], output_root=tmp_path, engine=Reports()
    )
    case = json.loads((output / "results.json").read_text())["cases"][0]
    assert case["result"] == "error"
    assert case[("source_sha256")] is None and case[("skip_reasons")] == {
        ("input_unavailable"): 1
    }


@pytest.mark.req("NFR-01")
def test_evaluator_imports_no_database_settings_or_llm(tmp_path):
    backend = Path(__file__).parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            ("-c"),
            (
                "import sys; from scripts import eval_validati"
                "on; assert not any(n.startswith(('app.db', 'a"
                "pp.llm', 'app.core.config')) for n in sys.mod"
                "ules)"
            ),
        ],
        env={"PATH": os.defpath, "PYTHONPATH": str(backend), "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr


@pytest.mark.req("FR-V-04")
async def test_empty_selection_refused(tmp_path):
    with pytest.raises(ValueError, match="no packages"):
        await eval_validation.run_evaluation(
            packages=[], output_root=tmp_path, engine=Reports()
        )


@pytest.mark.req("FR-V-03", "FR-V-04")
@pytest.mark.parametrize("failed", [False, True])
async def test_known_syntax_confirmation_uses_terraform_file_and_line(tmp_path, failed):
    class Syntax(Reports):
        async def validate(self, plan, files):
            return ValidationReport.build(
                [
                    ValidationCheck(
                        check_id="terraform.validate",
                        category="terraform",
                        tool="terraform",
                        status="failed" if failed else "passed",
                        file_path="terraform/main.tf",
                        line_start=172,
                        message="Invalid expression"
                        if failed
                        else "Configuration is valid",
                    )
                ],
                terraform_required=True,
                tool_versions=self.versions,
            )

    folder = tmp_path / "openai_gpt-oss/model"
    folder = folder.parent / "kubernetes_monitoring/cost"
    (folder / "terraform").mkdir(parents=True)
    (folder / "terraform/main.tf").write_text("terraform {}")
    output = await eval_validation.run_evaluation(
        packages=[folder], output_root=tmp_path, engine=Syntax()
    )
    data = json.loads((output / "results.json").read_text())
    assert data["known_syntax_failures_confirmed"] == {
        "gpt-oss/kubernetes_monitoring/cost": failed
    }
