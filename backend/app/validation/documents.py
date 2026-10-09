"""Parse package files once, sharing data and safe source positions."""

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import hcl2
import yaml  # type: ignore[import-untyped]
from hcl2.utils import SerializationOptions
from lark.exceptions import LarkError
from yaml.nodes import (  # type: ignore[import-untyped]
    MappingNode,
    Node,
    ScalarNode,
    SequenceNode,
)

from app.domain.package_layout import classify_path
from app.domain.paths import validate_file_map
from app.domain.plan import FileType


def mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


HELM_EXPRESSION = "__infraarch_helm_expression__"


def helm_template_resources(source: str) -> Iterator[dict[str, Any]]:
    """Inspect YAML declarations without evaluating Go templates or includes."""
    # Standalone actions (conditionals, toYaml blocks) are not YAML declarations.
    projected = re.sub(r"(?m)^[ \t]*{{[^\n]*}}[ \t]*$", "", source)
    projected = re.sub(r"{{[\s\S]*?}}", HELM_EXPRESSION, projected)
    for document in re.split(r"(?m)^---[ \t]*(?:#.*)?$", projected):
        loader = yaml.SafeLoader(document)
        try:
            node = loader.get_single_node()
            if node is not None:
                positions(node)  # Reject recursive aliases before construction/walks.
                data = loader.construct_document(node)
                if isinstance(data, dict):
                    yield data
        except (yaml.YAMLError, ValueError, TypeError):
            # Uninspectable template text is left to Helm's optional linter.
            continue
        finally:
            loader.dispose()


def helm_expression(value: Any) -> bool:
    return isinstance(value, str) and HELM_EXPRESSION in value


def normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.lower()).strip("-")


def code_text(
    source: str,
    *,
    hash_comments: bool = False,
    mask_strings: bool = True,
    slash_comments: bool = True,
) -> str:
    """Mask comments/quoted contents while preserving every newline and offset."""
    pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    if slash_comments:
        pattern += r"|/\*[\s\S]*?\*/|//[^\n]*"
    if hash_comments:
        pattern += r"|\#[^\n]*"

    def mask(match: re.Match[str]) -> str:
        text = match.group()
        if text[0] in {'"', "'"} and not mask_strings:
            return text
        return "".join("\n" if char == "\n" else " " for char in text)

    return re.sub(pattern, mask, source)


@dataclass(frozen=True)
class YamlDocument:
    data: Any
    line: int
    positions: dict[tuple[str | int, ...], int]


def positions(
    node: Node, prefix: tuple[str | int, ...] = (), active: frozenset[int] = frozenset()
) -> dict[tuple[str | int, ...], int]:
    if id(node) in active:
        raise ValueError("recursive YAML aliases")
    active = active | {id(node)}
    result = {prefix: node.start_mark.line + 1}
    if isinstance(node, MappingNode):
        for key, value in node.value:
            if isinstance(key, ScalarNode):
                result.update(positions(value, prefix + (key.value,), active))
    elif isinstance(node, SequenceNode):
        for index, value in enumerate(node.value):
            result.update(positions(value, prefix + (index,), active))
    return result


@dataclass(frozen=True)
class Document:
    path: str
    source: str
    kind: FileType | None
    data: Any = None
    yaml_documents: tuple[YamlDocument, ...] = ()
    error_line: int | None = None
    parse_error: bool = False

    def line(self, token: str | None = None) -> int:
        if token:
            for index, line in enumerate(self.source.splitlines(), 1):
                if token in line:
                    return index
        return 1


@dataclass
class PackageDocuments:
    files: dict[str, str]
    documents: dict[str, Document] = field(default_factory=dict)

    @classmethod
    def parse(cls, files: dict[str, str]) -> "PackageDocuments":
        safe = validate_file_map(files)
        package = cls(safe)
        for path, source in sorted(safe.items()):
            kind = classify_path(path)
            data: Any = None
            documents: list[YamlDocument] = []
            error_line: int | None = None
            failed = False
            try:
                if kind == FileType.TERRAFORM and path.endswith(".tf.json"):
                    data = json.loads(source)
                elif kind == FileType.TERRAFORM and path.endswith((".tf", ".tfvars")):
                    data = hcl2.loads(
                        source,
                        serialization_options=SerializationOptions(
                            strip_string_quotes=True,
                            with_comments=False,
                            explicit_blocks=False,
                        ),
                    )
                elif kind == FileType.GRAFANA:
                    data = json.loads(source)
                elif path.endswith((".yaml", ".yml")) and not (
                    kind == FileType.HELM and "/templates/" in path
                ):
                    loader = yaml.SafeLoader(source)
                    try:
                        while loader.check_data():
                            node = loader.get_node()
                            if node is not None:
                                locations = positions(node)
                                documents.append(
                                    YamlDocument(
                                        loader.construct_document(node),
                                        node.start_mark.line + 1,
                                        locations,
                                    )
                                )
                    finally:
                        loader.dispose()
                    data = (
                        documents[0].data
                        if len(documents) == 1
                        else [doc.data for doc in documents]
                    )
            except (yaml.YAMLError, LarkError, ValueError, TypeError) as error:
                failed = True
                mark = getattr(error, "problem_mark", None)
                error_line = (
                    mark.line + 1
                    if mark
                    else getattr(error, "line", None) or getattr(error, "lineno", 1)
                )
            package.documents[path] = Document(
                path, source, kind, data, tuple(documents), error_line, failed
            )
        return package

    def of_kind(self, kind: FileType) -> list[Document]:
        return [doc for doc in self.documents.values() if doc.kind == kind]


def blocks(data: Any, kind: str) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
    """Handle HCL block lists and tf.json dictionaries through one representation."""
    result: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    if not isinstance(data, dict):
        return result
    raw = data.get(kind, {})
    entries = raw if isinstance(raw, list) else [raw]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for label, body in entry.items():
            if kind == "resource" and isinstance(body, dict):
                for name, attributes in body.items():
                    if isinstance(attributes, dict):
                        result.append(((label, name), attributes))
            elif isinstance(body, dict):
                result.append(((label,), body))
    return result


def walk(
    data: Any, path: tuple[str | int, ...] = (), active: frozenset[int] = frozenset()
) -> Iterator[tuple[tuple[str | int, ...], Any]]:
    if isinstance(data, (dict, list)):
        if id(data) in active:
            return
        active = active | {id(data)}
        entries = data.items() if isinstance(data, dict) else enumerate(data)
        for key, value in entries:
            yield path + (key,), value
            yield from walk(value, path + (key,), active)
