"""Resolve catalogs, credentials and effective run selections once at submission."""

import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.credentials import CredentialMaterial
from app.db.repositories.providers import ProviderRepository
from app.domain.agent_selection import ROLES, AgentChoice, AgentSelection
from app.domain.enums import LLMProvider
from app.domain.model_catalogue import catalogue_id
from app.domain.run_config import RunConfig
from app.llm.catalog import normalize, probe


class ModelSelectionError(ValueError):
    """Only fixed public guidance, never provider/user input."""


class ModelSelectionService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        settings: Settings,
        cache: dict[str, Any],
        client: Any = None,
    ):
        self.sessions, self.settings, self.cache, self.client = (
            sessions,
            settings,
            cache,
            client,
        )

    async def catalog(self, *, refresh: bool = False) -> dict[str, Any]:
        async with self.sessions() as session, session.begin():
            repository = ProviderRepository(session)
            saved = await repository.settings()
            defaults = dict(saved.agent_defaults)
            identity = saved.default_credential_id
            material = await repository.material(identity) if identity else None
            static = [
                item
                for item in saved.static_models
                if item.get("credential_id") == (str(identity) if identity else None)
            ]
        if material is None and self.settings.llm_provider == LLMProvider.STUB:
            return {
                "provider": "stub",
                "credential_id": None,
                "defaults": defaults,
                "models": [
                    {
                        "id": "stub",
                        "name": "Stub (demo)",
                        "context_length": None,
                        "pricing": {},
                        "structured_output": True,
                        "reasoning": False,
                        "thinking_modes": [],
                        "source": "builtin",
                    }
                ],
            }
        if material is None:
            if self.settings.llm_api_key is None:
                return {
                    "provider": str(self.settings.llm_provider),
                    "credential_id": None,
                    "defaults": defaults,
                    "models": [],
                    "status": "setup_required",
                }
            provider = (
                "anthropic"
                if self.settings.llm_provider == LLMProvider.ANTHROPIC
                else "openrouter"
                if "openrouter.ai" in (self.settings.llm_base_url or "")
                else "openai"
            )
            material = CredentialMaterial(
                provider,
                "messages" if provider == "anthropic" else "chat_completions",
                self.settings.llm_base_url
                or (
                    "https://api.anthropic.com/v1"
                    if provider == "anthropic"
                    else "https://api.openai.com/v1"
                ),
                self.settings.llm_api_key,
            )
        key = str(identity or "environment") + ":" + str(static)
        cached = self.cache.get(key)
        if not refresh and cached and cached[0] > time.monotonic():
            result = cached[1]
        elif static:
            result = {
                "status": "offline",
                "models": [normalize(item, material.provider) for item in static],
            }
        else:
            result = await probe(material, self.client)
            if result["status"] == "ok":
                self.cache[key] = (time.monotonic() + 300, result)
            else:
                self.cache.pop(key, None)
        return {
            **result,
            "provider": material.provider,
            "credential_id": str(identity) if identity else None,
            "defaults": defaults,
        }

    async def resolve(
        self,
        config: RunConfig,
        *,
        interactive: bool,
        personal: dict[str, Any] | None = None,
    ) -> RunConfig:
        # Legacy requests never query provider metadata or inherit browser settings.
        use_catalog = interactive or bool(config.agent_models)
        catalog = await self.catalog() if use_catalog else None
        if set(config.agent_models) - {*ROLES, "generators"}:
            raise ModelSelectionError("Unknown agent role.")
        choices = {
            **(catalog or {}).get("defaults", {}),
            **(personal or {}),
            **{k: v.model_dump() for k, v in config.agent_models.items()},
        }
        if catalog is not None and catalog.get("credential_id"):
            provider = (
                LLMProvider.ANTHROPIC
                if catalog["provider"] == "anthropic"
                else LLMProvider.OPENAI
            )
            model = (
                (choices.get("architect") or {}).get("model")
                or config.model
                or self.settings.llm_model
            )
            if not model:
                raise ModelSelectionError(
                    "Select models in Settings before submitting."
                )
            config = config.model_copy(update={"provider": provider, "model": model})
        resolved = config.resolve(self.settings)
        selections = {}
        for role in ROLES:
            provider, model = resolved.provider, resolved.model
            effort = self.settings.llm_reasoning_effort
            if (
                role == "fixer"
                and provider != LLMProvider.STUB
                and provider == self.settings.llm_provider
            ):
                provider = self.settings.security_fix_provider or provider
                model = self.settings.security_fix_model or model
                effort = self.settings.security_fix_reasoning_effort or effort
            chosen = choices.get(
                role,
                choices.get("generators") if role.startswith("generator_") else None,
            )
            inherited = chosen is None
            if not chosen and catalog and catalog.get("credential_id"):
                chosen = {"model": model or resolved.model, "thinking_mode": effort}
            if chosen:
                choice = AgentChoice.model_validate(chosen)
                item = (
                    next(
                        (
                            m
                            for m in catalog["models"]
                            if m["id"]
                            == catalogue_id(catalog["provider"], choice.model)
                        ),
                        None,
                    )
                    or next(
                        (m for m in catalog["models"] if m["id"] == choice.model), None
                    )
                    if catalog
                    else None
                )
                if (
                    interactive
                    and inherited
                    and (item is None or item["structured_output"] is None)
                ):
                    # An unprobed environment fallback is the known-good legacy
                    # configuration, not a user claim of model capabilities.
                    selections[role] = AgentSelection(
                        model=choice.model,
                        provider=provider,
                        thinking_mode=effort
                        if provider != LLMProvider.ANTHROPIC
                        else None,
                        configured_thinking=effort,
                    )
                    continue
                if item is None or (
                    (role.startswith("generator_") or role == "fixer")
                    and item["structured_output"] is not True
                ):
                    raise ModelSelectionError(
                        "Choose a structured-output model for Generators and Fixer."
                    )
                if (
                    choice.thinking_mode is not None
                    and choice.thinking_mode != "off"
                    and choice.thinking_mode not in item["thinking_modes"]
                ):
                    raise ModelSelectionError("Choose a supported thinking mode.")
                if (
                    choice.thinking_mode == "off"
                    and item.get("reasoning") is True
                    and "off" not in item["thinking_modes"]
                ):
                    raise ModelSelectionError("This model cannot disable reasoning.")
                assert catalog is not None
                selections[role] = AgentSelection(
                    model=choice.model,
                    provider=resolved.provider,
                    thinking_mode=choice.thinking_mode,
                    configured_thinking=choice.thinking_mode,
                    request_style="anthropic"
                    if catalog["provider"] == "anthropic"
                    else "openrouter"
                    if catalog["provider"] == "openrouter"
                    else "openai",
                    reasoning_capable=item.get("reasoning") is True,
                    thinking_types=item.get("thinking_types", {}),
                )
            else:
                selections[role] = AgentSelection(
                    model=model or "unconfigured",
                    provider=provider,
                    thinking_mode=effort if provider != LLMProvider.ANTHROPIC else None,
                    configured_thinking=effort,
                )
        return config.model_copy(
            update={
                "resolved_agents": selections,
                "credential_id": UUID(catalog["credential_id"])
                if catalog and catalog.get("credential_id")
                else None,
            }
        )
