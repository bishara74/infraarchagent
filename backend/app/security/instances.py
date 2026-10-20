"""D-56 bounded symbolic Terraform instances. No variables, eval or AWS calls."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Any

import hcl2
from lark import Tree
from lark.exceptions import LarkError

from app.security.terraform import Resource, TerraformPackage, objects
from app.validation.documents import blocks


class Unresolved(ValueError):
    """Unknown is never evidence for an exception or connectivity change."""


@dataclass(frozen=True)
class Ref:
    module: str
    address: str
    attribute: str = "id"


@dataclass
class Instance:
    resource: Resource
    key: str | int | None
    env: dict[str, Any]

    @property
    def address(self) -> str:
        return self.resource.address + (
            "[" + json.dumps(self.key) + "]" if self.key is not None else ""
        )

    @property
    def module(self) -> str:
        return self.resource.module

    @property
    def type(self) -> str:
        return self.resource.type


@dataclass(frozen=True)
class Namespace:
    name: str


@lru_cache(maxsize=256)
def expression_tree(expression: str) -> tuple[Tree[Any], str]:
    if len(expression) > 4096:
        raise Unresolved()
    source = "value = " + expression
    tree = hcl2.parses_to_tree(source)
    attribute = next(tree.find_data("attribute"))
    return next(c for c in attribute.children[1:] if isinstance(c, Tree)), source


class Instances:
    MAX_DECLARATION = 64
    MAX_MODULE = 1024
    MAX_LOCALS = 16

    def __init__(self, files: dict[str, str]):
        self.package = TerraformPackage(files)
        self.declarations = {(r.module, r.address): r for r in self.package.resources}
        self.local_values: dict[tuple[str, str], Any] = {}
        self.expanded: dict[tuple[str, str], Any] = {}
        self.active: set[tuple[str, str]] = set()
        self.unsafe: set[str] = set()
        self.counts: dict[str, int] = {}
        identities: set[tuple[str, str]] = set()
        for resource in self.package.resources:
            identity = resource.module, resource.address
            if identity in identities:
                self.unsafe.add(resource.module)
            identities.add(identity)
        for doc in self.package.documents.documents.values():
            module = str(PurePosixPath(doc.path).parent)
            if doc.parse_error or blocks(doc.data, "module"):
                self.unsafe.add(module)
            for body in (
                objects(doc.data.get("locals", []))
                if isinstance(doc.data, dict)
                else []
            ):
                for name, value in body.items():
                    key = (module, name)
                    if key in self.local_values:
                        self.unsafe.add(module)
                    self.local_values[key] = value
        for key in self.declarations:
            try:
                self.expand(*key)
            except Unresolved:
                pass

    def expand(self, module: str, address: str) -> Any:
        key = module, address
        if module in self.unsafe or not self.package.module_safe(module):
            raise Unresolved()
        if key in self.expanded:
            result = self.expanded[key]
            if result is None:
                raise Unresolved()
            return result
        if key in self.active or key not in self.declarations:
            raise Unresolved()
        self.active.add(key)
        r = self.declarations[key]
        try:
            if any(k in r.body for k in ("provider", "dynamic")) or (
                "count" in r.body and "for_each" in r.body
            ):
                raise Unresolved()
            if "count" in r.body:
                count = self.value(r.body["count"], module)
                if type(count) is not int or not 0 <= count <= self.MAX_DECLARATION:
                    raise Unresolved()
                result = [Instance(r, i, {"count": {"index": i}}) for i in range(count)]
            elif "for_each" in r.body:
                collection = self.value(r.body["for_each"], module)
                if isinstance(collection, frozenset):
                    collection = {k: k for k in sorted(collection)}
                if (
                    not isinstance(collection, dict)
                    or len(collection) > self.MAX_DECLARATION
                    or not all(isinstance(k, str) for k in collection)
                ):
                    raise Unresolved()
                result = {
                    k: Instance(r, k, {"each": {"key": k, "value": v}})
                    for k, v in sorted(collection.items())
                }
            else:
                result = Instance(r, None, {})
            self.counts[module] = self.counts.get(module, 0) + (
                len(result) if isinstance(result, (list, dict)) else 1
            )
            if self.counts[module] > self.MAX_MODULE:
                self.unsafe.add(module)
                raise Unresolved()
            self.expanded[key] = result
            return result
        except (
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            StopIteration,
            RecursionError,
            LarkError,
        ):
            self.expanded[key] = None
            raise Unresolved() from None
        finally:
            self.active.discard(key)

    def all(self, module: str, types: set[str] | None = None) -> list[Instance]:
        if module in self.unsafe:
            return []
        result: list[Instance] = []
        for (scope, _), value in self.expanded.items():
            if scope != module or value is None:
                continue
            items = (
                list(value.values())
                if isinstance(value, dict)
                else value
                if isinstance(value, list)
                else [value]
            )
            result.extend(x for x in items if types is None or x.type in types)
        return result

    def unknown(self, module: str, types: set[str]) -> list[Resource]:
        return [
            r
            for key, r in self.declarations.items()
            if r.module == module
            and r.type in types
            and (module in self.unsafe or self.expanded.get(key) is None)
        ]

    def find(self, module: str, address: str) -> Instance | None:
        found = [i for i in self.all(module) if i.address == address]
        return found[0] if len(found) == 1 else None

    def get(self, instance: Instance, field: str, default: Any = None) -> Any:
        if field not in instance.resource.body:
            return default
        return self.value(instance.resource.body[field], instance.module, instance.env)

    def linked(self, instance: Instance, field: str) -> Instance | None:
        try:
            value = self.get(instance, field)
            return (
                self.find(value.module, value.address)
                if isinstance(value, Ref)
                else None
            )
        except Unresolved:
            return None

    def value(
        self, value: Any, module: str, env: dict[str, Any] | None = None, depth: int = 0
    ) -> Any:
        env = env or {}
        if depth > self.MAX_LOCALS:
            raise Unresolved()
        if isinstance(value, dict):
            return {k: self.value(v, module, env, depth) for k, v in value.items()}
        if isinstance(value, list):
            return [self.value(v, module, env, depth) for v in value]
        if not isinstance(value, str) or "${" not in value:
            return value
        if not value.startswith("${") or not value.endswith("}"):
            raise Unresolved()
        try:
            tree, source = expression_tree(value[2:-1])
            return self._eval(tree, source, module, env, depth)
        except (
            ValueError,
            TypeError,
            KeyError,
            IndexError,
            StopIteration,
            RecursionError,
            LarkError,
        ):
            raise Unresolved() from None

    def _attr(
        self, value: Any, name: str, module: str, env: dict[str, Any], depth: int
    ) -> Any:
        if isinstance(value, Namespace):
            if value.name == "local":
                return self.value(
                    self.local_values[module, name], module, env, depth + 1
                )
            if value.name.startswith("aws_"):
                return self.expand(module, value.name + "." + name)
            raise Unresolved()
        if isinstance(value, Instance):
            if name in {"id", "arn", "name", "bucket", "default_route_table_id"}:
                return Ref(value.module, value.address, name)
            if name not in value.resource.body:
                raise Unresolved()
            return self.get(value, name)
        if isinstance(value, dict):
            return value[name]
        raise Unresolved()

    def _eval(
        self, node: Tree[Any], source: str, module: str, env: dict[str, Any], depth: int
    ) -> Any:
        children = [c for c in node.children if isinstance(c, Tree)]
        kind = str(node.data)

        def run(n: Tree[Any], e: dict[str, Any] = env) -> Any:
            return self._eval(n, source, module, e, depth)

        if kind in {"expr_term", "object_elem_key"} and len(children) == 1:
            return run(children[0])
        if kind == "identifier":
            name = str(node.children[0])
            if name in {"true", "false", "null"}:
                return {"true": True, "false": False, "null": None}[name]
            return env[name] if name in env else Namespace(name)
        if kind == "int_lit":
            return int("".join(str(c) for c in node.children))
        if kind == "string":
            text = source[node.meta.start_pos : node.meta.end_pos]
            if "${" in text or "%{" in text:
                raise Unresolved()
            return json.loads(text)
        if kind == "tuple":
            return [run(c) for c in children if c.data != "new_line_or_comment"]
        if kind == "object":
            result = {}
            for child in children:
                if child.data != "object_elem":
                    continue
                parts = [c for c in child.children if isinstance(c, Tree)]
                raw_key = source[parts[0].meta.start_pos : parts[0].meta.end_pos]
                key = raw_key if raw_key.replace("_", "").isalnum() else run(parts[0])
                if key in result:
                    raise Unresolved()
                result[key] = run(parts[1])
            return result
        if kind == "get_attr_expr_term":
            name = str(next(children[1].find_data("identifier")).children[0])
            return self._attr(run(children[0]), name, module, env, depth)
        if kind == "index_expr_term":
            index = next(c for c in children[1].children if isinstance(c, Tree))
            key = run(index)
            if type(key) not in (int, str):
                raise Unresolved()
            return run(children[0])[key]
        if kind in {"full_splat_expr_term", "attr_splat_expr_term"}:
            items = run(children[0])
            if isinstance(items, dict):
                raise Unresolved()
            if not isinstance(items, list):
                items = [items]
            for operation in children[1].children:
                if isinstance(operation, Tree) and operation.data == "get_attr":
                    name = str(next(operation.find_data("identifier")).children[0])
                    items = [self._attr(v, name, module, env, depth) for v in items]
                elif isinstance(operation, Tree):
                    raise Unresolved()
            return items
        if kind == "function_call":
            name = str(children[0].children[0])
            args = (
                [
                    run(c)
                    for c in children[1].children
                    if isinstance(c, Tree) and c.data != "new_line_or_comment"
                ]
                if len(children) > 1
                else []
            )
            if (
                name in {"toset", "tolist", "tomap", "length", "keys", "values"}
                and len(args) == 1
            ):
                value = args[0]
                if name == "length" and isinstance(value, (list, dict, frozenset, str)):
                    return len(value)
                if (
                    name == "toset"
                    and isinstance(value, list)
                    and all(isinstance(x, str) for x in value)
                ):
                    return frozenset(value)
                if name == "tolist" and isinstance(value, (list, frozenset)):
                    return sorted(value) if isinstance(value, frozenset) else value
                if name == "tomap" and isinstance(value, dict):
                    return value
                if name in {"keys", "values"} and isinstance(value, dict):
                    return (
                        sorted(value)
                        if name == "keys"
                        else [value[k] for k in sorted(value)]
                    )
            if name == "concat" and all(isinstance(a, list) for a in args):
                return [v for a in args for v in a]
            if (
                name == "element"
                and len(args) == 2
                and isinstance(args[0], list)
                and args[0]
                and type(args[1]) is int
                and args[1] >= 0
            ):
                return args[0][args[1] % len(args[0])]
            raise Unresolved()
        if kind in {"for_tuple_expr", "for_object_expr"}:
            intro = children[0]
            variables = [
                str(c.children[0])
                for c in intro.children
                if isinstance(c, Tree) and c.data == "identifier"
            ]
            iterable = run(
                next(
                    c
                    for c in intro.children
                    if isinstance(c, Tree) and c.data == "expr_term"
                )
            )
            if isinstance(iterable, dict):
                pairs = sorted(iterable.items())
            elif isinstance(iterable, (list, frozenset)):
                pairs = list(
                    enumerate(
                        sorted(iterable)
                        if isinstance(iterable, frozenset)
                        else iterable
                    )
                )
            else:
                raise Unresolved()
            if len(pairs) > self.MAX_DECLARATION or any(
                c.data == "for_cond" for c in children
            ):
                raise Unresolved()
            out: Any = [] if kind == "for_tuple_expr" else {}
            for key, value in pairs:
                scope = {
                    **env,
                    **dict(
                        zip(
                            variables,
                            [value] if len(variables) == 1 else [key, value],
                            strict=True,
                        )
                    ),
                }
                if kind == "for_tuple_expr":
                    out.append(run(children[1], scope))
                else:
                    new_key = run(children[1], scope)
                    if not isinstance(new_key, str) or new_key in out:
                        raise Unresolved()
                    out[new_key] = run(children[2], scope)
            return out
        if kind == "binary_op" and len(children) == 2:
            left = run(children[0])
            parts = [c for c in children[1].children if isinstance(c, Tree)]
            op = source[parts[0].meta.start_pos : parts[0].meta.end_pos]
            right = run(parts[1])
            if type(left) is int and type(right) is int and op in {"+", "-"}:
                return left + right if op == "+" else left - right
        raise Unresolved()
