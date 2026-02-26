import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from property_tracker import add_property, get_properties, analyze_equity_options

os.environ["ENABLE_REAL_ESTATE"] = "true"


def _add(address, purchase_price, current_value, mortgage_balance):
    """Helper: run async add_property and return the property dict."""
    result = asyncio.run(add_property(
        address=address,
        purchase_price=purchase_price,
        current_value=current_value,
        mortgage_balance=mortgage_balance,
    ))
    return result["result"]["property"]


def test_equity_three_options_returned():
    prop = _add(
        address="123 Equity Test St Austin TX",
        purchase_price=400000,
        current_value=520000,
        mortgage_balance=380000,
    )
    result = analyze_equity_options(prop["id"])
    assert "options" in result
    assert "leave_untouched" in result["options"]
    assert "cash_out_invest" in result["options"]
    assert "rental_property" in result["options"]
    assert result["current_equity"] == 140000
    assert result["accessible_equity"] == 112000


def test_equity_math_correct():
    prop = _add("Math Test Property", 300000, 450000, 200000)
    result = analyze_equity_options(prop["id"])
    assert result["current_equity"] == 250000
    assert result["accessible_equity"] == 200000


def test_equity_recommendation_exists():
    prop = _add("Rec Test", 350000, 480000, 320000)
    result = analyze_equity_options(prop["id"])
    assert "recommendation" in result
    assert len(result["recommendation"]) > 20
    assert "disclaimer" in result


def test_equity_bad_property_id():
    result = analyze_equity_options("nonexistent-id-99999")
    assert result is not None
    assert "error" in result
