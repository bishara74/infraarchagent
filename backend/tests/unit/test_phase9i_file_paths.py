"""FR-V-03/NFR-01: exact package artifacts, no path guesses or host reads."""

import json
from types import SimpleNamespace

import pytest

from app.agents.budget import AgentBudget
from app.agents.deterministic import checked_one
from app.domain.enums import Variant
from app.domain.validation import DeterministicRepair
from app.validation.documents import PackageDocuments
from app.validation.equivalents import repair_equivalents
from app.validation.file_paths import repair_file_paths
from tests.unit.test_phase9i_deterministic import Engine, Scanner, Verifier, report
from tests.unit.test_secure_generation import plan

pytestmark = pytest.mark.req("FR-V-03", "FR-G-02", "NFR-01")

TARGET = "helm/app/values.yaml"


def package(expression='file("helm/app/values.yaml")', *, style="hcl"):
    if style == "json":
        return {
            "terraform/main.tf.json": json.dumps(
                {"locals": {"values": ["${" + expression + "}"]}}, indent=2
            ),
            TARGET: "replicaCount: 2\n",
        }
    return {
        "terraform/main.tf": '# KEEP file("helm/app/values.yaml")\n'
        "locals {\n  values = [" + expression + "] # KEEP\n}\n",
        TARGET: "replicaCount: 2\n",
    }


@pytest.mark.parametrize("style", ["hcl", "json"])
def test_exact_artifact_rebase_preserves_contents_comments_and_idempotence(style):
    files = package(style=style)
    original = dict(files)
    after, records = repair_equivalents(files)
    assert files == original
    assert after[TARGET] == original[TARGET]
    path = next(p for p in files if p.endswith((".tf", ".tf.json")))
    document = PackageDocuments.parse(after).documents[path]
    assert not document.parse_error
    assert document.data["locals"] == (
        {"values": ['${file("${path.module}/../helm/app/values.yaml")}']}
        if style == "json"
        else [{"values": ['${file("${path.module}/../helm/app/values.yaml")}']}]
    )
    if style == "hcl":
        assert after[path].startswith('# KEEP file("helm/app/values.yaml")\n')
        assert "] # KEEP\n" in after[path]
    assert len(records) == 1
    record = DeterministicRepair.model_validate(records[0])
    assert record.kind == "terraform_file_path"
    assert record.before_hash != record.after_hash
    assert record.line and record.name == TARGET
    assert repair_equivalents(after) == (after, [])


def test_absent_target_and_same_basename_elsewhere_are_not_guessed():
    files = package()
    files["helm/other/values.yaml"] = files.pop(TARGET)
    assert repair_file_paths(files) == (files, [])


@pytest.mark.parametrize("style", ["hcl", "json"])
@pytest.mark.parametrize(
    "expression",
    [
        'file(\n  "helm/app/values.yaml"\n)',
        'file(\n # retain argument comment\n "helm/app/values.yaml",\n)',
    ],
)
def test_multiline_literal_arguments_and_comments_are_preserved(expression, style):
    files = package(expression, style=style)
    after, records = repair_file_paths(files)
    assert len(records) == 1
    path = next(p for p in files if p.endswith((".tf", ".tf.json")))
    assert not PackageDocuments.parse(after).documents[path].parse_error
    before = (
        json.loads(files[path])["locals"]["values"][0]
        if style == "json"
        else files[path]
    )
    changed = (
        json.loads(after[path])["locals"]["values"][0]
        if style == "json"
        else after[path]
    )
    assert changed == before.replace(
        expression,
        expression.replace(
            '"helm/app/values.yaml"', '"${path.module}/../helm/app/values.yaml"', 1
        ),
        1,
    )
    assert repair_file_paths(after) == (after, [])


def test_existing_module_target_is_authoritative_even_with_package_root_target():
    files = {**package(), "terraform/" + TARGET: "replicaCount: 7\n"}
    assert repair_file_paths(files) == (files, [])


@pytest.mark.parametrize(
    "expression",
    [
        "file(var.path)",
        'file("${var.directory}/values.yaml")',
        'file("${path.module}/helm/app/values.yaml")',
        'file(abspath("helm/app/values.yaml"))',
        'file(true ? "helm/app/values.yaml" : "helm/other/values.yaml")',
        '"file(\\"helm/app/values.yaml\\")"',
        '"$${file("helm/app/values.yaml")}"',
    ],
)
@pytest.mark.parametrize("style", ["hcl", "json"])
def test_dynamic_expressions_and_literal_function_lookalikes_skip(expression, style):
    files = package(expression, style=style)
    assert repair_file_paths(files) == (files, [])


