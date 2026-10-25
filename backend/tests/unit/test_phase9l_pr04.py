"""PR-04/NFR-01: assessment reuse preserves fixed archive and evidence bytes."""

import copy
import hashlib
import json
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace
from uuid import UUID
from zipfile import ZipFile

import pytest

from app.core.config import Settings
from app.domain.archive import bundle_zip
from app.domain.enums import PackageStatus, Variant
from app.domain.lessons import content_hash, empty_snapshot
from app.pipeline import results
from app.security.profiles import assess, assess_v1
from app.security.profiles_v2 import assess_v2
from tests.unit.test_policy_profiles import (
    log_resources,
    network_resources,
    package,
    source,
)

pytestmark = pytest.mark.req("PR-04", "FR-S-04", "FR-UI-06", "NFR-01")
RUN = UUID("00000000-0000-4000-8000-000000000704")
STAMP = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)
CANARY = "pr04-snapshot-secret-canary"


def fixed_packages():
    logs = package(
        source(log_resources()),
        "AWS-0132",
        "aws_s3_bucket_server_side_encryption_configuration.logs",
    )
    network = package(source(network_resources()), "AWS-0053", "aws_lb.edge")
    malformed = copy.deepcopy(logs)
    malformed["files"]["terraform/broken.tf"] = 'resource "aws_s3_bucket" "broken" {'
    counted = copy.deepcopy(network)
    data = json.loads(counted["files"]["terraform/main.tf.json"])
    data["resource"]["aws_lb"]["edge"]["count"] = 2
    counted["files"]["terraform/main.tf.json"] = json.dumps(data)
    hcl = {
        "files": {
            "terraform/main.tf": 'resource "aws_s3_bucket" "data" {}\n',
            "kubernetes/pod.yaml": (
                "apiVersion: v1\nkind: Pod\nmetadata:\n  name: fixed\n"
            ),
        },
        "security_report": {"final": {"outcome": "clean", "remaining_blocking": []}},
        "validation_report": {"summary": {"result": "valid"}},
    }
    unknown = {"files": {}, "security_report": None, "validation_report": None}
    return {
        "logs": logs,
        "network": network,
        "malformed": malformed,
        "counted": counted,
        "hcl": hcl,
        "unknown": unknown,
    }


def fixed_snapshot_outputs():
    """Also used to capture actual pre-edit bytes outside the repository."""
    settings = Settings(
        _env_file=None,
        database_url="snapshot-unused",
        migration_database_url="snapshot-unused",
        test_database_url="snapshot-unused",
        test_migration_database_url="snapshot-unused",
        llm_api_key=CANARY,
    )
    service = results.ResultsService(None, settings)
    output = {}
    for case, value in fixed_packages().items():
        entries = [
            {
                "id": str(RUN),
                "lesson_id": str(RUN),
                "revision": 1,
                "scope_role": "generator_cost",
                "text": "Prefer clear storage notes.",
                "self_approved": True,
            }
        ]
        lessons = {
            **empty_snapshot("eligible"),
            "lessons_enabled": True,
            "set_version": 3,
            "set_hash": content_hash(entries),
            "entries": entries,
            "self_approved": True,
        }
        usage = {
            "enabled": True,
            "self_approved": True,
            "set_version": 3,
            "set_hash": lessons["set_hash"],
            "block_hash": content_hash("fixed"),
            "reason": "used",
            "lesson_ids": [str(RUN)],
        }
        snapshot = SimpleNamespace(
            run=SimpleNamespace(
                model="stub",
                agent_models=None,
                policy_profile="contextual-v1",
                lessons=lessons,
            ),
            telemetry=[
                {
                    "kind": "llm",
                    "id": str(RUN),
                    "call_id": str(RUN),
                    "role": "generator_cost",
                    "outcome": "success",
                    "lesson_usage": usage,
                }
            ],
            lesson_uses=[],
        )
        output[f"{case}/assessments.json"] = json.dumps(
            results.assess(value), sort_keys=True, ensure_ascii=False
        ).encode()
        packages = {}
        for variant, status in zip(
            Variant,
            [
                PackageStatus.ENGINEER_APPROVED,
                PackageStatus.CHECKS_PASSED,
                PackageStatus.REJECTED,
            ],
            strict=True,
        ):
            files = {
                **value["files"],
                "INFRAARCHAGENT_READINESS.md": "User readiness\n",
                "_infraarchagent/LESSONS.json": "User lessons\n",
                "notes.txt": CANARY,
            }
            row = SimpleNamespace(
                status=status,
                files=files,
                security_report=value["security_report"],
                validation_report=value["validation_report"],
                review_feedback=f"Reviewed {CANARY}",
                review_decision={
                    "action": "reject"
                    if status == PackageStatus.REJECTED
                    else "approve",
                    "reviewer_name": "Fixed engineer",
                    "decided_at": STAMP.isoformat(),
                    "reason": "Fixed decision",
                    "category": "other",
                },
            )
            label = SimpleNamespace(
                timestamp=STAMP,
                payload={
                    "review_action": None
                    if status == PackageStatus.CHECKS_PASSED
                    else row.review_decision["action"]
                },
            )
            archive, name = service._archive(
                RUN, variant, snapshot, row, None if case == "unknown" else label, True
            )
            output[f"{case}/{variant.value}.zip"] = archive
            packages[variant] = archive, name, status.value
        output[f"{case}/bundle.zip"] = bundle_zip(
            RUN, packages, lessons=service.safety.value(results.run_lessons(snapshot))
        )
    return output


