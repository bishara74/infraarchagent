"""Offline atomic rotation. Stop the backend; supply both keys via environment."""

import asyncio
import os

from app.core.config import get_settings
from app.core.credentials import CredentialError, CredentialVault
from app.db.repositories.providers import ProviderRepository
from app.db.session import make_app_engine, make_session_factory


async def rotate() -> None:
    engine = make_app_engine(get_settings())
    try:
        new_key = os.environ.get("CREDENTIAL_ENCRYPTION_NEW_KEY")
        if not new_key:
            raise CredentialError()
        async with make_session_factory(engine)() as session, session.begin():
            count = await ProviderRepository(session).rotate(
                CredentialVault(),
                CredentialVault(new_key),
                int(os.environ["CREDENTIAL_ENCRYPTION_NEW_VERSION"]),
            )
        print(
            f"Rotated {count} encrypted credentials. "
            "Restart with the new key and version."
        )
    finally:
        await engine.dispose()


def main() -> None:
    try:
        asyncio.run(rotate())
    except (ValueError, KeyError, OSError):
        raise SystemExit(
            "Rotation failed. Check master keys, versions and database; "
            "no partial rotation was committed."
        ) from None


if __name__ == "__main__":
    main()