@pytest.mark.parametrize(
    "target", ["../outside", "/tmp/outside", "C:/outside", "~/.env", ".env", "x/../y"]
)
def test_escape_attempts_and_dotenv_inputs_never_inspect_host_files(target):
    files = package("file(" + json.dumps(target) + ")")
    files[target] = "synthetic ignored content"
    assert repair_file_paths(files) == (files, [])


@pytest.mark.parametrize("style", ["hcl", "json"])
def test_ambiguous_declarations_skip_module(style):
    files = package(style=style)
    if style == "json":
        files["terraform/main.tf.json"] = (
            '{"locals":{"values":"different",'
            '"values":"${file(\\"helm/app/values.yaml\\")}"}}'
        )
    else:
        files["terraform/main.tf"] = (
            'locals {\n values = file("helm/app/values.yaml")\n values = "different"\n}'
        )
    assert repair_file_paths(files) == (files, [])


def test_malformed_sibling_skips_only_its_module():
    files = package()
    files["terraform/b.tf"] = "broken {"
    assert repair_file_paths(files) == (files, [])
    files["terraform/child/main.tf"] = package()["terraform/main.tf"]
    after, records = repair_file_paths(files)
    assert after["terraform/main.tf"] == files["terraform/main.tf"]
    assert (
        "${path.module}/../../helm/app/values.yaml" in after["terraform/child/main.tf"]
    )
    assert len(records) == 1


def test_heredoc_interpolations_rebase_without_rewriting_shell_text():
    source = """locals {
  script = <<-SCRIPT
# Unicode and escaped characters: \u00e9 \\ "
echo 'file("helm/app/values.yaml")'
${file("helm/app/values.yaml")}
$${file("helm/app/values.yaml")}
  SCRIPT
}
"""
    files = {**package(), "terraform/main.tf": source}
    after, records = repair_file_paths(files)
    assert after["terraform/main.tf"] == source.replace(
        '${file("helm/app/values.yaml")}\n',
        '${file("${path.module}/../helm/app/values.yaml")}\n',
        1,
    )
    assert len(records) == 1 and records[0]["line"] == 5
    assert repair_file_paths(after) == (after, [])


def test_multiple_json_interpolations_preserve_unrelated_source_escapes():
    value = '${file("helm/app/values.yaml")} / ${file("nginx/nginx.conf")}'
    source = json.dumps(
        {"locals": {"value": value}, "output": {"keep": {"value": "\u00e9"}}}
    )
    files = {
        "terraform/main.tf.json": source,
        TARGET: "replicaCount: 2\n",
        "nginx/nginx.conf": "events {}\n",
    }
    after, records = repair_file_paths(files)
    data = json.loads(after["terraform/main.tf.json"])
    assert data["locals"]["value"] == (
        '${file("${path.module}/../helm/app/values.yaml")} / '
        '${file("${path.module}/../nginx/nginx.conf")}'
    )
    assert "\\u00e9" in after["terraform/main.tf.json"]
    assert len(records) == 2
    assert repair_file_paths(after) == (after, [])


@pytest.mark.parametrize(
    "value",
    [
        'text" + file("helm/app/values.yaml") + "text',
        'text"\n injected = file("helm/app/values.yaml")\n keep = "text',
        '$${file(\n "helm/app/values.yaml"\n)}',
    ],
)
def test_json_decoded_template_fallback_never_reinterprets_literal_text(value):
    files = {
        "terraform/main.tf.json": json.dumps({"locals": {"value": value}}),
        TARGET: "replicaCount: 2\n",
    }
    assert repair_file_paths(files) == (files, [])


def test_child_module_respects_existing_root_working_directory_target():
    files = {
        "terraform/child/main.tf": package()["terraform/main.tf"],
        TARGET: "replicaCount: 2\n",
        "terraform/" + TARGET: "replicaCount: 7\n",
    }
    assert repair_file_paths(files) == (files, [])


@pytest.mark.parametrize(
    "mode,failed,reason",
    [
        ("clean", False, "improved"),
        ("clean", True, "no_improvement"),
        ("new_blocker", False, "new_blocking_findings"),
        ("unavailable", False, "verification_unavailable"),
    ],
)
async def test_path_proposals_use_existing_validity_and_security_guards(
    mode, failed, reason
):
    files = package()
    after, _, records = await checked_one(
        files,
        plan("EC2"),
        Variant.COST,
        report(True),
        Engine(failed),
        SimpleNamespace(scanner=Scanner(mode), terraform_verifier=Verifier()),
        AgentBudget(30),
        repair_file_paths,
    )
    assert (after != files) is (reason == "improved")
    assert records[0]["reason"] == reason
    assert records[0]["outcome"] == ("accepted" if reason == "improved" else "rejected")
