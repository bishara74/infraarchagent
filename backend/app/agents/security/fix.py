"""Generate and validate an atomic fix proposal for one existing file."""

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.agents.prompts.security_fix import system_prompt, user_prompt
from app.domain.models import Violation
from app.domain.package_layout import package_structure_errors
from app.domain.paths import UnsafePathError, validate_relative_path
from app.domain.plan import DeploymentPlan
from app.llm.base import LLMAdapter
from app.llm.errors import LLMDeadlineExceeded, LLMPermanentError, LLMRetryExhausted

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
    summary: str = Field(max_length=200)


class FixOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file: FixFile
    new_files: dict[str, str] = Field(default_factory=dict)
    fixes: list[FixSummary] = Field(default_factory=list)


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


def validate_fix(
    raw: dict[str, Any],
    *,
    path: str,
    files: Mapping[str, str],
    plan: DeploymentPlan,
) -> FixProposal:
    try:
        output = FixOutput.model_validate(raw)
    except ValidationError:
        return FixProposal(path, False, "invalid_response", None, {}, ())
    if output.file.path != path:
        return FixProposal(path, False, "wrong_path", None, {}, ())
    if not output.file.content:
        return FixProposal(path, False, "empty_content", None, {}, ())
    if len(output.new_files) > 3:
        return FixProposal(path, False, "too_many_new_files", None, {}, ())
    try:
        for new_path in output.new_files:
            validate_relative_path(new_path)
    except UnsafePathError:
        return FixProposal(path, False, "unsafe_new_path", None, {}, ())
    if any(new_path in files for new_path in output.new_files):
        return FixProposal(path, False, "new_file_exists", None, {}, ())
    current = suppression_comments(files[path])
    proposed = suppression_comments(output.file.content)
    if proposed - current or any(
        suppression_comments(content) for content in output.new_files.values()
    ):
        return FixProposal(path, False, "new_suppression", None, {}, ())
    candidate = dict(files)
    candidate[path] = output.file.content
    candidate.update(output.new_files)
    if package_structure_errors(candidate, plan.file_types):
        return FixProposal(path, False, "invalid_structure", None, {}, ())
    return FixProposal(
        path,
        True,
        None,
        output.file.content,
        dict(output.new_files),
        tuple(fix.summary for fix in output.fixes),
    )


class FixAgent:
    def __init__(
        self,
        adapter: LLMAdapter,
        *,
        attempt_timeout: float = 90,
        max_output_tokens: int = 16000,
    ) -> None:
        self.adapter = adapter
        self.attempt_timeout = attempt_timeout
        self.max_output_tokens = max_output_tokens

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
    ) -> FixProposal:
        try:
            response = await self.adapter.complete_json(
                user_prompt(
                    plan=plan,
                    path=path,
                    content=files[path],
                    findings=findings,
                    feedback=feedback,
                    validation_failures=validation_failures,
                ),
                system=system_prompt(directive),
                deadline=remaining,
                attempt_timeout=self.attempt_timeout,
                max_output_tokens=self.max_output_tokens,
            )
        except (LLMDeadlineExceeded, LLMPermanentError, LLMRetryExhausted):
            return FixProposal(path, False, "llm_failure", None, {}, ())
        proposal = validate_fix(response.data, path=path, files=files, plan=plan)
        return FixProposal(
            proposal.path,
            proposal.accepted,
            proposal.reason,
            proposal.content,
            proposal.new_files,
            proposal.summaries,
            response.response.input_tokens,
            response.response.output_tokens,
        )
