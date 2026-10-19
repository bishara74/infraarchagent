"""Versioned encrypted credential material, independent of LLM transports."""

import base64
import json
import os
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pydantic import SecretStr

from app.core.logging import register_secret


class CredentialError(ValueError):
    def __init__(self) -> None:
        super().__init__(
            "Credential unavailable. Configure the encryption key "
            "or select an active provider."
        )


@dataclass(frozen=True, repr=False)
class CredentialMaterial:
    provider: str
    api_protocol: str
    base_url: str
    secret: SecretStr
    credential_type: Literal["api_key"] = "api_key"


class CredentialVault:
    def __init__(self, key: str | None = None):
        try:
            encoded = (
                key
                if key is not None
                else os.environ.get("CREDENTIAL_ENCRYPTION_KEY", "")
            )
            material = base64.b64decode(encoded, validate=True)
            if len(material) != 32:
                raise ValueError
            self.cipher = AESGCM(material)
            register_secret(encoded)
        except (ValueError, TypeError):
            raise CredentialError() from None

    def encrypt(
        self, provider: str, credential_id: UUID, secret: SecretStr
    ) -> tuple[bytes, bytes]:
        register_secret(secret.get_secret_value())
        nonce = os.urandom(12)
        envelope = json.dumps(
            {"version": 1, "api_key": secret.get_secret_value()}
        ).encode()
        return self.cipher.encrypt(
            nonce, envelope, f"{provider}:{credential_id}".encode()
        ), nonce

    def decrypt(
        self, provider: str, credential_id: UUID, ciphertext: bytes, nonce: bytes
    ) -> SecretStr:
        try:
            envelope = json.loads(
                self.cipher.decrypt(
                    nonce, ciphertext, f"{provider}:{credential_id}".encode()
                )
            )
            if envelope["version"] != 1 or not isinstance(envelope["api_key"], str):
                raise ValueError
            secret = SecretStr(envelope["api_key"])
            register_secret(secret.get_secret_value())
            return secret
        except (InvalidTag, ValueError, KeyError, TypeError):
            raise CredentialError() from None
