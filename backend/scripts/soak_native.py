# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Run the offline native soak against one disposable backend process."""

import argparse
import asyncio
import glob
import json
import os
import platform
import re
import resource
import secrets
import signal
import socket
import subprocess
import sys
import sysconfig
import tempfile
import time
import traceback
from collections import deque
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.diagnostics import fault_log_path, native_versions
from app.core.logging import REDACTED, RedactingFilter
from app.core.telemetry import interval_union
from app.domain.enums import PackageStatus
from app.domain.states import TERMINAL_RUNS
from app.scanners.runner import scanner_versions
from scripts.phase9_common import ROOT, write_json

BACKEND = ROOT / "backend"
OUTPUT = ROOT / "docs/evals/phase11b-soak"
PINNED = {"checkov": "3.3.21", "trivy": "0.69.3", "terraform": "1.16.4"}
OPERATIONS = {"checkov", "trivy", "terraform.validate"}
ALLOCATOR_KEYS = ("LD_PRELOAD", "MALLOC_CHECK_", "GLIBC_TUNABLES")
DATABASE_URL = re.compile(r"\bpostgres(?:ql)?(?:\+\w+)?://[^\s\"'`<>]+", re.I)
BUSY_DATABASE = text("""
    SELECT EXISTS (
        SELECT FROM pg_stat_activity
        WHERE datname = current_database() AND backend_type = 'client backend'
          AND pid <> pg_backend_pid()
    )
""")


class SoakError(RuntimeError):
    """A reportable error with a fixed message that contains no credentials."""


def error_redactor(api_key: str) -> Callable[[str], str]:
    protected = []
    for name in ("TEST_DATABASE_URL", "TEST_MIGRATION_DATABASE_URL"):
        raw = os.getenv(name, "")
        protected.append(raw)
        try:
            protected.append(make_url(raw).password or "")
        except (ArgumentError, ValueError):
            pass
    redact = RedactingFilter(api_key, *protected).redact
    return lambda value: DATABASE_URL.sub(REDACTED, redact(value))


def innermost_errors(error: BaseException) -> Iterator[BaseException]:
    if isinstance(error, BaseExceptionGroup):
        for child in error.exceptions:
            yield from innermost_errors(child)
    elif error.__cause__ is not None:
        yield from innermost_errors(error.__cause__)
    elif error.__context__ is not None and not error.__suppress_context__:
        yield from innermost_errors(error.__context__)
    else:
        yield error


def record_error(
    report: dict, error: BaseException, redact: Callable[[str], str]
) -> None:
    # Use the formatter behind format_exception without its default group limits.
    details = traceback.TracebackException.from_exception(
        error, max_group_width=sys.maxsize, max_group_depth=sys.maxsize
    )
    report["error_detail"] = redact("".join(details.format()))
    messages = dict.fromkeys(
        redact(str(cause)).strip() or type(cause).__name__
        for cause in innermost_errors(error)
    )
    report["error"] = next(iter(messages)).splitlines()[0]
    for message in messages:
        print(message, file=sys.stderr)


def positive(value: str) -> int:
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return result


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=positive, default=os.getenv("RUNS", "60"))
    parser.add_argument(
        "--concurrency", type=positive, default=os.getenv("CONCURRENCY", "3")
    )
    parser.add_argument(
        "--cancel-every", type=positive, default=os.getenv("CANCEL_EVERY", "10")
    )
    parser.add_argument(
        "--malloc-check", choices=("on", "off"), default=os.getenv("MALLOC_CHECK", "on")
    )
    args = parser.parse_args(argv)
    if args.malloc_check not in ("on", "off"):
        parser.error("MALLOC_CHECK must be on or off")
    return args


def should_cancel(number: int, every: int) -> bool:
    return number % every == 0


