import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from relocation_runway import calculate_relocation_runway


def test_runway_seattle_vs_austin():
    result = calculate_relocation_runway(
        current_salary=120000, offer_salary=180000,
        current_city="Austin", destination_city="Seattle",
        portfolio_value=94000
    )
    assert result["destination_monthly"]["monthly_surplus"] is not None
    assert "months_to_6mo_emergency_fund" in result["milestones_if_you_move"]
    assert "verdict" in result
    assert "key_insight" in result
    assert result["scenario"]["offer"]["city"] == "Seattle"


def test_runway_impossible_offer():
    result = calculate_relocation_runway(
        current_salary=120000, offer_salary=40000,
        current_city="Austin", destination_city="San Francisco",
        portfolio_value=94000
    )
    assert result is not None
    assert "destination_monthly" in result
    surplus = result["destination_monthly"]["monthly_surplus"]
    warning = result["destination_monthly"].get("monthly_surplus_warning", False)
    assert surplus <= 0 or warning is True


def test_runway_moving_to_affordable_city():
    result = calculate_relocation_runway(
        current_salary=120000, offer_salary=110000,
        current_city="San Francisco", destination_city="Austin",
        portfolio_value=50000
    )
    assert "verdict" in result
    assert result["destination_monthly"]["housing_cost"] < 3000


def test_runway_global_city():
    result = calculate_relocation_runway(
        current_salary=100000, offer_salary=150000,
        current_city="Austin", destination_city="Berlin",
        portfolio_value=75000
    )
    assert "verdict" in result
    assert result["scenario"]["offer"]["city"] == "Berlin"


def test_runway_returns_comparison():
    result = calculate_relocation_runway(
        current_salary=120000, offer_salary=180000,
        current_city="Austin", destination_city="Denver",
        portfolio_value=94000
    )
    assert "milestones_if_you_move" in result
    assert "milestones_if_you_stay" in result
    assert "months_to_down_payment_20pct" in result["milestones_if_you_move"]
    assert "months_to_down_payment_20pct" in result["milestones_if_you_stay"]
