"""Planted credentials are assembled only inside temporary repositories."""

import subprocess

import pytest

from scripts.secret_scan import excluded, matches, scan


def planted(prefix="sk-or-"):
    return prefix + "q9F4tK7dN2mB8vA5xL6pZ3cR"


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize(
    "prefix,name",
    [
        ("sk-or-", "openrouter"),
        ("sk-ant-", "anthropic"),
        ("sk-", "openai"),
        ("AKIA", "aws_access_key"),
        ("ASIA", "aws_access_key"),
    ],
)
def test_provider_keys(prefix, name):
    value = (
        prefix + "ABCDEFGHIJKLMNOP" if prefix in {"AKIA", "ASIA"} else planted(prefix)
    )
    assert matches(value.encode(), set()) == [(1, name)]
    assert matches(value.encode(), {value}) == []
    assert matches((value[:-1] + "9").encode(), {value})


@pytest.mark.req("NFR-01")
def test_private_key_generic_assignment_and_placeholders():
    block = "-----BEGIN " + "OPENSSH PRIVATE KEY-----"
    assert matches(block.encode(), set()) == [(1, "private_key")]
    value = planted("")
    assert matches(f'LLM_API_KEY="{value}"'.encode(), set()) == [
        (1, "api_key_assignment")
    ]
    for value in ("", "${LLM_API_KEY}", "a" * 40, "replace-with-local-app-password"):
        assert not matches(
            f"LLM_API_KEY={value}".encode(), {"replace-with-local-app-password"}
        )


@pytest.mark.req("NFR-01")
def test_deleted_renamed_keys_history_and_exclusions(tmp_path, monkeypatch):
    def git(*args):
        subprocess.run(
            ["git", "-C", str(tmp_path), *args], check=True, capture_output=True
        )

    git("init")
    git("config", "user.email", "offline@example.invalid")
    git("config", "user.name", "Offline test")
    value = planted()
    (tmp_path / "old.txt").write_text(value)
    (tmp_path / ".env").write_text(value)
    git("add", ".")
    git("commit", "-m", "fixture")
    git("mv", "old.txt", "renamed.txt")
    git("commit", "-am", "rename")
    (tmp_path / "renamed.txt").unlink()
    git("commit", "-am", "delete")
    (tmp_path / "untracked.txt").write_text(value)
    (tmp_path / "alias").symlink_to(tmp_path / ".env")
    original = type(tmp_path).read_bytes

    def guarded(path):
        assert not excluded(path.relative_to(tmp_path))
        return original(path)

    monkeypatch.setattr(type(tmp_path), "read_bytes", guarded)
    findings, errors = scan(tmp_path, set())
    assert not errors
    assert {"old.txt", "renamed.txt", "untracked.txt"} == {
        row["file"] for row in findings
    }
    assert value not in str(findings)


@pytest.mark.req("NFR-01")
def test_clean_repository_and_cache_pruning(tmp_path):
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    for name in (".cache", "node_modules", ".venv"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "secret.txt").write_text(planted())
    (tmp_path / "example.txt").write_text("safe placeholder")
    assert scan(tmp_path, set()) == ([], [])
