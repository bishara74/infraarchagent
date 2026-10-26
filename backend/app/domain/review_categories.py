"""Fixed engineer decision categories; never remediation feedback."""

from typing import Literal

RejectionCategory = Literal[
    "requirements_not_met",
    "too_expensive",
    "organisational_policy",
    "security_concern",
    "operability",
    "too_complex",
    "other",
]
REJECTION_CATEGORIES = {
    "requirements_not_met": "requirements not met",
    "too_expensive": "too expensive",
    "organisational_policy": "organisational policy",
    "security_concern": "security concern",
    "operability": "operability",
    "too_complex": "too complex",
    "other": "other",
}

ApprovalCategory = Literal[
    "meets_requirements",
    "accepted_risk",
    "approved_with_follow_ups",
    "organisational_exception",
    "other",
]
APPROVAL_CATEGORIES = {
    "meets_requirements": "meets requirements",
    "accepted_risk": "accepted risk",
    "approved_with_follow_ups": "approved with follow-ups",
    "organisational_exception": "organisational exception",
    "other": "other",
}
ReviewCategory = RejectionCategory | ApprovalCategory
CATEGORIES = {**REJECTION_CATEGORIES, **APPROVAL_CATEGORIES}
