"""Benchmark-only routing options, public status confirmation and call accounting."""

import sys
from collections import Counter

from app.domain.agent_selection import ROLES
from app.llm.public_catalogue import CatalogueError, provider_health, provider_key


def preferences(args) -> dict:
    result = {}
    preference = getattr(args, "provider_preference", None)
    if preference:
        result.update({role: preference for role in ROLES[1:]})
    if getattr(args, "architect_provider_preference", None):
        result["architect"] = args.architect_provider_preference
    return result


async def status_preflight(
    selections: dict, *, force=False, transport=None, confirm=None
) -> list[dict]:
    checks = {}
    for selection in selections.values():
        order = selection.get("provider_order") or []
        if order:
            key = (selection["model"], order[0])
            if key not in checks:
                checks[key] = await provider_health(*key, transport=transport)
    if any(c["status"] != "ok" for c in checks.values()):
        print(
            "Warning: preferred provider status unavailable, degraded or unknown.",
            file=sys.stderr,
        )
        if not force:
            if confirm is None:

                def confirm():
                    return (
                        sys.stdin.isatty()
                        and input("Continue with provider fallbacks allowed? [y/N] ")
                        .strip()
                        .lower()
                        == "y"
                    )

            if not confirm():
                raise CatalogueError(
                    "Provider status requires confirmation or --force; no submission."
                )
    return list(checks.values())


def routing_statistics(telemetry: list[dict], selections: dict) -> dict:
    seen, counts, providers = set(), Counter(), Counter()
    for index, call in enumerate(telemetry):
        if call.get("kind") != "llm":
            continue
        identity = call.get("call_id") or call.get("id") or ("unidentified", index)
        if identity in seen:
            continue
        seen.add(identity)
        served = call.get("served_by")
        providers[served or "unknown"] += 1
        order = selections.get(call.get("role"), {}).get("provider_order") or []
        if not order:
            continue
        role = call.get("role")
        category = (
            "unknown"
            if not served
            else "preferred"
            if provider_key(served) == provider_key(order[0])
            else "fallback"
        )
        counts[category] += 1
        counts[str(role) + ":" + category] += 1
    known = counts["preferred"] + counts["fallback"]
    return {
        "preferred_calls": counts["preferred"],
        "fallback_calls": counts["fallback"],
        "unknown_calls": counts["unknown"],
        "known_preference_calls": known,
        "fallback_share": counts["fallback"] / known if known else None,
        "any_fallback": counts["fallback"] > 0,
        "served_by": dict(providers),
        "by_role": {
            role: {
                k: counts[role + ":" + k] for k in ("preferred", "fallback", "unknown")
            }
            for role in ROLES
        },
    }
