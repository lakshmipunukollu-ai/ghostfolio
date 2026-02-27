"""
Tests for realestate_strategy.py — simulate_real_estate_strategy()

Tests:
  1. test_basic_strategy_returns_expected_shape
  2. test_user_provided_appreciation_overrides_default
  3. test_conservative_preset_lower_than_optimistic
  4. test_disclaimer_and_how_to_adjust_present
  5. test_timeline_length_matches_total_years
  6. test_single_property_no_rentals
  7. test_net_worth_grows_over_time
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import pytest
from realestate_strategy import simulate_real_estate_strategy


# ---------------------------------------------------------------------------
# Test 1 — basic shape
# ---------------------------------------------------------------------------

def test_basic_strategy_returns_expected_shape():
    result = simulate_real_estate_strategy(
        initial_portfolio_value=94000,
        annual_income=120000,
        first_home_price=400000,
        total_years=10,
    )
    assert "strategy" in result
    assert "timeline" in result
    assert "final_picture" in result
    assert "disclaimer" in result
    assert "how_to_adjust" in result

    fp = result["final_picture"]
    assert "total_net_worth" in fp
    assert "total_real_estate_equity" in fp
    assert "investment_portfolio" in fp
    assert fp["total_net_worth"] > 0


# ---------------------------------------------------------------------------
# Test 2 — user-provided appreciation overrides default
# ---------------------------------------------------------------------------

def test_user_provided_appreciation_overrides_default():
    result_default = simulate_real_estate_strategy(
        94000, 120000, 400000, total_years=10
    )
    result_custom = simulate_real_estate_strategy(
        94000, 120000, 400000, total_years=10,
        annual_appreciation=0.02  # conservative
    )
    default_equity = result_default["final_picture"]["total_real_estate_equity"]
    custom_equity = result_custom["final_picture"]["total_real_estate_equity"]
    # Lower appreciation → lower real estate equity
    assert custom_equity < default_equity


# ---------------------------------------------------------------------------
# Test 3 — conservative numbers produce lower net worth than optimistic
# ---------------------------------------------------------------------------

def test_conservative_preset_lower_than_optimistic():
    result_conservative = simulate_real_estate_strategy(
        94000, 120000, 400000, total_years=10,
        annual_appreciation=0.02,
        annual_rent_yield=0.06,
        annual_market_return=0.05,
    )
    result_optimistic = simulate_real_estate_strategy(
        94000, 120000, 400000, total_years=10,
        annual_appreciation=0.06,
        annual_rent_yield=0.10,
        annual_market_return=0.09,
    )
    assert (
        result_optimistic["final_picture"]["total_net_worth"]
        > result_conservative["final_picture"]["total_net_worth"]
    )


# ---------------------------------------------------------------------------
# Test 4 — disclaimer and how_to_adjust fields present
# ---------------------------------------------------------------------------

def test_disclaimer_and_how_to_adjust_present():
    result = simulate_real_estate_strategy(
        94000, 120000, 400000
    )
    assert "disclaimer" in result
    assert "how_to_adjust" in result
    assert "assumptions" in result["strategy"]
    assert "note" in result["strategy"]["assumptions"]
    # Disclaimer should mention "planning tool" or "prediction"
    assert "planning tool" in result["disclaimer"] or "prediction" in result["disclaimer"]


# ---------------------------------------------------------------------------
# Test 5 — timeline length matches total_years
# ---------------------------------------------------------------------------

def test_timeline_length_matches_total_years():
    result = simulate_real_estate_strategy(
        94000, 120000, 400000, total_years=5
    )
    # Timeline includes year 0 through year 5 → 6 entries
    assert len(result["timeline"]) == 6
    assert result["timeline"][0]["year"] == 0
    assert result["timeline"][-1]["year"] == 5


# ---------------------------------------------------------------------------
# Test 6 — buy_interval > total_years means only one property purchased
# ---------------------------------------------------------------------------

def test_single_property_no_rentals():
    result = simulate_real_estate_strategy(
        94000, 120000, 400000,
        buy_interval_years=20,  # longer than simulation
        total_years=10,
    )
    fp = result["final_picture"]
    # Should have exactly 1 property (never triggers next buy)
    assert fp["num_properties_owned"] == 1
    # No rental income since only one property (primary home, not rented)
    assert fp["annual_rental_income"] == 0


# ---------------------------------------------------------------------------
# Test 7 — net worth generally grows over time
# ---------------------------------------------------------------------------

def test_net_worth_grows_over_time():
    result = simulate_real_estate_strategy(
        94000, 120000, 400000, total_years=10
    )
    timeline = result["timeline"]
    # Net worth at year 10 should be higher than year 0
    assert timeline[-1]["total_net_worth"] > timeline[0]["total_net_worth"]
