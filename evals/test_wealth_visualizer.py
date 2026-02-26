import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from wealth_visualizer import analyze_wealth_position


def test_wealth_above_median():
    result = analyze_wealth_position(
        portfolio_value=94000, age=34, annual_income=120000
    )
    assert result["current_position"]["total_net_worth"] == 94000
    assert "above median" in result["current_position"]["you_vs_median"]
    assert result["retirement_projection"]["monthly_income_at_retirement"] > 0
    assert "honest_assessment" in result


def test_wealth_below_median():
    result = analyze_wealth_position(
        portfolio_value=15000, age=45, annual_income=80000
    )
    # 45-54 median is $247k, $15k is well below
    assert result["current_position"]["total_net_worth"] == 15000
    assert result["current_position"]["total_net_worth"] < 247000
    assert "honest_assessment" in result


def test_wealth_includes_real_estate():
    result = analyze_wealth_position(
        portfolio_value=94000, age=40,
        annual_income=150000, real_estate_equity=140000
    )
    assert result["current_position"]["total_net_worth"] == 234000
    assert result["current_position"]["real_estate_equity"] == 140000


def test_early_retirement_scenario():
    result = analyze_wealth_position(
        portfolio_value=500000, age=40,
        annual_income=200000, target_retirement_age=55
    )
    assert result["retirement_projection"]["years_to_retirement"] == 15
    assert len(result["what_if_scenarios"]) >= 2


def test_retirement_math_reasonable():
    result = analyze_wealth_position(
        portfolio_value=100000, age=35,
        annual_income=100000, annual_savings=15000,
        target_retirement_age=65
    )
    projected = result["retirement_projection"]["projected_total_at_retirement"]
    assert projected > 700000
    assert projected < 5000000


def test_savings_grade_low_vs_high():
    result_low = analyze_wealth_position(
        50000, 30, 100000, annual_savings=5000
    )
    result_high = analyze_wealth_position(
        50000, 30, 100000, annual_savings=30000
    )
    low_grade = result_low["savings_analysis"]["savings_grade"]
    high_grade = result_high["savings_analysis"]["savings_grade"]
    assert low_grade in ["critical", "minimum", "low"]
    assert high_grade in ["excellent", "exceptional"]
