"""Fixed engineer decision categories; never remediation feedback."""

from typing import Literal

ReviewCategory = Literal[
    "requirements_not_met",
    "too_expensive",
    "organisational_policy",
    "security_concern",
    "operability",
    "too_complex",
    "other",
]
CATEGORIES = {
    "requirements_not_met": "requirements not met",
    "too_expensive": "too expensive",
    "organisational_policy": "organisational policy",
    "security_concern": "security concern",
    "operability": "operability",
    "too_complex": "too complex",
    "other": "other",
}
