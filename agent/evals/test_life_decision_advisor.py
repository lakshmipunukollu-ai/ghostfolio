import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from life_decision_advisor import analyze_life_decision


def test_job_offer_returns_complete_structure():
    result = analyze_life_decision(
        "job_offer",
        {
            "current_salary": 120000,
            "offer_salary": 180000,
            "current_city": "Austin",
            "destination_city": "Seattle",
            "portfolio_value": 94000,
            "age": 34,
        }
    )
    assert result is not None
    assert isinstance(result, dict)
    assert "financial_verdict" in result
    assert "recommendation" in result
    assert "tradeoffs" in result
    assert isinstance(result["tradeoffs"], list)


def test_home_purchase_decision():
    result = analyze_life_decision(
        "home_purchase",
        {
            "portfolio_value": 94000,
            "current_city": "Austin",
            "age": 34,
            "annual_income": 120000,
        }
    )
    assert result is not None
    assert "recommendation" in result


def test_rent_or_buy_decision():
    result = analyze_life_decision(
        "rent_or_buy",
        {
            "portfolio_value": 94000,
            "current_city": "Austin",
            "annual_income": 120000,
        }
    )
    assert result is not None
    assert "recommendation" in result


def test_minimal_context_does_not_crash():
    result = analyze_life_decision("general", {})
    assert result is not None
    assert isinstance(result, dict)
    has_content = (
        "summary" in result
        or "recommendation" in result
        or "message" in result
    )
    assert has_content


def test_missing_fields_handled_gracefully():
    result = analyze_life_decision(
        "job_offer",
        {"current_salary": 120000, "offer_salary": 180000}
    )
    assert result is not None
    assert isinstance(result, dict)
