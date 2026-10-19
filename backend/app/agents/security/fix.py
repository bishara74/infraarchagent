"""Generate and validate an atomic fix proposal for one existing file."""

import asyncio
import hashlib
import re
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import PurePosixPath
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.agents.prompts.security_fix import system_prompt, user_prompt
from app.agents.security.fix_schema import validate_output, wire_schema
from app.core.config import StructuredOutput
from app.core.logging import RedactingFilter
from app.domain.models import Violation
from app.domain.package_layout import package_structure_errors
from app.domain.paths import UnsafePathError, validate_relative_path
from app.domain.plan import DeploymentPlan
from app.llm.base import LLMAdapter, LLMAttempt
from app.llm.errors import (
    LLMDeadlineExceeded,
    LLMPermanentError,
    LLMRetryExhausted,
    failure_message,
)
from app.security.catalogue import guidance
from app.validation.documents import PackageDocuments
from app.validation.gate import patch_syntax_failure, syntax_checks
from app.validation.schema_context import schema_context

SUPPRESSION = re.compile(
    r"#\s*(?:checkov\s*:\s*skip|bridgecrew\s*:\s*skip|"
    r"tfsec\s*:\s*ignore|trivy\s*:\s*ignore|nosec\b)[^\n]*",
    re.IGNORECASE,
)


def suppression_comments(content: str) -> Counter[str]:
    return Counter(
        " ".join(match.lower().split()) for match in SUPPRESSION.findall(content)
    )


class FixFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    content: str


class FixSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str
    resource: str
    summary: str


class FixOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file: FixFile
    new_files: dict[str, str] = Field(default_factory=dict)
    edits: dict[str, str] = Field(default_factory=dict)
    fixes: Any = None


