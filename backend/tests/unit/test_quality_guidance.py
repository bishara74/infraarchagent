"""FR-G-02/FR-S-03: prompts describe supported, complete artifacts."""

import pytest

from app.agents.prompts.security_fix import system_prompt


@pytest.mark.req("FR-S-03", "FR-V-03")
def test_repair_guidance_addresses_observed_provider_and_document_failures():
    prompt = system_prompt("preserve cost intent")
    for text in (
        "5.100.0",
        "6.68.0",
        "aws_s3_bucket_public_access_block",
        "bucket = aws_s3_bucket.NAME.id",
        "block_public_acls = true",
        "block_public_policy = true",
        "ignore_public_acls = true",
        "restrict_public_buckets = true",
        "new log/replica bucket",
        "name every play",
        "ansible.builtin.*",
        "changed_when",
        "creates",
        'non-empty top-level "panels"',
        "not an API",
        "log_destination",
    ):
        assert text in prompt
