"""Labelled offline verification load rehearsal; no model or quality-rate input."""

import asyncio
import time
from types import SimpleNamespace
from uuid import uuid4

from app.agents.budget import AgentBudget
from app.agents.security.agent import SecurityAgent
from app.agents.security.fix import FixProposal
from app.agents.security.verification import TerraformVerifier
from app.core.config import Settings
from app.domain.enums import Variant
from app.domain.plan import DeploymentPlan
from app.pipeline.demo_stub import DEMO_PLAN
from app.pipeline.stages import StageContext
from app.scanners.runner import ProcessToolRunner
from app.scanners.scan import ScanResult
from app.validation.engine import BoundedRunner
from app.validation.measurement import initialization_metrics
from app.validation.workspace import ValidationWorkspace
from scripts.phase9e_metrics import measurement_summary


class ScriptedFix:
    async def propose(self, **kwargs):
        return FixProposal(
            kwargs["path"],
            True,
            None,
            kwargs["files"][kwargs["path"]] + "\n# scripted verification edit\n",
            {},
            (),
        )


class ScriptedScanner:
    async def scan(self, files, *args, **kwargs):
        return ScanResult([], {"terraform": "ok", "checkov": "ok", "trivy": "ok"})


async def verification_rehearsal(*, runner=None, settings=None) -> dict:
    settings = settings or Settings(_env_file=None)
    runner = runner or BoundedRunner(ProcessToolRunner(60), asyncio.Semaphore(3))
    plan = DeploymentPlan.model_validate({**DEMO_PLAN, "file_types": ["terraform"]})

    async def package(index, version):
        workspace = ValidationWorkspace()
        records = []
        source = (
            "terraform {\n required_providers {\n aws = {\n"
            f' source = "hashicorp/aws"\n version = "= {version}"\n'
            ' }\n }\n}\nresource "aws_vpc" "main" {\n'
            ' cidr_block = "10.0.0.0/16"\n}\n'
        )
        files = {"terraform/main.tf": source}
        security = SecurityAgent(
            ScriptedScanner(),
            ScriptedFix(),
            None,
            settings,
            terraform_verifier=TerraformVerifier(runner),
        )
        ctx = StageContext(uuid4(), SimpleNamespace(), plan)
        baseline = await security.scanner.scan(files)
        try:
            with workspace.activate():
                for iteration in range(1, 3):
                    record = {}
                    start_metrics = len(workspace.terraform_metrics)
                    started = time.monotonic()
                    try:
                        async with asyncio.timeout(60):
                            candidate, _, _, baseline = await security._fix_iteration(
                                ctx,
                                Variant.SECURITY,
                                files,
                                {"terraform/main.tf": []},
                                AgentBudget(60),
                                baseline,
                                record,
                                feedback=None,
                                validation_failures=[],
                            )
                        files = candidate
                    except TimeoutError:
                        record["deadline_only"] = bool(
                            record.get("candidate_created")
                            and not record.get("reasons")
                        )
                        record.setdefault("reasons", []).append("iteration_deadline")
                        record["outcome"] = (
                            "rolled_back"
                            if record.get("candidate_created")
                            else "stopped"
                        )
                    record.update(
                        initialization_metrics(
                            workspace.terraform_metrics[start_metrics:]
                        )
                    )
                    seconds = record.get(
                        "terraform_verification_seconds", 0
                    ) + record.get("security_verification_seconds", 0)
                    record.update(
                        stage="security_iteration_verification",
                        duration_seconds=seconds,
                        phase="security",
                        iteration=iteration,
                        iteration_seconds=time.monotonic() - started,
                        package=index,
                        provider_version=version,
                    )
                    records.append(record)
        finally:
            workspace.close()
        return records

    records = [
        record
        for package_records in await asyncio.gather(
            package(1, "5.100.0"), package(2, "6.68.0"), package(3, "6.68.0")
        )
        for record in package_records
    ]
    summary, table = measurement_summary(records)
    return {
        "label": "Separate scripted-fix verification rehearsal; "
        "real offline Terraform; "
        "three concurrent private workspaces; excluded from checks-passed rates "
        "and PR thresholds.",
        "records": records,
        "summary": summary,
        "table": table,
    }
