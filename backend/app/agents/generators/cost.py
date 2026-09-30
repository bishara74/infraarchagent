"""Cost strategy for the shared generator template."""

from app.agents.generators.base import GeneratorAgent
from app.domain.enums import Variant


class CostGeneratorAgent(GeneratorAgent):
    variant = Variant.COST
    optimisation_directive = (
        "Optimise for cost. Prefer AWS Free Tier eligible resources and the "
        "smallest reasonable sizes, such as t3.micro and db.t3.micro. Use "
        "on-demand pricing, single-AZ unless the plan requires otherwise, "
        "minimal replicas, no NAT gateway where a cheaper design works, "
        "and lightweight monitoring."
    )