def _safe_summaries(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    summaries: list[str] = []
    for item in raw:
        try:
            summary = FixSummary.model_validate(item)
        except ValidationError:
            continue
        summaries.append(summary.summary[:200])
    return tuple(summaries)


def _schema_reason(error: ValidationError) -> str:
    issue = error.errors(include_input=False, include_context=False)[0]
    location = issue["loc"]
    root = location[0] if location else None
    if root == "file":
        field = location[1] if len(location) > 1 else None
        path = f"file.{field}" if field in {"path", "content"} else "file"
    elif root in {"new_files", "edits"}:
        path = f"{root}.value" if len(location) > 1 else str(root)
    elif root == "fixes":
        index = location[1] if len(location) > 1 else None
        path = f"fixes[{index}]" if isinstance(index, int) else "fixes"
        field = location[2] if len(location) > 2 else None
        if field in {"rule_id", "resource", "summary"}:
            path += f".{field}"
    else:
        path = "response"
    code = {
        "missing": "missing",
        "string_too_long": "too_long",
        "extra_forbidden": "extra",
    }.get(issue["type"], "type")
    return f"schema:{path}.{code}"


@dataclass(frozen=True)
class FixProposal:
    path: str
    accepted: bool
    reason: str | None
    content: str | None
    new_files: dict[str, str]
    summaries: tuple[str, ...]
    input_tokens: int | None = None
    output_tokens: int | None = None
    cached_input_tokens: int | None = None
    schema_context_chars: int = 0
    schema_context_reason: str | None = None
    edits: dict[str, str] = field(default_factory=dict)
    edit_bases: dict[str, str] = field(default_factory=dict)
    normalized_existing_paths: tuple[str, ...] = ()
    conflicting_paths: tuple[str, ...] = ()
    llm_attempts: int | None = None
    attempt_details: tuple[LLMAttempt, ...] = ()
    failure_category: str | None = None
    call_kind: str = "security_fixer"


def content_hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()


def editable_paths(files: Mapping[str, str], path: str) -> set[str]:
    return {
        name
        for name in files
        if name == path
        or (
            path.startswith("terraform/")
            and PurePosixPath(name).parent == PurePosixPath(path).parent
            and name.endswith((".tf", ".tf.json"))
        )
    }


def validate_fix(
    raw: dict[str, Any],
    *,
    path: str,
    files: Mapping[str, str],
    plan: DeploymentPlan,
    context_paths: set[str] | None = None,
) -> FixProposal:
    try:
        output = FixOutput.model_validate(raw)
    except ValidationError as error:
        return FixProposal(path, False, _schema_reason(error), None, {}, ())
    if output.file.path != path:
        return FixProposal(path, False, "path_mismatch", None, {}, ())
    if not output.file.content:
        return FixProposal(path, False, "empty_content", None, {}, ())
    if len((set(output.new_files) | set(output.edits)) - {path}) > 3:
        return FixProposal(path, False, "too_many_new_files", None, {}, ())
    try:
        for new_path in {*output.new_files, *output.edits}:
            validate_relative_path(new_path)
    except UnsafePathError:
        return FixProposal(path, False, "unsafe_new_path", None, {}, ())
    context_paths = (
        editable_paths(files, path) if context_paths is None else context_paths
    )
    edits = {path: output.file.content}
    new_files = {}
    normalized = []
    for name, text in output.edits.items():
        if name not in files:
            return FixProposal(
                path,
                False,
                "edit_file_missing",
                None,
                {},
                (),
                conflicting_paths=(name,),
            )
        if name not in context_paths:
            return FixProposal(
                path,
                False,
                "existing_file_context_missing",
                None,
                {},
                (),
                conflicting_paths=(name,),
            )
        if name in edits and edits[name] != text:
            return FixProposal(
                path,
                False,
                "conflicting_edits",
                None,
                {},
                (),
                conflicting_paths=(name,),
            )
        edits[name] = text
    for name, text in output.new_files.items():
        if name in files:
            if name not in context_paths:
                return FixProposal(
                    path,
                    False,
                    "existing_file_context_missing",
                    None,
                    {},
                    (),
                    conflicting_paths=(name,),
                )
            if name in edits and edits[name] != text:
                return FixProposal(
                    path,
                    False,
                    "conflicting_edits",
                    None,
                    {},
                    (),
                    conflicting_paths=(name,),
                )
            edits[name] = text
            normalized.append(name)
        else:
            if name.casefold() in {p.casefold() for p in files}:
                return FixProposal(
                    path,
                    False,
                    "existing_path_case_conflict",
                    None,
                    {},
                    (),
                    conflicting_paths=(name,),
                )
            new_files[name] = text
    if any(not text for text in edits.values()):
        return FixProposal(path, False, "empty_edit", None, {}, ())
    if any(
        suppression_comments(text) - suppression_comments(files[name])
        for name, text in edits.items()
    ) or any(suppression_comments(content) for content in new_files.values()):
        return FixProposal(path, False, "new_suppression", None, {}, ())
    candidate = dict(files)
    candidate.update(edits)
    candidate.update(new_files)
    if package_structure_errors(candidate, plan.file_types):
        return FixProposal(path, False, "invalid_structure", None, {}, ())
    if syntax_checks(candidate, {*edits, *new_files}):
        return FixProposal(path, False, "invalid_syntax", None, {}, ())
    return FixProposal(
        path,
        True,
        None,
        output.file.content,
        dict(new_files),
        _safe_summaries(output.fixes),
        edits={name: text for name, text in edits.items() if name != path},
        edit_bases={name: content_hash(files[name]) for name in edits},
        normalized_existing_paths=tuple(sorted(normalized)),
    )


class FixAgent:
    def __init__(
        self,
        adapter: LLMAdapter,
        *,
        attempt_timeout: float = 90,
        max_output_tokens: int = 16000,
        schema_context_max_chars: int = 16000,
        structured_output: StructuredOutput = "json_schema",
    ) -> None:
        self.adapter = adapter
        self.wire_files = (
            bool(getattr(adapter, "supports_structured_output", False))
            and structured_output == "json_schema"
        )
        adapter.structured_output = structured_output
        adapter.output_schema = wire_schema() if self.wire_files else None
        adapter.output_schema_name = "fix_patch"
        self.output_validator = lambda data: validate_output(
            data, wire_files=self.wire_files
        )
        self.attempt_timeout = attempt_timeout
        self.max_output_tokens = max_output_tokens
        self.schema_context_max_chars = schema_context_max_chars

    async def propose(
        self,
        *,
        path: str,
        files: Mapping[str, str],
        findings: Sequence[Violation],
        plan: DeploymentPlan,
        directive: str,
        remaining: float,
        feedback: str | None = None,
        validation_failures: Sequence[dict[str, Any]] = (),
        previous_attempt: str = "",
        syntax_only: bool = False,
    ) -> FixProposal:
        started = time.monotonic()
        context = (
            ""
            if syntax_only
            else schema_context(
                path,
                dict(files),
                failures=list(validation_failures),
                findings=list(findings),
                limit=self.schema_context_max_chars,
            )
        )
        if not path.startswith("terraform/"):
            context_reason = "not_terraform"
        elif context and '"schema":' in context:
            context_reason = "schema_available"
        else:
            docs = PackageDocuments.parse(dict(files))
            context_reason = (
                "unparseable_document"
                if docs.documents.get(path) and docs.documents[path].parse_error
                else "no_schema_entries"
            )
        attempts: list[LLMAttempt] = []
        call_kind = (
            "syntax_repair"
            if syntax_only
            else "validation_repair"
            if validation_failures and not findings
            else "security_fixer"
        )
        try:
            response = await self.adapter.complete_json(
                user_prompt(
                    plan=plan,
                    path=path,
                    content=files[path],
                    findings=findings,
                    feedback=feedback,
                    validation_failures=validation_failures,
                    schema_context=context,
                    previous_attempt=RedactingFilter().redact(previous_attempt)[:4000],
                    existing_paths=sorted(files),
                    catalogue_guidance=guidance(
                        {f.resource.split(".")[0] for f in findings}
                    ),
                    related_files={
                        name: text
                        for name, text in files.items()
                        if name != path
                        and path.startswith("terraform/")
                        and PurePosixPath(name).parent == PurePosixPath(path).parent
                        and name.endswith((".tf", ".tf.json"))
                    },
                ),
                system=system_prompt(
                    directive, syntax_only=syntax_only, wire_files=self.wire_files
                ),
                deadline=remaining,
                attempt_timeout=self.attempt_timeout,
                max_output_tokens=self.max_output_tokens,
                response_validator=self.output_validator,
                attempt_observer=attempts.append,
            )
        except LLMRetryExhausted as error:
            return FixProposal(
                path,
                False,
                failure_message(error.last_category),
                None,
                {},
                (),
                schema_context_chars=len(context),
                schema_context_reason=context_reason,
                attempt_details=tuple(attempts),
                llm_attempts=len(attempts) or None,
                failure_category=error.last_category,
                call_kind=call_kind,
            )
        except LLMPermanentError as error:
            return FixProposal(
                path,
                False,
                failure_message(error.category),
                None,
                {},
                (),
                schema_context_chars=len(context),
                schema_context_reason=context_reason,
                attempt_details=tuple(attempts),
                llm_attempts=len(attempts) or None,
                failure_category=error.category,
                call_kind=call_kind,
            )
        except LLMDeadlineExceeded:
            return FixProposal(
                path,
                False,
                failure_message("unreachable"),
                None,
                {},
                (),
                schema_context_chars=len(context),
                schema_context_reason=context_reason,
                attempt_details=tuple(attempts),
                llm_attempts=len(attempts) or None,
                failure_category="deadline",
                call_kind=call_kind,
            )
        proposal = validate_fix(response.data, path=path, files=files, plan=plan)
        if proposal.accepted:
            assert proposal.content is not None
            candidate = {
                **files,
                path: proposal.content,
                **proposal.edits,
                **proposal.new_files,
            }
            try:
                async with asyncio.timeout(
                    max(0.001, remaining - (time.monotonic() - started))
                ):
                    if await patch_syntax_failure(
                        dict(files),
                        candidate,
                        {path, *proposal.edits, *proposal.new_files},
                    ):
                        proposal = FixProposal(
                            path, False, "invalid_syntax", None, {}, ()
                        )
            except TimeoutError:
                proposal = FixProposal(path, False, "time_budget", None, {}, ())
        return replace(
            proposal,
            llm_attempts=getattr(response, "attempts", None),
            attempt_details=tuple(attempts),
            call_kind=call_kind,
            input_tokens=response.response.input_tokens,
            output_tokens=response.response.output_tokens,
            cached_input_tokens=response.response.cached_input_tokens,
            schema_context_chars=len(context),
            schema_context_reason=context_reason,
        )
