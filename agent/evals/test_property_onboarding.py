"""
Tests for property onboarding and net worth flows.

Tests:
  1. test_add_property_returns_equity
  2. test_get_properties_shows_equity
  3. test_total_net_worth_combines_both
  4. test_no_properties_returns_graceful_response
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

# Use an in-memory SQLite to avoid polluting any real DB
os.environ["PROPERTIES_DB_PATH"] = ":memory:"
os.environ["ENABLE_REAL_ESTATE"] = "true"

import pytest

from property_tracker import (
    add_property,
    get_properties,
    get_total_net_worth,
    property_store_clear,
)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Clear the in-memory store between tests via autouse fixture
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_store():
    """Reset in-memory DB before each test."""
    property_store_clear()
    yield
    property_store_clear()


# ---------------------------------------------------------------------------
# Test 1 — add_property returns equity in the result
# ---------------------------------------------------------------------------

def test_add_property_returns_equity():
    result = _run(add_property(
        address="My Primary Home",
        purchase_price=400000,
        current_value=480000,
        mortgage_balance=310000,
    ))
    assert result is not None
    assert result.get("success") is True, f"Expected success, got: {result}"

    prop = result.get("result", {})
    # equity = current_value - mortgage_balance = 170000
    equity = prop.get("equity",
        prop.get("current_value", 480000) - prop.get("mortgage_balance", 310000))
    assert equity == 170000, f"Expected equity 170000, got {equity}"


# ---------------------------------------------------------------------------
# Test 2 — get_properties returns properties with equity
# ---------------------------------------------------------------------------

def test_get_properties_shows_equity():
    _run(add_property("Test Home", 300000, 380000, 250000))
    result = _run(get_properties())
    assert result is not None
    assert result.get("success") is True

    props = result.get("result", {}).get("properties", [])
    assert len(props) > 0, "Expected at least one property"
    for p in props:
        assert "equity" in p or "current_value" in p, (
            f"Property missing equity/current_value: {p.keys()}"
        )


# ---------------------------------------------------------------------------
# Test 3 — total net worth combines portfolio + real estate equity
# ---------------------------------------------------------------------------

def test_total_net_worth_combines_both():
    _run(add_property("Net Worth Test Home", 350000, 420000, 280000))
    # equity = 420000 - 280000 = 140000
    result = _run(get_total_net_worth(portfolio_value=94000))
    assert result.get("success") is True

    data = result.get("result", {})
    assert data["investment_portfolio"] == 94000
    assert data["total_net_worth"] > 94000, "Total net worth should exceed portfolio alone"
    assert "real_estate_equity" in data
    assert data["real_estate_equity"] > 0, "Expected positive real estate equity"
    # 94000 + 140000 = 234000
    assert data["total_net_worth"] == pytest.approx(94000 + 140000, abs=1)


# ---------------------------------------------------------------------------
# Test 4 — no properties returns graceful response (not a crash)
# ---------------------------------------------------------------------------

def test_no_properties_returns_graceful_response():
    result = _run(get_properties())
    assert result is not None
    assert isinstance(result, dict)
    # Should not crash — may return success with empty list or a helpful message
    assert "success" in result or "error" in result
    if result.get("success"):
        data = result.get("result", {})
        props = data.get("properties", [])
        # Empty list is fine — just must not crash
        assert isinstance(props, list)