def environment(concurrency: int) -> dict[str, str]:
    env = {
        k: os.environ[k]
        for k in ("PATH", "LANG", "LC_ALL", "TMPDIR")
        if k in os.environ
    }
    for role, setting, test_setting in (
        ("infraarch_app", "DATABASE_URL", "TEST_DATABASE_URL"),
        ("infraarch_owner", "MIGRATION_DATABASE_URL", "TEST_MIGRATION_DATABASE_URL"),
    ):
        value = os.getenv(test_setting, "")
        try:
            url = make_url(value)
            valid = (
                url.drivername == "postgresql+asyncpg"
                and url.username == role
                and url.database == "infraarch_test"
                and url.host in {"localhost", "127.0.0.1", "::1"}
                and not {"host", "port", "user", "database", "dsn"}.intersection(
                    url.query
                )
            )
        except (ArgumentError, ValueError):
            valid = False
        if not valid:
            raise SoakError(
                f"Export {test_setting} for the local infraarch_test {role} role."
            )
        env[setting] = env[test_setting] = value
    env.update(
        INFRAARCH_TEST_BOOTSTRAP="1",
        PYTHONPATH=os.pathsep.join(map(str, (BACKEND / "tests/bootstrap", BACKEND))),
        LLM_PROVIDER="stub",
        SECURITY_FIX_PROVIDER="stub",
        MAX_CONCURRENT_RUNS=str(concurrency),
    )
    return env


async def require_idle_database(url: str) -> None:
    engine = create_async_engine(url, connect_args={"timeout": 5, "command_timeout": 5})
    try:
        async with engine.connect() as connection:
            busy = await connection.scalar(BUSY_DATABASE)
    except Exception as error:
        raise SoakError("Could not check local infraarch_test connections.") from error
    finally:
        await engine.dispose()
    if busy:
        raise SoakError(
            "infraarch_test is in use. Stop other test or soak sessions first."
        )


def allocator_environment(env: dict[str, str], mode: str) -> tuple[dict[str, str], str]:
    child = {key: value for key, value in env.items() if key not in ALLOCATOR_KEYS}
    if mode == "off":
        return child, "off"
    libc, release = platform.libc_ver()
    if libc != "glibc" or not release:
        raise SoakError("Malloc checking requires glibc.")
    child.update(MALLOC_CHECK_="3", GLIBC_TUNABLES="glibc.malloc.check=3")
    if tuple(map(int, release.split(".")[:2])) < (2, 34):
        return child, "glibc"
    multiarch = sysconfig.get_config_var("MULTIARCH") or ""
    library = next(
        (
            candidate
            for parent in (
                Path("/lib"),
                Path("/usr/lib"),
                Path("/lib64"),
                Path("/usr/lib64"),
            )
            for directory in (parent / multiarch, parent)
            for name in ("libc_malloc_debug.so.0", "libc_malloc_debug.so")
            if (candidate := directory / name).is_file()
        ),
        None,
    )
    if library is None:
        raise SoakError("Malloc checking requires an installed libc_malloc_debug.so.")
    child["LD_PRELOAD"] = str(library)
    return child, "glibc-preload"


def verify_scanners() -> dict[str, str]:
    versions = {}
    for tool, result in scanner_versions().items():
        version = str(result["version"])
        if not result["available"] or not re.search(
            rf"(?:^|[\s:v]){re.escape(PINNED[tool])}(?=\s|$)", version
        ):
            raise SoakError(f"The soak requires {tool} {PINNED[tool]} on PATH.")
        versions[tool] = PINNED[tool]
    return versions


def allow_cores() -> None:
    _, hard = resource.getrlimit(resource.RLIMIT_CORE)
    resource.setrlimit(resource.RLIMIT_CORE, (hard, hard))


def live_resources(pid: int) -> dict:
    def status(process: int) -> dict[str, str]:
        return dict(
            line.split(":", 1)
            for line in Path(f"/proc/{process}/status").read_text().splitlines()
        )

    pending = [pid]
    seen = {pid}
    children = 0
    while pending:
        process = pending.pop()
        for thread in Path(f"/proc/{process}/task").glob("*/children"):
            try:
                for child in map(int, thread.read_text().split()):
                    if child not in seen:
                        seen.add(child)
                        if status(child)["State"].strip()[0] != "Z":
                            children += 1
                            pending.append(child)
            except (OSError, KeyError):
                continue
    try:
        rss = int(status(pid)["VmRSS"].split()[0])
    except (OSError, KeyError):
        return {"rss_kib": None, "live_descendants": None}
    return {"rss_kib": rss, "live_descendants": children}


