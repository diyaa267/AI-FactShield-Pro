"""Provider health and configuration helpers for AI-FactShield Pro."""
from __future__ import annotations

import os
from datetime import datetime, timezone

PROVIDERS = {
    "NewsAPI": "NEWS_API_KEY",
    "GNews": "GNEWS_API_KEY",
    "Google Fact Check": "GOOGLE_FACTCHECK_API_KEY",
}


def provider_config() -> list[dict]:
    rows = []
    for name, env_name in PROVIDERS.items():
        rows.append({
            "provider": name,
            "configured": bool(os.getenv(env_name, "").strip()),
            "environment_variable": env_name,
        })
    rows.extend([
        {"provider": "Google News RSS", "configured": True, "environment_variable": None},
        {"provider": "GDELT", "configured": True, "environment_variable": None},
    ])
    return rows


def system_metadata() -> dict:
    return {
        "service": "AI-FactShield Pro",
        "mode": "live-evidence-verification",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "providers": provider_config(),
        "api_keys_are_server_side": True,
    }
