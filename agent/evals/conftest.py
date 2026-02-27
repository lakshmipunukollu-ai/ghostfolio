"""
pytest conftest for the AgentForge eval suite.

Two responsibilities:
1. Patches teleport_api._fetch_from_teleport to return None immediately,
   bypassing all live HTTP calls. This forces get_city_housing_data to fall
   back to HARDCODED_FALLBACK data instantly. Tests run in <1s total.
2. Ensures pytest-asyncio is configured for STRICT mode (set in pytest.ini).
   All async tests carry @pytest.mark.asyncio (they already do).
"""

import os
import sys

# Make 'agent/' and 'agent/tools/' importable from any working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import pytest


# ---------------------------------------------------------------------------
# Teleport API mock — eliminates all live network calls during tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_teleport_no_network(monkeypatch):
    """
    Patches teleport_api._fetch_from_teleport to return None immediately.
    This forces get_city_housing_data to use HARDCODED_FALLBACK for every
    city, with zero HTTP requests and zero wait time.

    Also patches search_city_slug to return from the in-memory cache only,
    so no DNS/HTTP calls are made during slug resolution.

    autouse=True applies this to every test automatically.
    """
    try:
        import teleport_api

        async def _instant_fetch(city_name: str, slug: str):
            """Skip live API call — triggers fallback path immediately."""
            return None

        async def _cache_only_slug(city_name: str):
            """Return from cache or None — no HTTP search calls."""
            lower = city_name.lower().strip()
            return teleport_api._slug_cache.get(lower)

        monkeypatch.setattr(teleport_api, "_fetch_from_teleport", _instant_fetch)
        monkeypatch.setattr(teleport_api, "search_city_slug", _cache_only_slug)
    except ImportError:
        pass  # teleport_api not importable in this test context — skip