def independent_assess(package, files=None):
    """Independent evaluator inputs, matching the pre-reuse call structure."""
    legacy = assess_v1(package, files)
    return {
        **legacy,
        "contextual-v2": assess_v2(
            package, files if files is not None else package.get("files") or {}, legacy
        ),
    }


def test_fixed_snapshots_match_independent_evaluators_byte_for_byte(monkeypatch):
    optimized = fixed_snapshot_outputs()
    monkeypatch.setattr(results, "assess", independent_assess)
    independent = fixed_snapshot_outputs()
    assert optimized == independent
    for path, data in optimized.items():
        if not path.endswith(".zip"):
            continue
        with ZipFile(BytesIO(data)) as archive:
            assert all(
                CANARY.encode() not in archive.read(p) for p in archive.namelist()
            )
            if path.endswith("bundle.zip"):
                manifest = json.loads(archive.read("manifest.json"))
                for name, digest in manifest["files"].items():
                    assert hashlib.sha256(archive.read(name)).hexdigest() == digest
                for variant in Variant:
                    single = optimized[f"{path.split('/')[0]}/{variant.value}.zip"]
                    assert (
                        manifest["variants"][variant.value]["single_variant_zip"][
                            "sha256"
                        ]
                        == hashlib.sha256(single).hexdigest()
                    )


@pytest.mark.parametrize(
    "files_override", [None, {}, {"terraform/other.tf": "terraform {}"}]
)
@pytest.mark.parametrize("case", list(fixed_packages()))
def test_all_profiles_preserve_overrides_and_input_bytes(case, files_override):
    value = fixed_packages()[case]
    before = copy.deepcopy(value)
    assert assess(value, files_override) == independent_assess(value, files_override)
    assert value == before


@pytest.mark.parametrize("file_count", [1, 50, 129])
def test_each_terraform_document_is_parsed_once_per_assessment(monkeypatch, file_count):
    import hcl2

    original = hcl2.parses_to_tree
    parsed = []

    def counted(source):
        parsed.append(source)
        return original(source)

    monkeypatch.setattr(hcl2, "parses_to_tree", counted)
    files = {
        f"terraform/file-{i:03}.tf": f'resource "aws_s3_bucket" "bucket{i}" {{}}'
        for i in range(file_count)
    }
    value = {"files": files}
    assess(value)
    assert parsed == [files[path] for path in sorted(files)]
    parsed.clear()
    # No process-wide reuse, even when the next call keeps the same path.
    files["terraform/file-000.tf"] = 'resource "aws_s3_bucket" "changed" {'
    assess(value)
    assert parsed == [files[path] for path in sorted(files)]
