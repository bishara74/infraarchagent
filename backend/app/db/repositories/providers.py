"""Provider persistence and atomic credential rotation."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.credentials import CredentialError, CredentialMaterial, CredentialVault
from app.db.models import LLMSettings, ProviderCredential


class ProviderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def settings(self, *, lock: bool = False) -> LLMSettings:
        row = await self.session.get(LLMSettings, 1, with_for_update=lock)
        if row is None:
            row = LLMSettings(id=1, agent_defaults={}, static_models=[])
            self.session.add(row)
            await self.session.flush()
        return row

    async def list(self) -> list[ProviderCredential]:
        return list(
            await self.session.scalars(
                select(ProviderCredential).order_by(ProviderCredential.created_at)
            )
        )

    async def create(
        self,
        provider: str,
        label: str,
        base_url: str,
        protocol: str,
        secret: SecretStr,
        created_by: UUID | None,
    ) -> ProviderCredential:
        import os

        credential_id = uuid4()
        ciphertext, nonce = CredentialVault().encrypt(provider, credential_id, secret)
        row = ProviderCredential(
            id=credential_id,
            provider=provider,
            label=label,
            base_url=base_url,
            api_protocol=protocol,
            credential_type="api_key",
            ciphertext=ciphertext,
            nonce=nonce,
            key_version=int(os.environ.get("CREDENTIAL_ENCRYPTION_KEY_VERSION", "1")),
            last4=secret.get_secret_value()[-4:],
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def material(self, credential_id: UUID) -> CredentialMaterial:
        row = await self.session.get(ProviderCredential, credential_id)
        if row is None or row.revoked_at or row.credential_type != "api_key":
            raise CredentialError()
        secret = CredentialVault().decrypt(
            row.provider, row.id, row.ciphertext, row.nonce
        )
        row.last_used_at = datetime.now(UTC)
        return CredentialMaterial(row.provider, row.api_protocol, row.base_url, secret)

    async def revoke(self, credential_id: UUID) -> None:
        row = await self.session.get(
            ProviderCredential, credential_id, with_for_update=True
        )
        if row:
            row.revoked_at = datetime.now(UTC)

    async def select(self, credential_id: UUID | None) -> None:
        if credential_id:
            await self.material(credential_id)
        (await self.settings(lock=True)).default_credential_id = credential_id

    async def rotate(
        self, old: CredentialVault, new: CredentialVault, version: int
    ) -> int:
        rows = list(
            await self.session.scalars(select(ProviderCredential).with_for_update())
        )
        if any(version <= row.key_version for row in rows):
            raise CredentialError()
        for row in rows:
            secret = old.decrypt(row.provider, row.id, row.ciphertext, row.nonce)
            row.ciphertext, row.nonce = new.encrypt(row.provider, row.id, secret)
            row.key_version = version
        return len(rows)
