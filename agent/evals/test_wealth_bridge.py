"""
Tests for wealth_bridge.py, property_tracker.py (full CRUD), and teleport_api.py.

Tests:
  1.  test_down_payment_austin_portfolio_94k
        portfolio_value = 94000 → can_afford_full is True for at least one market
  2.  test_down_payment_small_portfolio
        portfolio_value = 20000 → can_afford_safe is False for all markets
  3.  test_job_offer_seattle_not_real_raise
        $120k Austin → $180k Seattle = NOT a real raise
  4.  test_job_offer_sf_genuine_raise
        $80k Austin → $250k SF = IS a real raise
  5.  test_job_offer_global_city_london
        Any two-city comparison returns expected fields
  6.  test_property_crud_full_cycle
        CREATE → READ → UPDATE → DELETE
  7.  test_net_worth_combines_portfolio_and_property
        equity + portfolio = expected total
  8.  test_teleport_fallback_works_when_api_unavailable
        get_city_housing_data("seattle") returns usable data
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import pytest


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _set_flag(value: str):
    os.environ["ENABLE_REAL_ESTATE"] = value


def _clear_flag():
    os.environ.pop("ENABLE_REAL_ESTATE", None)


# Use an in-memory SQLite for property tracker tests (no file side effects)
os.environ["PROPERTIES_DB_PATH"] = ":memory:"


# ---------------------------------------------------------------------------
# Test 1 — down payment power with $94k portfolio
# ---------------------------------------------------------------------------

def test_down_payment_austin_portfolio_94k():
    """
    GIVEN  portfolio_value = 94000 (sufficient for Caldwell County at $237,491)
    WHEN   calculate_down_payment_power is called with no target_cities
    THEN   at least one market shows can_afford_full = True
           and portfolio_value is preserved in the result
    """
    from tools.wealth_bridge import calculate_down_payment_power

    result = calculate_down_payment_power(94_000)

    assert result["portfolio_value"] == 94_000
    assert "markets" in result
    assert len(result["markets"]) > 0

    # Caldwell County median = $237,491 → 20% down = $47,498 → $94k covers it
    affordable_full = [m for m in result["markets"] if m["can_afford_full"]]
    assert len(affordable_full) > 0, (
        f"Expected at least one market with can_afford_full=True at $94k. "
        f"Markets: {[(m['area'], m['required_down_20pct']) for m in result['markets']]}"
    )

    # Verify key output fields present
    first_market = result["markets"][0]
    assert "median_price" in first_market
    assert "required_down_20pct" in first_market
    assert "monthly_payment_estimate" in first_market
    assert "rent_vs_buy_verdict" in first_market

    # Down payment scenarios
    assert result["down_payment_scenarios"]["full"] == 94_000
    assert result["down_payment_scenarios"]["conservative"] == pytest.approx(75_200)
    assert result["down_payment_scenarios"]["safe"] == pytest.approx(56_400)


# ---------------------------------------------------------------------------
# Test 2 — small portfolio ($20k) cannot afford safe 20% down anywhere
# ---------------------------------------------------------------------------

def test_down_payment_small_portfolio():
    """
    GIVEN  portfolio_value = 20000 (insufficient for 20% down on any Austin market)
    WHEN   calculate_down_payment_power is called
    THEN   can_afford_safe is False for all markets
    """
    from tools.wealth_bridge import calculate_down_payment_power

    result = calculate_down_payment_power(20_000)

    assert result["portfolio_value"] == 20_000

    # safe = 20000 * 0.60 = 12000; cheapest market Caldwell = $237,491 → need $47,498
    # So all markets should have can_afford_safe = False
    safe_affordable = [m for m in result["markets"] if m["can_afford_safe"]]
    assert len(safe_affordable) == 0, (
        f"Expected no safe-affordable markets at $20k. "
        f"Got: {[(m['area'], m['required_down_20pct']) for m in safe_affordable]}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Seattle $180k offer vs Austin $120k is NOT a real raise
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_job_offer_seattle_not_real_raise():
    """
    GIVEN  current: $120k in Austin (COL index 95.4)
           offer:   $180k in Seattle (COL index 150.2)
    WHEN   calculate_job_offer_affordability is called
    THEN   is_real_raise = False
           real_raise_amount < 0
           breakeven_salary_needed > 180000

    Math: adjusted = 180000 * (95.4 / 150.2) ≈ $114,407
          real_raise = 114,407 - 120,000 = -$5,593
    """
    from tools.wealth_bridge import calculate_job_offer_affordability

    result = await calculate_job_offer_affordability(
        offer_salary=180_000,
        offer_city="Seattle",
        current_salary=120_000,
        current_city="Austin",
    )

    assert result["is_real_raise"] is False, (
        f"Expected Seattle $180k to NOT be a real raise vs Austin $120k. "
        f"Got: adjusted={result['adjusted_offer_in_current_city_terms']}"
    )
    assert result["real_raise_amount"] < 0, "Real raise should be negative"
    assert result["breakeven_salary_needed"] > 180_000, (
        "Breakeven in Seattle should exceed the offer salary"
    )
    assert "verdict" in result
    assert len(result["verdict"]) > 20
    assert "offer_city" in result and result["offer_city"] != ""


# ---------------------------------------------------------------------------
# Test 4 — San Francisco $250k vs Austin $80k IS a genuine raise
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_job_offer_sf_genuine_raise():
    """
    GIVEN  current: $80k in Austin (COL index 95.4)
           offer:   $250k in San Francisco (COL index 178.1)
    WHEN   calculate_job_offer_affordability is called
    THEN   is_real_raise = True
           adjusted_offer_in_current_city_terms > 80000

    Math: adjusted = 250000 * (95.4 / 178.1) ≈ $133,969
          real_raise = 133,969 - 80,000 = +$53,969
    """
    from tools.wealth_bridge import calculate_job_offer_affordability

    result = await calculate_job_offer_affordability(
        offer_salary=250_000,
        offer_city="San Francisco",
        current_salary=80_000,
        current_city="Austin",
    )

    assert result["is_real_raise"] is True, (
        f"Expected SF $250k to be a real raise vs Austin $80k. "
        f"Got: adjusted={result.get('adjusted_offer_in_current_city_terms')}"
    )
    assert result["adjusted_offer_in_current_city_terms"] > 80_000


# ---------------------------------------------------------------------------
# Test 5 — Global city (London) comparison returns expected fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_job_offer_global_city_london():
    """
    GIVEN  any salary offer in London vs Austin
    WHEN   calculate_job_offer_affordability is called
    THEN   result has all required fields and offer_city is non-empty
    """
    from tools.wealth_bridge import calculate_job_offer_affordability

    result = await calculate_job_offer_affordability(
        offer_salary=150_000,
        offer_city="London",
        current_salary=120_000,
        current_city="Austin",
    )

    required_fields = {
        "current_salary", "current_city", "current_col_index",
        "offer_salary", "offer_city", "offer_col_index",
        "adjusted_offer_in_current_city_terms",
        "real_raise_amount", "is_real_raise", "breakeven_salary_needed",
        "verdict", "tax_note", "housing_comparison",
    }
    missing = required_fields - set(result.keys())
    assert not missing, f"Missing fields in job offer result: {missing}"
    assert result["offer_city"] != "", "offer_city must be non-empty"
    assert isinstance(result["is_real_raise"], bool)
    assert result["current_col_index"] > 0
    assert result["offer_col_index"] > 0


# ---------------------------------------------------------------------------
# Test 6 — Property CRUD full cycle (CREATE → READ → UPDATE → DELETE)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_property_crud_full_cycle():
    """
    GIVEN  ENABLE_REAL_ESTATE=true
    WHEN   full CRUD cycle is executed
    THEN   each operation produces correct results:
           CREATE: equity = current_value - mortgage_balance = $130,000
           READ:   property appears in list
           UPDATE: equity recalculates to $140,000 after value bump
           DELETE: property no longer appears in list
    """
    _set_flag("true")
    from tools.property_tracker import (
        add_property, get_properties, update_property,
        remove_property, property_store_clear,
    )
    property_store_clear()

    # CREATE
    prop_result = await add_property(
        address="123 Test St Austin TX",
        purchase_price=400_000,
        current_value=450_000,
        mortgage_balance=320_000,
    )
    assert prop_result["success"] is True, f"add_property failed: {prop_result}"
    prop = prop_result["result"]["property"]
    assert prop["equity"] == pytest.approx(130_000), (
        f"Expected equity=130000, got {prop['equity']}"
    )
    assert "id" in prop
    prop_id = prop["id"]

    # READ
    list_result = await get_properties()
    assert list_result["success"] is True
    ids = [p["id"] for p in list_result["result"]["properties"]]
    assert prop_id in ids, f"Added property ID {prop_id} not found in list: {ids}"

    # UPDATE
    updated = await update_property(prop_id, current_value=460_000)
    assert updated["success"] is True, f"update_property failed: {updated}"
    updated_prop = updated["result"]["property"]
    assert updated_prop["equity"] == pytest.approx(140_000), (
        f"Expected equity=140000 after update, got {updated_prop['equity']}"
    )

    # DELETE (soft)
    removed = await remove_property(prop_id)
    assert removed["success"] is True, f"remove_property failed: {removed}"
    assert removed["result"]["status"] == "removed"

    # Verify gone from active list
    props_after = await get_properties()
    ids_after = [p["id"] for p in props_after["result"]["properties"]]
    assert prop_id not in ids_after, (
        f"Property {prop_id} should be removed but still appears in: {ids_after}"
    )


# ---------------------------------------------------------------------------
# Test 7 — Net worth combines portfolio value and real estate equity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_net_worth_combines_portfolio_and_property():
    """
    GIVEN  one property: current_value=$400k, mortgage=$250k → equity=$150k
    WHEN   get_total_net_worth(portfolio_value=94000) is called
    THEN   real_estate_equity == 150000
           total_net_worth == 244000
           investment_portfolio == 94000
    """
    _set_flag("true")
    from tools.property_tracker import (
        add_property, get_total_net_worth, property_store_clear,
    )
    property_store_clear()

    await add_property(
        address="456 Equity St Austin TX",
        purchase_price=300_000,
        current_value=400_000,
        mortgage_balance=250_000,
    )

    result = await get_total_net_worth(portfolio_value=94_000)
    assert result["success"] is True, f"get_total_net_worth failed: {result}"

    data = result["result"]
    assert data["real_estate_equity"] == pytest.approx(150_000), (
        f"Expected real_estate_equity=150000, got {data['real_estate_equity']}"
    )
    assert data["total_net_worth"] == pytest.approx(244_000), (
        f"Expected total_net_worth=244000, got {data['total_net_worth']}"
    )
    assert data["investment_portfolio"] == pytest.approx(94_000)


# ---------------------------------------------------------------------------
# Test 8 — Teleport fallback works when API is unavailable (or any city name)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_teleport_fallback_works_when_api_unavailable():
    """
    GIVEN  "seattle" is requested from teleport_api
    WHEN   get_city_housing_data("seattle") is called
    THEN   result contains MedianRentMonthly and city is non-empty
           (live API or fallback — either is acceptable)
    """
    from tools.teleport_api import get_city_housing_data

    result = await get_city_housing_data("seattle")

    assert isinstance(result, dict), "Result must be a dict"
    assert result.get("city", "") != "", "city field must be non-empty"

    has_rent = "MedianRentMonthly" in result
    has_price = "median_price" in result or "ListPrice" in result
    assert has_rent or has_price, (
        f"Result must have MedianRentMonthly or median_price. Got keys: {list(result.keys())}"
    )
