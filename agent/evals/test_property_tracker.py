"""
Unit tests for the Property Tracker tool.

Tests cover:
  1. add_property schema — result contains required fields
  2. Equity computed correctly — equity = current_value - mortgage_balance
  3. Appreciation computed correctly — appreciation = current_value - purchase_price
  4. list_properties empty — returns success with empty list and zero summary
  5. list_properties with data — summary totals are mathematically correct
  6. get_real_estate_equity — returns correct totals across multiple properties
  7. Feature flag disabled — all tools return FEATURE_DISABLED
  8. remove_property — removes the correct entry
  9. remove_property not found — returns structured error, no crash
  10. add_property validation — empty address returns structured error
  11. add_property validation — zero purchase price returns structured error
  12. No mortgage — equity equals full current value when mortgage_balance=0
  13. current_value defaults to purchase_price when not supplied
"""

import asyncio
import os
import sys

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


_SAMPLE_ADDRESS = "123 Barton Hills Dr, Austin, TX 78704"
_SAMPLE_PURCHASE = 450_000.0
_SAMPLE_VALUE = 522_500.0
_SAMPLE_MORTGAGE = 380_000.0


# ---------------------------------------------------------------------------
# Test 1 — add_property schema
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_property_schema():
    """
    GIVEN  the feature is enabled
    WHEN   add_property is called with valid inputs
    THEN   the result has success=True, a tool_result_id, and a property dict
           with all required fields.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, property_store_clear
    property_store_clear()

    result = await add_property(
        address=_SAMPLE_ADDRESS,
        purchase_price=_SAMPLE_PURCHASE,
        current_value=_SAMPLE_VALUE,
        mortgage_balance=_SAMPLE_MORTGAGE,
    )

    assert result["success"] is True
    assert result["tool_name"] == "property_tracker"
    assert "tool_result_id" in result

    prop = result["result"]["property"]
    required_fields = {
        "id", "address", "property_type", "purchase_price",
        "current_value", "mortgage_balance", "equity", "equity_pct",
        "appreciation", "appreciation_pct", "county_key", "added_at",
    }
    missing = required_fields - set(prop.keys())
    assert not missing, f"Property missing fields: {missing}"
    assert prop["address"] == _SAMPLE_ADDRESS


# ---------------------------------------------------------------------------
# Test 2 — equity computed correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_equity_computed():
    """
    GIVEN  current_value=522500 and mortgage_balance=380000
    WHEN   add_property is called
    THEN   equity == 142500 and equity_pct ≈ 27.27%.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, property_store_clear
    property_store_clear()

    result = await add_property(
        address=_SAMPLE_ADDRESS,
        purchase_price=_SAMPLE_PURCHASE,
        current_value=_SAMPLE_VALUE,
        mortgage_balance=_SAMPLE_MORTGAGE,
    )

    prop = result["result"]["property"]
    assert prop["equity"] == pytest.approx(142_500.0), "equity must be current_value - mortgage"
    assert prop["equity_pct"] == pytest.approx(27.27, abs=0.1), "equity_pct must be ~27.27%"


# ---------------------------------------------------------------------------
# Test 3 — appreciation computed correctly
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_appreciation_computed():
    """
    GIVEN  purchase_price=450000 and current_value=522500
    WHEN   add_property is called
    THEN   appreciation == 72500 and appreciation_pct ≈ 16.11%.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, property_store_clear
    property_store_clear()

    result = await add_property(
        address=_SAMPLE_ADDRESS,
        purchase_price=_SAMPLE_PURCHASE,
        current_value=_SAMPLE_VALUE,
        mortgage_balance=_SAMPLE_MORTGAGE,
    )

    prop = result["result"]["property"]
    assert prop["appreciation"] == pytest.approx(72_500.0)
    assert prop["appreciation_pct"] == pytest.approx(16.11, abs=0.1)


# ---------------------------------------------------------------------------
# Test 4 — list_properties empty store
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_properties_empty():
    """
    GIVEN  no properties have been added
    WHEN   list_properties is called
    THEN   success=True, properties=[], all summary totals are zero.
    """
    _set_flag("true")
    from tools.property_tracker import list_properties, property_store_clear
    property_store_clear()

    result = await list_properties()

    assert result["success"] is True
    assert result["result"]["properties"] == []
    summary = result["result"]["summary"]
    assert summary["property_count"] == 0
    assert summary["total_equity"] == 0
    assert summary["total_current_value"] == 0


# ---------------------------------------------------------------------------
# Test 5 — list_properties summary totals are correct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_properties_totals():
    """
    GIVEN  two properties are added
    WHEN   list_properties is called
    THEN   summary totals are the correct arithmetic sum of both properties.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, list_properties, property_store_clear
    property_store_clear()

    await add_property(
        address="123 Main St, Austin, TX",
        purchase_price=450_000,
        current_value=522_500,
        mortgage_balance=380_000,
    )
    await add_property(
        address="456 Round Rock Ave, Round Rock, TX",
        purchase_price=320_000,
        current_value=403_500,
        mortgage_balance=250_000,
        county_key="williamson_county",
    )

    result = await list_properties()
    assert result["success"] is True

    summary = result["result"]["summary"]
    assert summary["property_count"] == 2
    assert summary["total_purchase_price"] == pytest.approx(770_000)
    assert summary["total_current_value"] == pytest.approx(926_000)
    assert summary["total_mortgage_balance"] == pytest.approx(630_000)
    assert summary["total_equity"] == pytest.approx(296_000)  # 926000 - 630000
    assert summary["total_equity_pct"] == pytest.approx(31.96, abs=0.1)


