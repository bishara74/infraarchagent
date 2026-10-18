"""Offline benchmark-A replay; scripted corrections are explicit test oracles.

No model is called. These replacements are corpus fixtures, never production
normalization rules or an estimate of real fixer reliability.
"""

import argparse
import asyncio
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.agents.budget import AgentBudget
from app.agents.generation_syntax import recover_generation_syntax
from app.agents.security.fix import FixProposal
from app.domain.plan import DeploymentPlan
from app.validation.syntax import native_syntax, normalize_blocks
from app.validation.workspace import ValidationWorkspace
from scripts.phase9_common import ROOT


def scripted_fixture(source: str) -> str:
    source = source.replace(
        "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*]",
        'ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]',
    )
    for service in ("monitoring.rds.amazonaws.com", "ecs-tasks.amazonaws.com"):
        for separator in (" ", "; "):
            old = (
                'statement { actions = ["sts:AssumeRole"]; principals { '
                'type = "Service"' + separator + 'identifiers = ["' + service + '"] } }'
            )
            new = (
                'statement {\n actions = ["sts:AssumeRole"]\n principals {\n '
                'type = "Service"\n identifiers = ["' + service + '"]\n }\n }'
            )
            source = source.replace(old, new)
    source = source.replace('image!=""', 'image!=\\"\\"')
    source = source.replace('container!=""', 'container!=\\"\\"')
    for port in (9090, 3000):
        source = source.replace(
            f'from_port = {port} to_port = {port} protocol = "tcp" '
            "security_groups = [aws_security_group.api_sg.id]",
            f'from_port = {port}\n to_port = {port}\n protocol = "tcp"\n '
            "security_groups = [aws_security_group.api_sg.id]",
        )
    source = source.replace(
        'rule { apply_server_side_encryption_by_default { sse_algorithm = "AES256" } }',
        "rule {\n apply_server_side_encryption_by_default {\n "
        'sse_algorithm = "AES256"\n }\n }',
    )
    return source


async def replay(directory: Path) -> dict:
    cases = []
    digests = {}
    for path in sorted(directory.glob("*.json")):
        raw = path.read_bytes()
        digests[path] = hashlib.sha256(raw).hexdigest()
        run = json.loads(raw)
        plan = DeploymentPlan.model_validate(run["plan"])
        for package in run["packages"]:
            original = package["original_files"]
            workspace = ValidationWorkspace()
            try:
                with workspace.activate():
                    initial = await native_syntax(original)
                    if not initial:
                        continue
                    normalized, records = normalize_blocks(original)
                    after_normalization = await native_syntax(normalized)

                    class ScriptedFixer:
                        async def propose(self, **kwargs):
                            file = kwargs["path"]
                            corrected = scripted_fixture(kwargs["files"][file])
                            corrected = normalize_blocks({file: corrected})[0][file]
                            return FixProposal(
                                file, True, None, corrected, {}, (), llm_attempts=0
                            )

                    async def regenerate(feedback, original=original):
                        return {p: scripted_fixture(s) for p, s in original.items()}

                    result, report = await recover_generation_syntax(
                        original,
                        plan,
                        ScriptedFixer(),
                        AgentBudget(145),
                        redact=lambda value: value,
                        regenerate=regenerate,
                    )
                    final = await native_syntax(result)
                    original_files = {issue.path for issue in initial}
                    normalized_files = {issue.path for issue in after_normalization}
                    final_files = {issue.path for issue in final}
                    historical = [
                        c
                        for c in package["validation_report"]["checks"]
                        if c["status"] == "failed"
                        and c["message"]
                        in {
                            "Document could not be parsed",
                            "Invalid multi-line string",
                            "Invalid single-argument block definition",
                        }
                    ]
                    cases.append(
                        {
                            "run_id": path.stem,
                            "variant": package["variant"],
                            "files": sorted(original_files),
                            "initial_diagnostics": len(initial),
                            "normalized_diagnostics": len(after_normalization),
                            "final_diagnostics": len(final),
                            "normalization_blocks": len(records),
                            "deterministic_files_repaired": len(
                                original_files - normalized_files
                            ),
                            "scripted_files_repaired": len(
                                normalized_files - final_files
                            ),
                            "path": report["path"],
                            "historical_syntax_findings": sum(
                                v["rule_id"] == "TERRAFORM_SYNTAX"
                                for v in package["security_report"]["final"].get(
                                    "remaining_blocking", []
                                )
                            ),
                            "historical_messages": dict(
                                Counter(c["message"] for c in historical)
                            ),
                        }
                    )
            finally:
                workspace.close()
    assert all(
        hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in digests.items()
    )
    return {
        "mode": "offline_native_and_scripted_no_llm",
        "input_files_unchanged": True,
        "input_hashes": {p.name: h for p, h in digests.items()},
        "affected_packages": len(cases),
        "affected_files": sum(len(c["files"]) for c in cases),
        "deterministic_packages_repaired": sum(
            c["normalized_diagnostics"] == 0 for c in cases
        ),
        "deterministic_files_repaired": sum(
            c["deterministic_files_repaired"] for c in cases
        ),
        "scripted_additional_files_repaired": sum(
            c["scripted_files_repaired"] for c in cases
        ),
        "final_packages_repaired": sum(c["final_diagnostics"] == 0 for c in cases),
        "initial_native_diagnostics": sum(c["initial_diagnostics"] for c in cases),
        "after_normalization_native_diagnostics": sum(
            c["normalized_diagnostics"] for c in cases
        ),
        "final_native_diagnostics": sum(c["final_diagnostics"] for c in cases),
        "historical_syntax_findings": sum(
            c["historical_syntax_findings"] for c in cases
        ),
        "recovery_paths": dict(Counter(c["path"] for c in cases)),
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results", type=Path, default=ROOT / ".cache/phase9f-a-results"
    )
    args = parser.parse_args()
    print(json.dumps(asyncio.run(replay(args.results)), indent=2))


if __name__ == "__main__":
    main()