def check_server(
    process: subprocess.Popen, report: dict, run: int | None = None
) -> None:
    alive = process.poll() is None
    report["server_checks"].append({"run": run, "at": timestamp(), "alive": alive})
    if not alive:
        raise SoakError("The server exited unexpectedly.")


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def record_work(row: dict, events: list[dict]) -> None:
    telemetry = {
        entry["id"]: entry
        for event in events
        for entry in event["payload"].get("telemetry", [])
        if "id" in entry
    }.values()
    tools = [
        {**entry, "started_at": entry["execution_started_at"]}
        for entry in telemetry
        if entry["kind"] == "tool"
        and entry.get("operation") in OPERATIONS
        and entry.get("executed")
        and entry.get("execution_started_at")
        and entry.get("finished_at")
    ]
    row.update(
        scanner_wall_seconds=interval_union(tools) if tools else None,
        tools_completed=sorted(
            {entry["operation"] for entry in tools if entry["completed"]}
        ),
        remediation_observed=any(
            entry["kind"] == "llm"
            and entry.get("role") == "fixer"
            and entry.get("phase") == "security"
            for entry in telemetry
        ),
        verification_observed=any(
            entry["kind"] == "verification" for entry in telemetry
        ),
    )


async def submit(
    client: httpx.AsyncClient, prompt: str, row: dict, redact: Callable[[str], str]
) -> None:
    # Retry only confirmed capacity responses, which do not create a run.
    for _ in range(10):
        response = await client.post(
            "/api/pipeline/run",
            json={"text": prompt, "config": {"provider": "stub"}},
        )
        row["submit_http_status"] = response.status_code
        if response.status_code != 429:
            break
        await asyncio.sleep(0.1)
    if response.status_code == 202:
        row["run_id"] = str(UUID(response.json()["run_id"]))
        return
    try:
        body = response.json()
    except ValueError:
        body = None
    code = (body.get("code") or body.get("error")) if isinstance(body, dict) else None
    row["submit_error_code"] = redact(code) if isinstance(code, str) else None
    suffix = f" ({row['submit_error_code']})" if row["submit_error_code"] else ""
    raise SoakError(
        f"Pipeline submission returned HTTP {response.status_code}{suffix}."
    )


async def observe(
    client: httpx.AsyncClient, prompt: str, row: dict, redact: Callable[[str], str]
) -> None:
    events = []
    try:
        await submit(client, prompt, row, redact)
        url = f"/api/pipeline/{row['run_id']}"
        cursor = 0
        async with asyncio.timeout(1800):
            while True:
                try:
                    async with client.stream(
                        "GET",
                        url + "/stream",
                        headers={"Last-Event-ID": str(cursor)} if cursor else {},
                    ) as stream:
                        stream.raise_for_status()
                        data = []
                        async for line in stream.aiter_lines():
                            if line.startswith("data:"):
                                data.append(line[5:].lstrip(" "))
                            elif not line and data:
                                event = json.loads("\n".join(data))
                                data = []
                                if event["seq"] <= cursor:
                                    continue
                                cursor = event["seq"]
                                events.append(event)
                                if (
                                    row["cancel_requested"]
                                    and not row["cancel_attempted"]
                                    and event["kind"] == "package_status"
                                    and event["status"] == "scanning"
                                    and event["message"] == "security scan started"
                                ):
                                    row["cancel_attempted"] = True
                                    cancel = await client.post(
                                        url + "/cancel",
                                        json={"reviewer_name": "soak"},
                                    )
                                    row["cancel_http_status"] = cancel.status_code
                    snapshot = await client.get(url + "/results")
                    snapshot.raise_for_status()
                    result = snapshot.json()
                    if result["run"]["status"] in TERMINAL_RUNS:
                        row["status"] = result["run"]["status"]
                        statuses = {
                            pkg["variant"]: pkg["status"] for pkg in result["packages"]
                        }
                        statuses.update(
                            (item["variant"], PackageStatus.FAILED.value)
                            for item in result["missing_variants"]
                        )
                        row["package_statuses"] = statuses
                        row["cancelled"] = row["status"] == "cancelled"
                        return
                except httpx.TransportError:
                    pass
                await asyncio.sleep(0.25)
    finally:
        row["ended_at"] = timestamp()
        record_work(row, events)


def soak_client(
    base_url: str,
    api_key: str,
    concurrency: int,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"X-API-Key": api_key},
        trust_env=False,
        timeout=httpx.Timeout(45, connect=2),
        limits=httpx.Limits(max_connections=2 * concurrency + 4),
        transport=transport,
    )


