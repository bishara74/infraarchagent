"""FR-S-01/02, NFR-01: recordings, syntax boundaries and offline scanners."""

import json
import shutil
from pathlib import Path

import pytest

from app.domain.enums import Severity, Variant
from app.scanners.trivy_parser import parse_trivy
from app.security.policy import VARIANT_EXEMPTIONS, classify
from tests.unit.test_scanners import FIXTURES, files, recorded_output

CORPUS = json.loads((FIXTURES / "terraform-diagnostics.json").read_text())["cases"]
TOOLS_AVAILABLE = all(shutil.which(tool) for tool in ("checkov", "trivy", "terraform"))


@pytest.mark.req("FR-S-01")
def test_trivy_recorded_ids_locations_and_avdid_precedence() -> None:
    root = FIXTURES / "vulnerable"
    raw = recorded_output("trivy", "vulnerable")
    parsed = parse_trivy(raw, root, set(files("vulnerable")))
    encrypted = next(item for item in parsed if item.rule_id == "AWS-0080")
    assert (
        encrypted.severity,
        encrypted.file_path,
        encrypted.resource,
        encrypted.line_start,
        encrypted.line_end,
    ) == (Severity.HIGH, "terraform/main.tf", "aws_db_instance.db", 17, 17)
    privileged = next(item for item in parsed if item.rule_id == "KSV-0017")
    assert (privileged.file_path, privileged.line_start, privileged.line_end) == (
        "k8s/deployment.yaml",
        15,
        19,
    )
    data = json.loads(raw)
    for result in data["Results"]:
        for entry in result.get("Misconfigurations", []):
            entry["AVDID"] = "AVD-TEST-0001"
    assert {
        item.rule_id
        for item in parse_trivy(json.dumps(data), root, set(files("vulnerable")))
    } == {"AVD-TEST-0001"}


@pytest.mark.req("FR-S-01")
@pytest.mark.parametrize(
    "data",
    [
        {"Results": []},
        {"SchemaVersion": 2},
        {"Results": [{"Target": "ignored", "Misconfigurations": None}]},
    ],
)
def test_empty_trivy_reports(data: object) -> None:
    assert parse_trivy(json.dumps(data), Path("/tmp/package"), set()) == []


@pytest.mark.req("FR-S-01")
@pytest.mark.parametrize("status", ["PASS", "EXCEPTION", "WARN", None])
def test_only_trivy_fail_is_kept(status: object) -> None:
    data = {
        "Results": [{"Target": "outside", "Misconfigurations": [{"Status": status}]}]
    }
    assert parse_trivy(json.dumps(data), Path("/tmp/package"), set()) == []


@pytest.mark.req("FR-S-01", "NFR-01")
@pytest.mark.parametrize(
    "path",
    [
        "../escape.tf",
        "/outside.tf",
        "terraform/unknown.tf",
        "terraform/../main.tf",
        "C:\\secret.tf",
    ],
)
def test_trivy_paths_are_confined(path: str) -> None:
    data = {
        "Results": [
            {
                "Target": path,
                "Misconfigurations": [
                    {"Status": "FAIL", "ID": "AWS-0080", "Severity": "HIGH"}
                ],
            }
        ]
    }
    with pytest.raises(ValueError):
        parse_trivy(json.dumps(data), Path("/tmp/package"), {"terraform/main.tf"})


@pytest.mark.req("FR-S-01")
@pytest.mark.parametrize(
    "data",
    [
        [],
        {"Results": {}},
        {"Results": [None]},
        {"Results": [{"Misconfigurations": [None]}]},
        {"Results": [{"Misconfigurations": {}}]},
    ],
)
def test_malformed_trivy_report(data: object) -> None:
    with pytest.raises(ValueError):
        parse_trivy(json.dumps(data), Path("/tmp/package"), set())


@pytest.mark.req("FR-S-02")
def test_all_trivy_exemptions_are_confirmed_by_a_recorded_failure() -> None:
    parsed = parse_trivy(
        recorded_output("trivy", "vulnerable"),
        FIXTURES / "vulnerable",
        set(files("vulnerable")),
    )
    emitted = {item.rule_id: item for item in parsed}
    exemptions = {
        (variant, rule)
        for variant, rule in VARIANT_EXEMPTIONS
        if not rule.startswith("CKV")
    }
    assert exemptions == {(Variant.COST, "AWS-0133")}
    for variant, rule in exemptions:
        item = emitted[rule]
        assert classify([item], variant)[0].advisory_reason.startswith(
            "variant_exemption:"
        )
        for other in set(Variant) - {variant}:
            assert not (classify([item], other)[0].advisory_reason or "").startswith(
                "variant_exemption:"
            )
        # The emitted rule is LOW today; security never changes its classification
        # via an exemption if the embedded rule severity changes in the future.
        assert classify(
            [item.model_copy(update={"severity": Severity.HIGH})], Variant.SECURITY
        )[0].blocking
