"""Small, deterministic gate for infrastructure descriptions."""

import re
import unicodedata


class InputRuleError(ValueError):
    code = "invalid_input"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class InputLengthError(InputRuleError):
    code = "invalid_length"


class InputContentError(InputRuleError):
    code = "invalid_content"


class NoInfrastructureIntentError(InputRuleError):
    code = "no_infrastructure_intent"


# A deliberately broad gate: one whole infrastructure term is enough to proceed.
INFRASTRUCTURE_TERMS = (
    "deploy",
    "deployment",
    "host",
    "provision",
    "scale",
    "scaling",
    "infrastructure",
    "cloud",
    "aws",
    "amazon web services",
    "ec2",
    "lambda",
    "server",
    "virtual machine",
    "vm",
    "instance",
    "compute",
    "autoscaling",
    "auto scaling",
    "load balancer",
    "alb",
    "elb",
    "web app",
    "web application",
    "website",
    "web server",
    "frontend",
    "backend",
    "application",
    "online",
    "platform",
    "e-commerce",
    "ecommerce",
    "endpoint",
    "serving",
    "websocket",
    "bot",
    "store",
    "cron",
    "scheduled",
    "scalable",
    "api",
    "microservice",
    "service",
    "static site",
    "cdn",
    "cloudfront",
    "route 53",
    "dns",
    "domain",
    "https",
    "ssl",
    "tls",
    "network",
    "vpc",
    "subnet",
    "gateway",
    "firewall",
    "security group",
    "database",
    "postgres",
    "postgresql",
    "mysql",
    "mariadb",
    "rds",
    "dynamodb",
    "redis",
    "cache",
    "s3",
    "bucket",
    "object storage",
    "storage",
    "volume",
    "ebs",
    "container",
    "docker",
    "dockerfile",
    "kubernetes",
    "k8s",
    "eks",
    "ecs",
    "fargate",
    "helm",
    "terraform",
    "ansible",
    "nginx",
    "jenkins",
    "ci/cd",
    "pipeline",
    "message queue",
    "queue",
    "sqs",
    "sns",
    "kafka",
    "monitoring",
    "metrics",
    "prometheus",
    "grafana",
    "cloudwatch",
    "logging",
)


def _term_pattern(term: str) -> str:
    if term.isalpha():
        return re.escape(term) + r"(?:s|es|ing|ed)?"
    return r"\s+".join(re.escape(part) for part in term.split())


_INTENT_PATTERN = re.compile(
    r"(?<!\w)(?:"
    + "|".join(_term_pattern(term) for term in INFRASTRUCTURE_TERMS)
    + r")(?!\w)",
    re.IGNORECASE,
)


def validate_request_text(text: str) -> str:
    """Return stripped input or raise the first applicable client error."""
    if any(
        unicodedata.category(char) == "Cc" and char not in "\n\r\t" for char in text
    ):
        raise InputContentError(
            "Please remove control characters from the description."
        )
    accepted = text.strip()
    length = len(accepted)
    if not 10 <= length <= 2000:
        raise InputLengthError(
            "Please describe your infrastructure in 10–2,000 characters "
            f"(you entered {length})."
        )
    if _INTENT_PATTERN.search(accepted) is None:
        raise NoInfrastructureIntentError(
            "This doesn't look like an infrastructure description. Describe what "
            "you want to deploy, for example: 'A Python web API with a PostgreSQL "
            "database behind a load balancer.'"
        )
    return accepted