async def drive(
    process: subprocess.Popen,
    client: httpx.AsyncClient,
    report: dict,
    path: Path,
    redact: Callable[[str], str],
) -> None:
    from scripts.benchmark import prompts

    params = report["parameters"]
    frozen = prompts()
    schedule = iter(range(1, params["runs"] + 1))

    async def watch() -> None:
        while process.poll() is None:
            await asyncio.sleep(0.2)
        check_server(process, report)

    async with client:

        async def worker() -> None:
            for number in schedule:
                if process.poll() is not None:
                    check_server(process, report)
                index = (number - 1) % len(frozen)
                row = dict(
                    number=number,
                    run_id=None,
                    prompt_id=index + 1,
                    started_at=timestamp(),
                    ended_at=None,
                    status=None,
                    package_statuses={},
                    cancelled=None,
                    submit_http_status=None,
                    submit_error_code=None,
                    cancel_requested=should_cancel(number, params["cancel_every"]),
                    cancel_attempted=False,
                    cancel_http_status=None,
                    scanner_wall_seconds=None,
                )
                report["runs"].append(row)
                await observe(client, frozen[index], row, redact)
                check_server(process, report, number)
                report["resources"].append(
                    {"run": number, "at": timestamp(), **live_resources(process.pid)}
                )
                write_json(path, report)

        async def workload() -> None:
            async with asyncio.timeout(120):
                while True:
                    try:
                        health = await client.get("/api/health")
                        if health.status_code == 200:
                            break
                    except httpx.TransportError:
                        pass
                    await asyncio.sleep(0.25)
            check_server(process, report)
            async with asyncio.TaskGroup() as group:
                for _ in range(min(params["runs"], params["concurrency"])):
                    group.create_task(worker())

        tasks = {asyncio.create_task(watch()), asyncio.create_task(workload())}
        try:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


def discover_core(pattern: str, pid: int, started: float) -> str | None:
    if not pattern or pattern.startswith("|"):
        return None
    # Linux resolves relative patterns against the crashing process's cwd.
    candidate = Path(pattern)
    if not candidate.is_absolute():
        candidate = BACKEND / candidate
    wildcard = re.sub(r"%[pP]", str(pid), glob.escape(str(candidate)))
    wildcard = re.sub(r"%[a-zA-Z]", "*", wildcard).replace("%%", "%")
    uses_pid = Path("/proc/sys/kernel/core_uses_pid").read_text().strip() == "1"
    if uses_pid and "%p" not in pattern:
        wildcard += f".{pid}"
    for name in glob.iglob(wildcard):
        core = Path(name)
        try:
            if core.is_file() and core.stat().st_mtime >= started:
                return str(core)
        except OSError:
            continue
    return None


def collect_exit(
    process: subprocess.Popen,
    report: dict,
    directory: Path,
    stderr,
    started: float,
    redact: Callable[[str], str],
) -> None:
    code = process.poll()
    assert code is not None
    report.update(
        return_code=code,
        exit_signal=-code if code < 0 else None,
        native_abort=code == -signal.SIGABRT,
    )
    fault_log = fault_log_path(process.pid)
    if fault_log.is_file():
        (directory / fault_log.name).write_text(
            redact(fault_log.read_text(errors="replace"))
        )
        report["evidence"]["faulthandler"] = fault_log.name
    stderr.seek(0)
    tail = directory / "server-stderr-tail.log"
    tail.write_text(
        redact(b"".join(deque(stderr, maxlen=200)).decode(errors="replace"))
    )
    report["evidence"]["stderr"] = tail.name
    report["evidence"]["core_file"] = discover_core(
        report["environment"]["core_pattern"], process.pid, started
    )


