"""Security strategy for the shared generator template."""

from app.agents.generators.base import GeneratorAgent
from app.domain.enums import Variant


class SecurityGeneratorAgent(GeneratorAgent):
    variant = Variant.SECURITY
    optimisation_directive = (
        "Optimise for security. Use least-privilege IAM with no wildcard actions "
        "or resources. Encrypt RDS storage, S3 objects, and EBS volumes at rest; "
        "use TLS/HTTPS in transit. Put every non-public planned service in a "
        "private subnet. Do not allow 0.0.0.0/0 ingress except HTTPS port 443 "
        "on public load balancers. Add S3 public access blocks, never hardcode "
        "secrets or credentials, and enable logging."
    )
