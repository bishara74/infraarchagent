"""Unmistakably synthetic public catalogue evidence. Never real model metadata."""

import json
from datetime import UTC, datetime

from app.core.public_catalogue import PUBLIC_BASE, digest

ARCHITECT = "test-only/architect-2099"
BASELINE = "test-only/baseline"
FIXER = "test-only/fixer"


def fake_snapshot(path):
    models = [
        {
            "id": model,
            "name": "FAKE TEST MODEL",
            "created": i,
            "context_length": 12345,
            "pricing": {"prompt": "0.000123", "completion": "0.000456"},
            "supported_parameters": [
                "reasoning",
                "response_format",
                "structured_outputs",
            ],
        }
        for i, model in enumerate((BASELINE, FIXER, ARCHITECT))
    ]
    endpoints = {
        model["id"]: [
            {
                "provider_name": "Test Fast",
                "tag": "test-fast",
                "status": 0,
                "supported_parameters": model["supported_parameters"],
                "pricing": model["pricing"],
                "context_length": 12345,
            },
            {
                "provider_name": "Test Backup",
                "tag": "test-backup",
                "status": 0,
                "supported_parameters": model["supported_parameters"],
                "pricing": model["pricing"],
                "context_length": 12345,
            },
        ]
        for model in models
    }
    payload = {"models": models, "endpoints": endpoints}
    snapshot = {
        "version": 1,
        "source": PUBLIC_BASE,
        "captured_at": datetime.now(UTC).isoformat(),
        "payload": payload,
        "sha256": digest(payload),
    }
    path.write_text(json.dumps(snapshot))
    return snapshot