def summarize(report: dict, directory: Path) -> None:
    params = report["parameters"]
    settled = sum(row["status"] in TERMINAL_RUNS for row in report["runs"])
    for metric in ("rss_kib", "live_descendants"):
        values = [
            sample[metric]
            for sample in report["resources"]
            if sample[metric] is not None
        ]
        report["resource_summary"][metric] = {
            "peak": max(values, default=None),
            "final": values[-1] if values else None,
            "monotonic_growth": bool(
                values and values[-1] > values[0] and values == sorted(values)
            ),
        }
    if report["error"]:
        message = f"Soak stopped after {settled} settled runs. {report['error']}"
    else:
        message = (
            f"not reproduced in {settled} runs "
            f"(concurrency {params['concurrency']}, stub provider), "
            f"with faulthandler and malloc checking {params['malloc_check']}"
        )
    write_json(directory / "report.json", report)
    (directory / "README.md").write_text(
        "<!-- AI assistance: written with OpenAI Codex from the author's task\n"
        "descriptions; reviewed and modified by the author. See AI_USE.md. -->\n\n"
        f"# Native soak\n\n{message}\n\n"
        "Stub runs omit real provider network and TLS activity.\n"
        "See [report.json](report.json) for run outcomes and process measurements.\n"
    )


def validate_outcomes(report: dict) -> None:
    for row in report["runs"]:
        if row["cancel_requested"]:
            if row["cancel_http_status"] != 202 or not row["cancelled"]:
                raise SoakError(
                    f"Run {row['number']} did not settle after scan-stage cancellation."
                )
        elif (
            row["status"] not in {"success", "partial_success"}
            or set(row["tools_completed"]) != OPERATIONS
            or not row["remediation_observed"]
            or not row["verification_observed"]
        ):
            raise SoakError(
                f"Run {row['number']} did not confirm scanner and remediation coverage."
            )


def run(
    args: argparse.Namespace,
    directory: Path,
    report: dict,
    api_key: str,
    redact: Callable[[str], str],
) -> None:
    env = environment(args.concurrency)
    server_env, mode = allocator_environment(env, args.malloc_check)
    report["environment"].update(
        scanners=verify_scanners(),
        malloc_check_mode=mode,
        malloc_debug_preload=server_env.get("LD_PRELOAD"),
    )
    owner_url = env["TEST_MIGRATION_DATABASE_URL"]
    asyncio.run(require_idle_database(owner_url))
    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "-x", "database=test", "upgrade", "head"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        timeout=120,
        check=False,
    )
    if migration.returncode:
        raise SoakError("Test database migration failed.")
    asyncio.run(require_idle_database(owner_url))

    server_env["API_KEY"] = api_key
    with tempfile.TemporaryFile() as stderr, socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        started = time.time()
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "scripts.soak_native_server",
                str(listener.fileno()),
            ],
            cwd=BACKEND,
            env=server_env,
            stdout=subprocess.DEVNULL,
            stderr=stderr,
            preexec_fn=allow_cores,
            pass_fds=(listener.fileno(),),
            start_new_session=True,
        )
        listener.close()
        report["server_pid"] = process.pid
        try:
            asyncio.run(
                drive(
                    process,
                    soak_client(f"http://127.0.0.1:{port}", api_key, args.concurrency),
                    report,
                    directory / "report.json",
                    redact,
                )
            )
            validate_outcomes(report)
        finally:
            code = process.poll()
            unexpected_exit = code is not None
            if not unexpected_exit:
                process.terminate()
                try:
                    code = process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise SoakError(
                        "The server did not shut down within 20 seconds."
                    ) from None
                unexpected_exit = code not in (0, -signal.SIGTERM)
            if unexpected_exit:
                if not report["server_checks"] or report["server_checks"][-1]["alive"]:
                    report["server_checks"].append(
                        {"run": None, "at": timestamp(), "alive": False}
                    )
                collect_exit(process, report, directory, stderr, started, redact)
                raise SoakError("The server exited unexpectedly.")


def main() -> None:
    args = arguments()
    api_key = secrets.token_urlsafe(32)
    redact = error_redactor(api_key)
    directory = OUTPUT / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    directory.mkdir(parents=True)
    report = {
        "environment": {
            **native_versions(),
            "cpu_count": os.cpu_count(),
            "core_pattern": Path("/proc/sys/kernel/core_pattern").read_text().strip(),
        },
        "parameters": {**vars(args), "provider": "stub"},
        "runs": [],
        "server_checks": [],
        "resources": [],
        "resource_summary": {},
        "native_abort": False,
        "return_code": None,
        "exit_signal": None,
        "evidence": {},
        "error": None,
        "error_detail": None,
    }
    try:
        run(args, directory, report, api_key, redact)
    except (Exception, KeyboardInterrupt) as error:
        record_error(report, error, redact)
    finally:
        summarize(report, directory)
        print(directory)
    if report["error"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
