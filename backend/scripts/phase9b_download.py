"""Offline PR-04 attribution on disposable PostgreSQL with a loopback HTTP server."""

import argparse
import asyncio
import hashlib
import socket
import time
from pathlib import Path

import httpx
import uvicorn
from pydantic import SecretStr
from sqlalchemy import event

from app.core.auth import COOKIE_NAME
from app.core.config import Settings
from app.db.repositories.users import UserRepository
from app.db.session import make_app_engine
from app.main import create_app
from scripts.phase9_common import environment, write_json
from scripts.phase9_report import statistics_for, write_csv
from scripts.seed_benchmark_package import seed_package
from tests.database_safety import assert_test_database_settings


def summarize(rows: list[dict]) -> dict:
    return {
        condition: {
            **statistics_for(
                [r["seconds"] for r in rows if r["condition"] == condition]
            ),
            "verdict": "INCOMPLETE"
            if not any(r["condition"] == condition for r in rows)
            else "PASS"
            if all(r["seconds"] <= 2 for r in rows if r["condition"] == condition)
            else "FAIL",
        }
        for condition in ("session", "shared_key", "prevalidated_session")
    }


async def measure(output: Path, repeat: int = 10) -> None:
    if repeat < 1:
        raise ValueError("Repeat count must be positive")
    settings = Settings(_env_file=None)
    assert_test_database_settings(settings)
    if settings.llm_provider.value != "stub":
        raise ValueError("Only stub verification settings are allowed")
    output.mkdir(parents=True, exist_ok=False)
    settings = settings.model_copy(
        update={"api_key": SecretStr("phase9b-measurement-only")}
    )
    engine = make_app_engine(settings, test=True)
    app = create_app(settings, engine)
    samples = []
    active = {}
    activity = app.state.auth.activity
    user_method = app.state.auth.user
    cached_session = None
    control = False

    async def timed_activity(digest):
        start = time.perf_counter()
        try:
            return cached_session if control else await activity(digest)
        finally:
            active["session_seconds"] = time.perf_counter() - start

    async def timed_user(user_id):
        start = time.perf_counter()
        try:
            return await user_method(user_id)
        finally:
            active["user_seconds"] = time.perf_counter() - start

    def before(_conn, _cursor, _statement, _parameters, context, _many):
        context.phase9b_start = time.perf_counter()

    def after(_conn, _cursor, _statement, _parameters, context, _many):
        active["database_seconds"] = (
            active.get("database_seconds", 0)
            + time.perf_counter()
            - context.phase9b_start
        )

    from app.pipeline import results as result_module

    original_zip = result_module.package_zip

    def timed_zip(*args, **kwargs):
        start = time.perf_counter()
        try:
            return original_zip(*args, **kwargs)
        finally:
            active["zip_seconds"] = time.perf_counter() - start

    app.state.auth.activity = timed_activity
    app.state.auth.user = timed_user
    result_module.package_zip = timed_zip
    event.listen(engine.sync_engine, "before_cursor_execute", before)
    event.listen(engine.sync_engine, "after_cursor_execute", after)
    server = None
    task = None
    sock = socket.socket()
    try:
        seed = await seed_package(app.state.session_factory)
        async with app.state.session_factory() as session, session.begin():
            # No password login is performed; identity is synthetic and isolated.
            user = await UserRepository(session).create(
                "phase9b-measurement", "not-a-login-hash"
            )
            user_id = user.id
        token = await app.state.auth.login(user_id)
        from app.core.auth import token_hash

        cached_session = await activity(token_hash(token))
        assert cached_session is not None
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        sock.setblocking(False)
        port = sock.getsockname()[1]
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=port,
            lifespan="off",
            log_level="error",
            access_log=False,
        )
        server = uvicorn.Server(config)
        task = asyncio.create_task(server.serve(sockets=[sock]))
        # Yield for socket startup; this is synchronization, not timed workload.
        while not server.started:
            if task.done():
                await task
            await asyncio.sleep(0.01)
        url = f"http://127.0.0.1:{port}/api/pipeline/{seed['run_id']}/download/cost"
        fingerprint = None
        async with httpx.AsyncClient(timeout=60, trust_env=False) as client:
            for round_index in range(-2, repeat):
                conditions = ["session", "shared_key", "prevalidated_session"]
                if round_index % 2:
                    conditions.reverse()
                for condition in conditions:
                    control = condition == "prevalidated_session"
                    client.cookies.clear()
                    headers = {}
                    if condition == "shared_key":
                        headers["X-API-Key"] = settings.api_key.get_secret_value()
                    else:
                        client.cookies.set(COOKIE_NAME, token)
                    active.clear()
                    start = time.perf_counter()
                    response = await client.get(url, headers=headers)
                    elapsed = time.perf_counter() - start
                    assert response.status_code == 200
                    digest = hashlib.sha256(response.content).hexdigest()
                    fingerprint = fingerprint or digest
                    assert digest == fingerprint
                    assert 9_900_000 < len(response.content) <= 10_000_000
                    if round_index >= 0:
                        samples.append(
                            {
                                "round": round_index,
                                "condition": condition,
                                "seconds": elapsed,
                                "archive_bytes": len(response.content),
                                "archive_sha256": digest,
                                **active,
                            }
                        )
            # Restore the real guard and prove revocation still blocks download.
            control = False
            await app.state.auth.revoke(token)
            client.cookies.clear()
            client.cookies.set(COOKIE_NAME, token)
            assert (await client.get(url)).status_code == 401
        report = {
            "synthetic": True,
            "warmups_per_condition": 2,
            "measured_per_condition": repeat,
            "transport": "loopback HTTP, complete response body",
            "seed": seed,
            "summary": summarize(samples),
            "samples": samples,
            "revoked_session_status": 401,
        }
        write_json(output / "results.json", report)
        write_json(
            output / "environment.json",
            environment(mode="stub", provider="stub", model="stub"),
        )
        write_csv(output / "timings.csv", samples)
        lines = [
            "# PR-04 offline session-check attribution",
            "",
            (
                "Synthetic rejected package; no LLM/scanner/validator executed. "
                "Same near-10 MB archive and SHA-256 in every condition. Two warm-"
                "ups and ten alternating measured requests per condition; loopback"
                " HTTP timing includes full response consumption. Test-only "
                "prevalidated_session skips the session touch lookup and is "
                "attribution only, not a production endpoint or authenticated "
                "compliance result."
            ),
            "",
            "| Condition | Count | Median s | Max s | ≤2 s every request |",
            "|---|---:|---:|---:|---|",
        ]
        for condition, stats in report["summary"].items():
            lines.append(
                f"| {condition} | {stats['count']} | {stats['median']:.6f} | "
                f"{stats['max']:.6f} | {stats['verdict']} |"
            )
        lines += [
            "",
            (
                "Per-request session/user time, SQL execution totals and ZIP work "
                "are recorded in timings.csv. SQL totals overlap their enclosing "
                "operations and must not be added to them. Shared-key skips "
                "session/user work; prevalidated_session retains user lookup. "
                "Revocation after restoring the original guard returns HTTP 401. "
                "These are local descriptive samples, not proof for other machines"
                " or provider conditions. Prior 9h measurements remain unchanged. "
                "No production authentication guard was removed."
            ),
        ]
        (output / "summary.md").write_text("\n".join(lines) + "\n")
        print("PR-04 measurements:", report["summary"])
    finally:
        result_module.package_zip = original_zip
        app.state.auth.activity = activity
        app.state.auth.user = user_method
        event.remove(engine.sync_engine, "before_cursor_execute", before)
        event.remove(engine.sync_engine, "after_cursor_execute", after)
        if server:
            server.should_exit = True
        if task:
            await task
        sock.close()
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    asyncio.run(measure(args.output_dir))


if __name__ == "__main__":
    main()
