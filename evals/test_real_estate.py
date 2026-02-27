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
        # Error is now a nested dict with {code, message}
        assert isinstance(result["error"], dict), f"Expected dict error, got: {result['error']}"
        assert result["error"]["code"] == "REAL_ESTATE_FEATURE_DISABLED", (
            f"Expected REAL_ESTATE_FEATURE_DISABLED, got: {result}"
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
    # Error is now a nested dict with {code, message}
    assert isinstance(result["error"], dict)
    assert result["error"]["code"] == "REAL_ESTATE_PROVIDER_UNAVAILABLE"
    assert "Atlantis" in result["error"]["message"]
    # Message must name at least one supported city so user knows what to try
    assert any(city in result["error"]["message"].lower() for city in ["austin", "denver", "seattle"])


# ---------------------------------------------------------------------------
# Test 6 — bedroom filter: min_beds=3 returns only 3+ bed listings
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_listings_bedroom_filter():
    """
    GIVEN  the real estate feature is enabled
    WHEN   search_listings('Austin', min_beds=3) is called
    THEN   every returned listing has bedrooms >= 3.
    """
    _set_flag("true")
    from tools.real_estate import search_listings, cache_clear
    cache_clear()

    result = await search_listings("Austin", min_beds=3)

    assert result["success"] is True, f"Expected success, got: {result}"
    listings = result["result"]["listings"]
    assert len(listings) >= 1, "Expected at least 1 listing with 3+ beds in Austin"

    for listing in listings:
        assert listing["bedrooms"] >= 3, (
            f"Listing {listing['id']} has {listing['bedrooms']} beds — should be >= 3"
        )

    # filters_applied must be recorded in the result
    assert result["result"]["filters_applied"].get("min_beds") == 3


# ---------------------------------------------------------------------------
# Test 7 — price filter: max_price excludes listings above threshold
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_listings_price_filter():
    """
    GIVEN  the real estate feature is enabled
    WHEN   search_listings('Austin', max_price=400000) is called
    THEN   every returned listing has price <= 400000.
    """
    _set_flag("true")
    from tools.real_estate import search_listings, cache_clear
    cache_clear()

    max_price = 400_000
    result = await search_listings("Austin", max_price=max_price)

    assert result["success"] is True, f"Expected success, got: {result}"
    listings = result["result"]["listings"]

    for listing in listings:
        assert listing["price"] <= max_price, (
            f"Listing {listing['id']} priced at ${listing['price']:,} "
            f"exceeds max_price ${max_price:,}"
        )

    assert result["result"]["filters_applied"].get("max_price") == max_price


# ---------------------------------------------------------------------------
# Test 8 — structured error code: all errors use nested {code, message} shape
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_structured_error_code():
    """
    GIVEN  the real estate feature is enabled
    WHEN   any function encounters an error condition
    THEN   the error field is a dict with 'code' and 'message' keys
           and the code is one of the expected REAL_ESTATE_* values.
    """
    _set_flag("true")
    from tools.real_estate import (
        get_neighborhood_snapshot,
        search_listings,
        get_listing_details,
        cache_clear,
    )
    cache_clear()

    valid_codes = {
        "REAL_ESTATE_PROVIDER_UNAVAILABLE",
        "REAL_ESTATE_FEATURE_DISABLED",
    }

    # Test 1: unknown location in snapshot
    r1 = await get_neighborhood_snapshot("Atlantis")
    assert r1["success"] is False
    assert isinstance(r1["error"], dict), "error must be a dict"
    assert "code" in r1["error"], "error must have 'code' key"
    assert "message" in r1["error"], "error must have 'message' key"
    assert r1["error"]["code"] in valid_codes

    # Test 2: unknown location in search
    r2 = await search_listings("Atlantis")
    assert r2["success"] is False
    assert isinstance(r2["error"], dict)
    assert r2["error"]["code"] in valid_codes
    assert len(r2["error"]["message"]) > 10, "message must be non-empty"

    # Test 3: unknown listing ID in detail lookup
    r3 = await get_listing_details("xxx-999")
    assert r3["success"] is False
    assert isinstance(r3["error"], dict)
    assert r3["error"]["code"] in valid_codes
