"""FR-UI-06 reproducible compression, safe paths and collision preservation."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.domain.archive import package_zip


@pytest.mark.req("FR-UI-06", "NFR-01")
@pytest.mark.parametrize(
    "collisions,expected",
    [
        ({}, "INFRAARCHAGENT_READINESS.md"),
        ({"INFRAARCHAGENT_READINESS.md": "original"}, "_infraarchagent/READINESS.md"),
        (
            {
                "infraarchagent_readiness.md": "original",
                "_infraarchagent/READINESS.md": "second",
            },
            "_infraarchagent/READINESS-2.md",
        ),
        (
            {
                "INFRAARCHAGENT_READINESS.md": "original",
                "_infraarchagent/readiness.md": "second",
                "_infraarchagent/readiness-2.md": "third",
            },
            "_infraarchagent/READINESS-3.md",
        ),
    ],
)
def test_sorted_deflated_fixed_metadata_and_collision_preservation(
    collisions, expected
):
    files = {"terraform/z.tf": "last", "terraform/a.tf": "first", **collisions}
    first = package_zip(files, "Ready")
    assert first == package_zip(dict(reversed(list(files.items()))), "Ready")
    with ZipFile(BytesIO(first)) as archive:
        assert archive.namelist() == sorted([*files, expected])
        assert archive.read(expected).decode() == "Ready"
        for name, content in files.items():
            assert archive.read(name).decode() == content
        for info in archive.infolist():
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.compress_type == ZIP_DEFLATED
            assert info.external_attr >> 16 == 0o100644


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "files",
    [
        {"../outside": "bad"},
        {"/server/path": "bad"},
        {"a.tf": "first", "A.tf": "second"},
        {"a\\b": "bad"},
    ],
)
def test_zip_revalidates_persisted_paths(files):
    with pytest.raises(ValueError, match="path"):
        package_zip(files, "Ready")


@pytest.mark.req("FR-UI-06", "FR-S-09", "FR-S-10")
@pytest.mark.parametrize(
    "action,retried,expected",
    [
        (None, False, "automatic (clean scan and valid validation)"),
        (
            None,
            True,
            "automatic after an engineer-requested retry "
            "(clean scan and valid validation)",
        ),
        ("approve", True, "engineer decision"),
        ("reject", True, "engineer decision"),
    ],
)
def test_readiness_document_distinguishes_origins(action, retried, expected):
    from datetime import UTC, datetime
    from uuid import uuid4

    from app.domain.archive import readiness_document
    from app.domain.enums import PackageStatus, Variant

    document = readiness_document(
        run_id=uuid4(),
        variant=Variant.COST,
        status=PackageStatus.NOT_PRODUCTION_READY
        if action == "reject"
        else PackageStatus.PRODUCTION_READY,
        model="stub",
        labelled_at=datetime.now(UTC),
        review_action=action,
        feedback=None,
        security_report=None,
        validation_report=None,
        retried=retried,
    )
    assert f"Label origin: {expected}\n" in document
