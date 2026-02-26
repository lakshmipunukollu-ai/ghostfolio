"""
Unit tests for the Real Estate tool integration.

Tests cover:
  1. Normalization — search_listings returns NormalizedListing schema
  2. Caching — second call returns cached data without re-computing
  3. Integration schema — compare_neighborhoods returns expected structure
  4. Feature flag — all tools return FEATURE_DISABLED when flag is off
  5. Graceful fallback — unknown location returns a helpful error, not a crash
"""

import asyncio
import os
import sys

# Add agent root to path so imports work when running from any directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_flag(value: str):
    os.environ["ENABLE_REAL_ESTATE"] = value


def _clear_flag():
    os.environ.pop("ENABLE_REAL_ESTATE", None)


# ---------------------------------------------------------------------------
# Test 1 — normalization: search_listings returns expected schema
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_listings_schema():
    """
    GIVEN  the real estate feature is enabled
    WHEN   search_listings('Austin') is called
    THEN   the result conforms to the NormalizedListing schema:
           each listing must have id, address, price, bedrooms, sqft,
           days_on_market, cap_rate_estimate.
    """
    _set_flag("true")
    # Import inside test so the env var is already set
    from tools.real_estate import search_listings, cache_clear
    cache_clear()

    result = await search_listings("Austin")

    assert result["success"] is True, f"Expected success, got: {result}"
    assert result["tool_name"] == "real_estate"
    assert "tool_result_id" in result

    listings = result["result"]["listings"]
    assert len(listings) >= 1, "Expected at least 1 listing"

    required_fields = {
        "id", "address", "city", "state", "price", "bedrooms",
        "bathrooms", "sqft", "days_on_market", "cap_rate_estimate",
    }
    for listing in listings:
        missing = required_fields - set(listing.keys())
        assert not missing, f"Listing missing fields: {missing}"
        assert isinstance(listing["price"], (int, float)), "price must be numeric"
        assert listing["price"] > 0, "price must be positive"
        assert isinstance(listing["cap_rate_estimate"], (int, float))


# ---------------------------------------------------------------------------
# Test 2 — caching: repeated call returns cached result
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_neighborhood_snapshot_caching():
    """
    GIVEN  the real estate feature is enabled
    WHEN   get_neighborhood_snapshot('Austin') is called twice
    THEN   the second call returns the same tool_result_id (from cache)
           and does not mutate data.
    """
    _set_flag("true")
    from tools.real_estate import get_neighborhood_snapshot, cache_clear
    cache_clear()

    first = await get_neighborhood_snapshot("Austin")
    second = await get_neighborhood_snapshot("Austin")

    assert first["success"] is True
    assert second["success"] is True

    # Both calls must return same tool_result_id (cache hit)
    assert first["tool_result_id"] == second["tool_result_id"], (
        "Expected same tool_result_id on cache hit"
    )

    # Data must be identical
    assert first["result"]["median_price"] == second["result"]["median_price"]


# ---------------------------------------------------------------------------
# Test 3 — integration schema: compare_neighborhoods returns correct structure
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_compare_neighborhoods_schema():
    """
    GIVEN  the real estate feature is enabled
    WHEN   compare_neighborhoods('Austin', 'Denver') is called
    THEN   the result contains both locations, all metric keys, and summaries.
    """
    _set_flag("true")
    from tools.real_estate import compare_neighborhoods, cache_clear
    cache_clear()

    result = await compare_neighborhoods("Austin", "Denver")

    assert result["success"] is True, f"Expected success, got: {result}"
    comp = result["result"]

    assert "location_a" in comp
    assert "location_b" in comp
    assert "metrics" in comp
    assert "summaries" in comp

    required_metrics = {
        "median_price", "price_per_sqft", "gross_rental_yield_pct",
        "days_on_market", "walk_score",
    }
    for metric in required_metrics:
        assert metric in comp["metrics"], f"Missing metric: {metric}"
        assert "a" in comp["metrics"][metric]
        assert "b" in comp["metrics"][metric]

    # Both summaries must be non-empty strings
    for loc, summary in comp["summaries"].items():
        assert isinstance(summary, str) and len(summary) > 20, (
            f"Summary for {loc} is too short or missing"
        )


# ---------------------------------------------------------------------------
# Test 4 — feature flag: all tools return FEATURE_DISABLED when flag is off
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feature_flag_disabled():
    """
    GIVEN  ENABLE_REAL_ESTATE is not set (or set to false)
    WHEN   any real estate tool is called
    THEN   it returns success=False with error=FEATURE_DISABLED (no crash).
    """
    _set_flag("false")
    from tools.real_estate import (
        search_listings,
        get_neighborhood_snapshot,
        compare_neighborhoods,
        is_real_estate_enabled,
        cache_clear,
    )
    cache_clear()

    assert is_real_estate_enabled() is False

    for coro in [
        search_listings("Austin"),
        get_neighborhood_snapshot("Austin"),
        compare_neighborhoods("Austin", "Denver"),
    ]:
        result = await coro
        assert result["success"] is False
        assert result["error"] == "FEATURE_DISABLED", (
            f"Expected FEATURE_DISABLED, got: {result}"
        )

    # Restore for other tests
    _set_flag("true")


# ---------------------------------------------------------------------------
# Test 5 — graceful fallback: unknown location returns helpful error, no crash
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_location_graceful_error():
    """
    GIVEN  the real estate feature is enabled
    WHEN   search_listings is called with an unsupported location
    THEN   it returns success=False with error=NO_LISTINGS_FOUND and a helpful
           message listing supported cities (no exception raised).
    """
    _set_flag("true")
    from tools.real_estate import search_listings, cache_clear
    cache_clear()

    result = await search_listings("Atlantis")

    assert result["success"] is False
    assert result["error"] == "NO_LISTINGS_FOUND"
    assert "Atlantis" in result["message"]
    # Message must name at least one supported city so user knows what to try
    assert any(city in result["message"].lower() for city in ["austin", "denver", "seattle"])
