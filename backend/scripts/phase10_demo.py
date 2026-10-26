"""Create explicitly synthetic defence data through the application's HTTP services."""

import argparse
import asyncio
import getpass
import json
from pathlib import Path
from urllib.parse import urlsplit

import httpx


def local_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Use a loopback HTTP URL without credentials or a path")
    return value.rstrip("/")


def checked(response: httpx.Response, statuses: tuple[int, ...] = (200,)) -> dict:
    if response.status_code not in statuses:
        raise RuntimeError(
            "Demo service request failed; inspect the application's safe diagnostics"
        )
    return response.json()


async def settled(client: httpx.AsyncClient, run_id: str, interval: float) -> dict:
    async with asyncio.timeout(600):
        while True:
            result = checked(await client.get(f"/api/pipeline/{run_id}/results"))
            if result["run"]["status"] in {
                "success",
                "partial_success",
                "failed",
            } and not any(
                row["retry_in_progress"]
                or row["status"] in {"scanning", "remediating", "validating"}
                for row in result["packages"]
            ):
                return result
            await asyncio.sleep(interval)


async def seed(client: httpx.AsyncClient, *, interval: float = 0.2) -> dict:
    account = checked(await client.get("/api/auth/session")).get("user")
    if not account or account["role"] != "admin":
        raise RuntimeError("Sign in as a named administrator for demo seeding")
    controls = checked(await client.get("/api/lessons/control"))
    if not controls.get("admin_direct_activation"):
        raise RuntimeError(
            "Start the dedicated demo server with LESSONS_ADMIN_DIRECT_ACTIVATION=true"
        )
    output = {"synthetic": True, "provider": "stub", "runs": [], "lesson_id": None}
    for disposition in ("pending", "approved", "rejected", "retried"):
        accepted = checked(
            await client.post(
                "/api/pipeline/run",
                json={
                    "text": (
                        f"Synthetic defence demo ({disposition}): create an "
                        "AWS web service with Terraform."
                    ),
                    "config": {"provider": "stub", "model": "stub"},
                },
            ),
            (202,),
        )
        run_id = accepted["run_id"]
        result = await settled(client, run_id, interval)
        security = next(
            (row for row in result["packages"] if row["variant"] == "security"), None
        )
        if not security or security["status"] != "pending_review":
            raise RuntimeError(
                "Start a dedicated stub server with PIPELINE_DEMO_SCENARIO=review"
            )
        path = f"/api/pipeline/{run_id}/packages/security/review"
        if disposition in {"approved", "rejected"}:
            checked(
                await client.post(
                    path,
                    json={
                        "action": "approve" if disposition == "approved" else "reject",
                        "category": "accepted_risk"
                        if disposition == "approved"
                        else "operability",
                        "reason": (
                            f"Synthetic defence demo: deliberately {disposition} "
                            "for demonstration; no cloud deployment was verified."
                        ),
                    },
                )
            )
            result = checked(await client.get(f"/api/pipeline/{run_id}/results"))
        elif disposition == "retried":
            checked(
                await client.post(
                    path,
                    json={
                        "action": "retry",
                        "feedback": "Declare the missing review_demo local.",
                    },
                ),
                (202,),
            )
            result = await settled(client, run_id, interval)
        security = next(
            row for row in result["packages"] if row["variant"] == "security"
        )
        expected = {
            "pending": "pending_review",
            "approved": "engineer_approved",
            "rejected": "rejected",
            "retried": "checks_passed",
        }[disposition]
        if security["status"] != expected:
            raise RuntimeError("Synthetic demo did not reach its expected label")
        if disposition == "approved":
            lesson = {
                "decision_id": security["review_decision"]["decision_id"],
                "scope_role": "architect",
                "category": "accepted_risk",
                "applies_to": ["logging"],
                "text": "Prefer explicit retention periods for operational logs.",
            }
            preview = checked(await client.post("/api/lessons/check", json=lesson))
            if not preview["filter_result"]["passed"]:
                raise RuntimeError("Demo lesson did not pass the current filter")
            approved = checked(await client.post("/api/lessons", json=lesson), (201,))
            if (
                approved["status"] != "approved"
                or approved["approval"] != "admin_direct"
            ):
                raise RuntimeError("Demo lesson was not activated")
            output["lesson_id"] = approved["id"]
        output["runs"].append(
            {
                "run_id": run_id,
                "disposition": disposition,
                "labels": {row["variant"]: row["status"] for row in result["packages"]},
            }
        )
    return output


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", type=local_url, default="http://127.0.0.1:8000")
    parser.add_argument("--username")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Choose a fresh demo index path")
    username = args.username or input("Named demo administrator: ")
    password = getpass.getpass("Demo account password: ")
    async with httpx.AsyncClient(
        base_url=args.base_url,
        headers={"Origin": args.base_url},
        trust_env=False,
        follow_redirects=False,
        timeout=30,
    ) as client:
        checked(
            await client.post(
                "/api/auth/login", json={"username": username, "password": password}
            )
        )
        result = await seed(client)
        checked(await client.post("/api/auth/logout"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("Synthetic demo created; the index contains IDs and labels only.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, RuntimeError, httpx.HTTPError, TimeoutError):
        raise SystemExit(
            "Demo seed failed. Check the dedicated stub/review server and named "
            "admin login; retain any created synthetic runs."
        ) from None
