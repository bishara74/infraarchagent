"""Shared deployment correctness guidance; never substitutes for validation."""

PROVIDER_GUIDANCE = "\n".join(
    (
        "Offline provider mirror: hashicorp/aws 5.100.0 and 6.68.0; random 3.9.1;",
        "kubernetes 2.38.0; helm 2.17.0; tls 4.4.1; null 3.3.2.",
        "Choose a compatible mirrored version and use its actual resource schema.",
        "Every Terraform module must explicitly declare terraform/required_providers,",
        "including provider sources and constraints satisfiable by this mirror.",
        "Use separate lines or commas between object attributes; no HCL semicolons.",
        "Declare every var.* input exactly once, normally in variables.tf;",
        "never give secret inputs defaults. Declare every referenced data source.",
        "Never duplicate resources across the requested file and new_files.",
        "Preserve valid existing resources and deployment/optimisation intent.",
    )
)

S3_GUIDANCE = "\n".join(
    (
        "For each S3 bucket, including every new log/replica bucket, use a standalone",
        "resource aws_s3_bucket_public_access_block with "
        "bucket = aws_s3_bucket.NAME.id",
        "and block_public_acls = true, block_public_policy = true,",
        "ignore_public_acls = true, restrict_public_buckets = true (separate lines).",
        "Do not place these arguments directly on aws_s3_bucket and do not nest a",
        "public_access_block block inside it. Preserve correctly linked protection.",
        "Use provider-supported standalone versioning/encryption/logging resources.",
        "For flow logs use log_destination, not log_group_name/resource_id.",
        "For load balancers use drop_invalid_header_fields = true,",
        "not load_balancer_attributes blocks. Empty security-group rule blocks",
        "are incomplete rules; use supported empty rule collections to deny traffic.",
        "CKV2_AWS_12: manage the VPC's default group with aws_default_security_group",
        "and NO ingress/egress blocks. Never use empty blocks or revoke_all_rules.",
        "aws_flow_log custom log_format field placeholders must be literal $${...},",
        "for example $${version} $${account-id}, preserving real Terraform references.",
        "S3 replication uses aws_s3_bucket_replication_configuration with its",
        "provider-supported rule/destination blocks, never inline bucket replication.",
    )
)

DOCUMENT_GUIDANCE = "\n".join(
    (
        "Ansible: name every play; use fully qualified ansible.builtin.* modules.",
        "For command/shell tasks use suitable changed_when or creates handling",
        "that accurately describes changes; do not mask changes or lint failures.",
        "Grafana provisioning dashboards must be plain dashboard JSON, not an API",
        'wrapper: use a non-empty top-level "panels" array, with real panel types',
        "and useful queries. Do not substitute datasource configuration "
        "for dashboards.",
        "Helm charts require non-empty templates/ manifests, not just Chart.yaml.",
        "Define every referenced named Helm helper in the same chart; use standard",
        "helm-create helpers or explicit manifests, never undefined include calls.",
        (
            "Use ordinary quotes inside Go templates, not liter"
            "al backslash-escaped quotes."
        ),
        "All HCL, YAML and JSON documents must parse; preserve required file types.",
    )
)
