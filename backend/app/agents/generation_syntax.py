"""Provisional generation recovery, before establishing scanner baselines."""

import asyncio
import re
from collections import Counter
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from difflib import SequenceMatcher
from typing import Any

from app.agents.budget import AgentBudget
from app.agents.generators.base import GeneratorError
from app.agents.security.fix import FixAgent
from app.domain.plan import DeploymentPlan
from app.scanners.runner import ToolFailure
from app.validation.preservation import CONTROL_FIELDS, removes_security_controls
from app.validation.syntax import native_syntax, normalize_blocks

SYNTAX_GUIDANCE = (
    "Syntax only: preserve resource identities, values and security controls. "
    "Close quoted strings; put block arguments on separate lines without semicolons. "
    "IAM policies must use jsonencode() or a valid heredoc. Escape PromQL quotes "
    "inside JSON strings. Edit only the requested failing file; create no files."
)


def preserves_intent(before: str, after: str) -> bool:
    declarations = re.compile(
        r'(?m)^\s*(resource|data|variable|module|output)\s+("[^"\n]+"(?:\s+"[^"\n]+")?)\s*\{'
    )
    controls = re.compile(
        r"\b(" + "|".join(sorted(CONTROL_FIELDS)) + r")[\"']?\s*(?:=|:|\{)"
    )
    literals = re.compile(
        r"\b("
        + "|".join(sorted(CONTROL_FIELDS))
        + r')["\']?\s*(?:=|:)\s*(true|false|[0-9]+|"(?:\\.|[^"\\\n])*")'
    )
    return (
        Counter(declarations.findall(before)) == Counter(declarations.findall(after))
        and not (Counter(controls.findall(before)) - Counter(controls.findall(after)))
        and not (Counter(literals.findall(before)) - Counter(literals.findall(after)))
    )


def syntax_edit_scope(before: str, after: str, lines: list[int]) -> bool:
    """Token changes stay near diagnostics; quoted whitespace stays intact."""
    old, new = before.splitlines(keepends=True), after.splitlines(keepends=True)
    token = re.compile(r'"(?:\\.|[^"\\])*"|[^\s]')
    for kind, a, b, c, d in SequenceMatcher(
        None, old, new, autojunk=False
    ).get_opcodes():
        if kind == "equal":
            continue
        if token.findall("".join(old[a:b])) == token.findall("".join(new[c:d])):
            continue
        if not any(
            a >= max(0, line - 3) and max(a, b - 1) <= line + 1 for line in lines
        ):
            return False
    return True


async def recover_generation_syntax(
    files: dict[str, str],
    plan: DeploymentPlan,
    fixer: FixAgent,
    budget: AgentBudget,
    *,
    redact: Callable[[Any], Any],
    regenerate: Callable[[list[dict[str, Any]]], Awaitable[dict[str, str]]],
) -> tuple[dict[str, str], dict[str, Any]]:
    current, normalizations = normalize_blocks(redact(files))
    report: dict[str, Any] = {
        "path": "unchanged",
        "normalizations": normalizations,
        "rounds": [],
        "regeneration": "not_needed",
        "skipped_steps": [],
    }
    try:
        async with asyncio.timeout(max(0.001, budget.remaining())):
            issues = await native_syntax(current)
            report["initial_errors"] = len(issues)
            if not issues:
                report["path"] = "normalization" if normalizations else "unchanged"
                return current, report
            for index in (1, 2):
                if budget.remaining() < 1:
                    report["skipped_steps"].extend(
                        f"syntax_round_{i}" for i in range(index, 3)
                    )
                    break
                record: dict[str, Any] = {"index": index, "actions": []}
                report["rounds"].append(record)
                for path in sorted({issue.path for issue in issues}):
                    if budget.remaining() < 1:
                        break
                    diagnostics = [
                        redact(issue.feedback(current))
                        for issue in issues
                        if issue.path == path
                    ]
                    proposal = await fixer.propose(
                        path=path,
                        files=current,
                        findings=[],
                        plan=plan,
                        directive=SYNTAX_GUIDANCE,
                        remaining=budget.remaining(),
                        feedback=SYNTAX_GUIDANCE,
                        validation_failures=diagnostics,
                        syntax_only=True,
                    )
                    action = {
                        "file": path,
                        "accepted": False,
                        "reason": proposal.reason,
                        "input_tokens": proposal.input_tokens,
                        "output_tokens": proposal.output_tokens,
                        "cached_input_tokens": proposal.cached_input_tokens,
                        "llm_attempts": proposal.llm_attempts,
                        "attempt_details": [
                            asdict(a) for a in proposal.attempt_details
                        ],
                        "failure_category": proposal.failure_category,
                    }
                    record["actions"].append(action)
                    if not proposal.accepted or proposal.content is None:
                        continue
                    candidate = {**current, path: proposal.content}
                    if (
                        proposal.edits
                        or proposal.new_files
                        or not preserves_intent(current[path], proposal.content)
                        or not syntax_edit_scope(
                            current[path],
                            proposal.content,
                            [issue.line for issue in issues if issue.path == path],
                        )
                        or removes_security_controls(current, candidate)
                    ):
                        action["reason"] = "syntax_scope_or_control_changed"
                        continue
                    if await native_syntax(candidate, {path}):
                        action["reason"] = "invalid_syntax"
                        continue
                    current = candidate
                    action.update(accepted=True, reason="syntax_repaired")
                issues = await native_syntax(current)
                if not issues:
                    report["path"] = f"syntax_round_{index}"
                    report["final_errors"] = 0
                    return current, report
            if budget.remaining() >= 1:
                report["regeneration"] = "attempted"
                feedback = [redact(issue.feedback(current)) for issue in issues]
                replacement = await regenerate(feedback)
                replacement, records = normalize_blocks(replacement)
                report["normalizations"].extend(records)
                replacement_issues = await native_syntax(replacement)
                if not replacement_issues:
                    report.update(
                        path="regeneration", regeneration="accepted", final_errors=0
                    )
                    return replacement, report
                report["regeneration"] = "unparsable"
            else:
                report["regeneration"] = "deadline"
                report["skipped_steps"].append("regeneration")
            report.update(
                path="deadline"
                if report["regeneration"] == "deadline"
                else "unresolved",
                final_errors=len(issues),
            )
    except TimeoutError:
        report["skipped_steps"].extend(
            f"syntax_round_{i}" for i in range(len(report["rounds"]) + 1, 3)
        )
        if report["regeneration"] == "not_needed":
            report["skipped_steps"].append("regeneration")
        report.update(path="deadline", regeneration="deadline")
    except GeneratorError:
        report.update(
            path="unresolved", regeneration="failed", reason="regeneration_unavailable"
        )
    except ToolFailure:
        report.update(path="unresolved", reason="syntax_verification_unavailable")
    return current, report
