"""Resolve catalogs, credentials and effective run selections once at submission."""

import time
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.credentials import CredentialMaterial
from app.core.public_catalogue import CatalogueError, load_snapshot, provider_order
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

    async def catalog(
        self, *, refresh: bool = False, environment_only: bool = False
    ) -> dict[str, Any]:
        defaults, identity, material, static = {}, None, None, []
        if (
            environment_only
            and self.settings.llm_provider == LLMProvider.OPENAI
            and urlparse(self.settings.llm_base_url or "").hostname == "openrouter.ai"
        ):
            try:
                snapshot = load_snapshot(self.settings.openrouter_catalogue_snapshot)
            except CatalogueError as error:
                raise ModelSelectionError(str(error)) from None
            return {
                "provider": "openrouter",
                "credential_id": None,
                "defaults": {},
                "models": [
                    normalize(item, "openrouter")
                    for item in snapshot["payload"]["models"]
                ],
            }
        if not environment_only:
            async with self.sessions() as session, session.begin():
                repository = ProviderRepository(session)
                saved = await repository.settings()
                defaults = dict(saved.agent_defaults)
                identity = saved.default_credential_id
                material = await repository.material(identity) if identity else None
                static = [
                    item
                    for item in saved.static_models
                    if item.get("credential_id")
                    == (str(identity) if identity else None)
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
        catalog = (
            await self.catalog(environment_only=not interactive)
            if use_catalog
            else None
        )
        if set(config.agent_models) - {*ROLES, "generators"}:
            raise ModelSelectionError("Unknown agent role.")
        if set(config.provider_preferences) - set(ROLES):
            raise ModelSelectionError("Unknown provider-preference role.")
        # Specific roles beat the generator group *within* each tier only.
        tiers = (
            {k: v.model_dump() for k, v in config.agent_models.items()},
            (personal or {}) if interactive else {},
            (catalog or {}).get("defaults", {}) if interactive else {},
        )
        selected_credential = catalog is not None and bool(catalog.get("credential_id"))
        if selected_credential:
            assert catalog is not None
            base_provider = (
                LLMProvider.ANTHROPIC
                if catalog["provider"] == "anthropic"
                else LLMProvider.OPENAI
            )
            base_model = config.model or self.settings.llm_model
        else:
            resolved = config.resolve(self.settings)
            base_provider, base_model = resolved.provider, resolved.model
        selections = {}
        for role in ROLES:
            provider, model = base_provider, base_model
            effort = self.settings.llm_reasoning_effort
            if (
                role == "fixer"
                and provider != LLMProvider.STUB
                and provider == self.settings.llm_provider
            ):
                provider = self.settings.security_fix_provider or provider
                model = self.settings.security_fix_model or model
                effort = self.settings.security_fix_reasoning_effort or effort
            chosen = None
            for tier in tiers:
                chosen = tier.get(role)
                if chosen is None and role.startswith("generator_"):
                    chosen = tier.get("generators")
                if chosen is not None:
                    break
            inherited = chosen is None
            if inherited and selected_credential:
                if not model:
                    labels = {
                        "architect": "Architect",
                        "generator_cost": "Cost Generator",
                        "generator_performance": "Performance Generator",
                        "generator_security": "Security Generator",
                        "fixer": "Fixer",
                    }
                    raise ModelSelectionError(
                        f"Choose a model for {labels[role]} "
                        "or configure its default in Settings."
                    )
                chosen = {"model": model, "thinking_mode": effort}
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
                    provider=base_provider,
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
        if config.provider_preferences:
            if (
                base_provider != LLMProvider.OPENAI
                or "openrouter.ai"
                != urlparse(self.settings.llm_base_url or "").hostname
                or selected_credential
            ):
                raise ModelSelectionError(
                    "Provider preferences require environment OpenRouter transport."
                )
            try:
                snapshot = load_snapshot(self.settings.openrouter_catalogue_snapshot)
                for role, preference in config.provider_preferences.items():
                    if selections[role].provider != LLMProvider.OPENAI:
                        raise CatalogueError(
                            "Preferred-provider role requires OpenRouter transport."
                        )
                    order = provider_order(snapshot, selections[role].model, preference)
                    selections[role] = selections[role].model_copy(
                        update={"provider_order": order}
                    )
            except CatalogueError as error:
                raise ModelSelectionError(str(error)) from None
        return config.model_copy(
            update={
                # Retain the legacy representative model, only after resolving
                # every role from the independent baseline above.
                **(
                    {"provider": base_provider, "model": selections["architect"].model}
                    if selected_credential
                    else {}
                ),
                "resolved_agents": selections,
                "credential_id": UUID(catalog["credential_id"])
                if catalog and catalog.get("credential_id")
                else None,
            }
        )
