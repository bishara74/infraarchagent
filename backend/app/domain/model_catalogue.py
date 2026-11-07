# AI assistance: written with OpenAI Codex from the author's task
# descriptions; reviewed and modified by the author. See AI_USE.md.
"""Metadata routing only: never rewrite the model ID used for inference."""

ROUTING_SUFFIXES = frozenset({"nitro", "floor", "exacto", "online"})


def catalogue_id(provider: str, model_id: str) -> str:
    if provider != "openrouter":
        return model_id
    slug, *suffixes = model_id.split(":")
    return ":".join([slug, *(s for s in suffixes if s not in ROUTING_SUFFIXES)])
