import pytest

from app.domain.paths import UnsafePathError, validate_file_map, validate_relative_path


@pytest.mark.parametrize(
    "path", ["main.tf", "modules/web/main.tf", ".hidden", "a_1-2.x"]
)
def test_accepted_paths(path: str) -> None:
    assert validate_relative_path(path) == path


@pytest.mark.parametrize(
    "path",
    [
        "",
        "../x",
        "a/../b",
        "/etc/passwd",
        "C:/x",
        "a\\b",
        "a//b",
        "./a",
        "a/./b",
        "a/",
        "a\x00b",
        "x" * 256,
        "a/a/a/a/a/a/a/a/a",
        "space name.tf",
        "é.tf",
    ],
)
def test_rejected_paths(path: str) -> None:
    with pytest.raises(UnsafePathError):
        validate_relative_path(path)


def test_file_map_rejects_duplicates_and_non_text() -> None:
    with pytest.raises(UnsafePathError):
        validate_file_map({"Main.tf": "a", "main.tf": "b"})
    with pytest.raises(ValueError):
        validate_file_map({"main.tf": 4})  # type: ignore[dict-item]
    assert validate_file_map({"main.tf": "hello"}) == {"main.tf": "hello"}
