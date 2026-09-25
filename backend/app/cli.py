"""Operational commands for package retention."""

import argparse
import asyncio
from datetime import UTC, datetime

from app.core.config import get_settings
from app.db.repositories.packages import PackageRepository
from app.db.session import make_app_engine, make_session_factory


async def sweep_packages(days: int | None, dry_run: bool) -> int:
    settings = get_settings()
    engine = make_app_engine(settings)
    try:
        async with make_session_factory(engine)() as session:
            async with session.begin():
                return await PackageRepository(session).delete_expired(
                    datetime.now(UTC),
                    days if days is not None else settings.package_retention_days,
                    dry_run,
                )
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    sweep = commands.add_parser("sweep-packages")
    sweep.add_argument("--days", type=int)
    sweep.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.days is not None and args.days < 1:
        parser.error("--days must be at least 1")
    count = asyncio.run(sweep_packages(args.days, args.dry_run))
    action = "would be deleted" if args.dry_run else "deleted"
    print(f"{count} package(s) {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
