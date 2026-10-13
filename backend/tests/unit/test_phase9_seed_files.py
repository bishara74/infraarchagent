import pytest

from app.domain.archive import package_zip
from scripts.seed_benchmark_package import calibrated_files


@pytest.mark.req("PR-04")
def test_seeded_content_is_reproducible_and_nontrivially_compressible():
    first = calibrated_files(704, 100_000, "synthetic readiness")
    assert first == calibrated_files(704, 100_000, "synthetic readiness")
    assert first != calibrated_files(705, 100_000, "synthetic readiness")
    archive = package_zip(first, "synthetic readiness")
    assert 99_500 <= len(archive) <= 100_000
    assert sum(map(len, first.values())) > len(archive) * 1.2
