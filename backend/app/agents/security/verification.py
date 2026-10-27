"""Offline Terraform regression verification within the security iteration budget."""

from app.domain.validation import ValidationCheck
from app.scanners.runner import CommandToolRunner, ProcessToolRunner
from app.validation.documents import PackageDocuments
from app.validation.terraform import validate_terraform
from app.validation.tools import DEFAULT_MIRROR
from app.validation.workspace import ValidationWorkspace, current_workspace


class TerraformVerifier:
    def __init__(self, runner: CommandToolRunner | None = None) -> None:
        self.runner = runner or ProcessToolRunner(60)

    async def checks(self, files: dict[str, str]) -> list[ValidationCheck]:
        if not any(
            p.startswith("terraform/") and p.endswith((".tf", ".tf.json"))
            for p in files
        ):
            return []
        workspace = current_workspace()
        owned = workspace is None
        workspace = workspace or ValidationWorkspace()
        try:
            async with workspace.check(files) as root:
                return await validate_terraform(
                    root,
                    set(files),
                    self.runner,
                    DEFAULT_MIRROR,
                    PackageDocuments.parse(files),
                )
        finally:
            if owned:
                workspace.close()


def failure_count(checks: list[ValidationCheck]) -> int | None:
    if any(
        c.status == "skipped"
        or (c.check_id == "terraform.file_input" and c.status == "failed")
        for c in checks
    ):
        return None
    return sum(
        c.check_id == "terraform.validate" and c.status == "failed" for c in checks
    )


def terraform_files(files: dict[str, str]) -> dict[str, str]:
    return {p: text for p, text in files.items() if p.startswith("terraform/")}


def restore_terraform(
    before: dict[str, str], candidate: dict[str, str]
) -> dict[str, str]:
    return {
        **{p: text for p, text in candidate.items() if not p.startswith("terraform/")},
        **terraform_files(before),
    }