# ---------------------------------------------------------------------------
# Test 6 — get_real_estate_equity returns correct totals
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_real_estate_equity():
    """
    GIVEN  one property with equity 142500
    WHEN   get_real_estate_equity is called
    THEN   total_real_estate_equity == 142500.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, get_real_estate_equity, property_store_clear
    property_store_clear()

    await add_property(
        address=_SAMPLE_ADDRESS,
        purchase_price=_SAMPLE_PURCHASE,
        current_value=_SAMPLE_VALUE,
        mortgage_balance=_SAMPLE_MORTGAGE,
    )

    result = await get_real_estate_equity()
    assert result["success"] is True
    assert result["result"]["total_real_estate_equity"] == pytest.approx(142_500.0)
    assert result["result"]["total_real_estate_value"] == pytest.approx(522_500.0)
    assert result["result"]["property_count"] == 1


# ---------------------------------------------------------------------------
# Test 7 — feature flag disabled
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feature_flag_disabled():
    """
    GIVEN  ENABLE_REAL_ESTATE=false
    WHEN   any property tracker tool is called
    THEN   all return success=False with PROPERTY_TRACKER_FEATURE_DISABLED.
    """
    _set_flag("false")
    from tools.property_tracker import (
        add_property, list_properties, get_real_estate_equity,
        remove_property, is_property_tracking_enabled, property_store_clear,
    )
    property_store_clear()

    assert is_property_tracking_enabled() is False

    for coro in [
        add_property(_SAMPLE_ADDRESS, _SAMPLE_PURCHASE),
        list_properties(),
        get_real_estate_equity(),
        remove_property("prop_001"),
    ]:
        result = await coro
        assert result["success"] is False
        assert isinstance(result["error"], dict)
        assert result["error"]["code"] == "PROPERTY_TRACKER_FEATURE_DISABLED"

    _set_flag("true")


# ---------------------------------------------------------------------------
# Test 8 — remove_property removes the correct entry
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_remove_property():
    """
    GIVEN  one property exists
    WHEN   remove_property is called with its ID
    THEN   success=True, and list_properties afterwards shows empty.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, list_properties, remove_property, property_store_clear
    property_store_clear()

    add_result = await add_property(
        address=_SAMPLE_ADDRESS,
        purchase_price=_SAMPLE_PURCHASE,
        current_value=_SAMPLE_VALUE,
        mortgage_balance=_SAMPLE_MORTGAGE,
    )
    prop_id = add_result["result"]["property"]["id"]

    remove_result = await remove_property(prop_id)
    assert remove_result["success"] is True
    assert remove_result["result"]["status"] == "removed"

    list_result = await list_properties()
    assert list_result["result"]["properties"] == []


# ---------------------------------------------------------------------------
# Test 9 — remove_property not found returns structured error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_remove_property_not_found():
    """
    GIVEN  the store is empty
    WHEN   remove_property is called with a non-existent ID
    THEN   success=False with code=PROPERTY_TRACKER_NOT_FOUND, no crash.
    """
    _set_flag("true")
    from tools.property_tracker import remove_property, property_store_clear
    property_store_clear()

    result = await remove_property("prop_999")
    assert result["success"] is False
    assert isinstance(result["error"], dict)
    assert result["error"]["code"] == "PROPERTY_TRACKER_NOT_FOUND"
    assert "prop_999" in result["error"]["message"]


# ---------------------------------------------------------------------------
# Test 10 — validation: empty address
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_property_empty_address():
    """
    GIVEN  an empty address string
    WHEN   add_property is called
    THEN   success=False with code=PROPERTY_TRACKER_INVALID_INPUT.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, property_store_clear
    property_store_clear()

    result = await add_property(address="   ", purchase_price=450_000)
    assert result["success"] is False
    assert result["error"]["code"] == "PROPERTY_TRACKER_INVALID_INPUT"


# ---------------------------------------------------------------------------
# Test 11 — validation: zero purchase price
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_property_zero_price():
    """
    GIVEN  a purchase_price of 0
    WHEN   add_property is called
    THEN   success=False with code=PROPERTY_TRACKER_INVALID_INPUT.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, property_store_clear
    property_store_clear()

    result = await add_property(address=_SAMPLE_ADDRESS, purchase_price=0)
    assert result["success"] is False
    assert result["error"]["code"] == "PROPERTY_TRACKER_INVALID_INPUT"


# ---------------------------------------------------------------------------
# Test 12 — no mortgage: equity equals full current value
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_mortgage_equity_full_value():
    """
    GIVEN  mortgage_balance defaults to 0
    WHEN   add_property is called
    THEN   equity == current_value (property is fully owned).
    """
    _set_flag("true")
    from tools.property_tracker import add_property, property_store_clear
    property_store_clear()

    result = await add_property(
        address=_SAMPLE_ADDRESS,
        purchase_price=_SAMPLE_PURCHASE,
        current_value=_SAMPLE_VALUE,
    )
    prop = result["result"]["property"]
    assert prop["equity"] == pytest.approx(_SAMPLE_VALUE)
    assert prop["equity_pct"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# Test 13 — current_value defaults to purchase_price
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_current_value_defaults_to_purchase_price():
    """
    GIVEN  current_value is not supplied
    WHEN   add_property is called
    THEN   current_value equals purchase_price and appreciation == 0.
    """
    _set_flag("true")
    from tools.property_tracker import add_property, property_store_clear
    property_store_clear()

    result = await add_property(
        address=_SAMPLE_ADDRESS,
        purchase_price=_SAMPLE_PURCHASE,
    )
    prop = result["result"]["property"]
    assert prop["current_value"] == pytest.approx(_SAMPLE_PURCHASE)
    assert prop["appreciation"] == pytest.approx(0.0)
