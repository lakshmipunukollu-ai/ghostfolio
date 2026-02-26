"""
Property Tracker Tool — AgentForge integration
===============================================
Feature flag: set ENABLE_REAL_ESTATE=true in .env to activate.
(Shares the same flag as the real estate market data tool.)

Allows users to track real estate properties they own alongside
their financial portfolio. Equity is computed as:
    equity = current_value - mortgage_balance

Three capabilities:
  1. add_property(...)            — record a property you own
  2. list_properties()            — show all properties with equity computed
  3. get_real_estate_equity()     — total equity across all properties (for net worth)

Schema (StoredProperty):
  id, address, property_type, purchase_price, purchase_date,
  current_value, mortgage_balance, equity, equity_pct,
  county_key, added_at

All functions return the standard tool result envelope:
  {tool_name, success, tool_result_id, timestamp, result}  — on success
  {tool_name, success, tool_result_id, error: {code, message}}  — on failure
"""

import os
import time
from datetime import datetime

# ---------------------------------------------------------------------------
# Feature flag  (shared with real_estate.py)
# ---------------------------------------------------------------------------

def is_property_tracking_enabled() -> bool:
    """Returns True only when ENABLE_REAL_ESTATE=true in environment."""
    return os.getenv("ENABLE_REAL_ESTATE", "false").strip().lower() == "true"


_FEATURE_DISABLED_RESPONSE = {
    "tool_name": "property_tracker",
    "success": False,
    "tool_result_id": "property_tracker_disabled",
    "error": {
        "code": "PROPERTY_TRACKER_FEATURE_DISABLED",
        "message": (
            "The Property Tracker feature is not currently enabled. "
            "Set ENABLE_REAL_ESTATE=true in your environment to activate it."
        ),
    },
}

# ---------------------------------------------------------------------------
# In-memory property store
# ---------------------------------------------------------------------------

_property_store: dict[str, dict] = {}
_property_counter: list[int] = [0]  # mutable container so helpers can increment it


def property_store_clear() -> None:
    """Clears the property store and resets the counter. Used in tests."""
    _property_store.clear()
    _property_counter[0] = 0


def _next_id() -> str:
    _property_counter[0] += 1
    return f"prop_{_property_counter[0]:03d}"


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

async def add_property(
    address: str,
    purchase_price: float,
    current_value: float | None = None,
    mortgage_balance: float = 0.0,
    county_key: str = "austin",
    property_type: str = "Single Family",
    purchase_date: str | None = None,
) -> dict:
    """
    Records a property in the in-memory store.

    Args:
        address:          Full street address (e.g. "123 Barton Hills Dr, Austin, TX 78704").
        purchase_price:   Original purchase price in USD.
        current_value:    Current estimated market value. Defaults to purchase_price if None.
        mortgage_balance: Outstanding mortgage balance. Defaults to 0 (paid off / no mortgage).
        county_key:       ACTRIS data key for market context (e.g. "austin", "travis_county").
        property_type:    "Single Family", "Condo", "Townhouse", "Multi-Family", or "Land".
        purchase_date:    Optional ISO date string (YYYY-MM-DD).
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_add_{int(datetime.utcnow().timestamp())}"

    # Validation
    if not address or not address.strip():
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {
                "code": "PROPERTY_TRACKER_INVALID_INPUT",
                "message": "address is required and cannot be empty.",
            },
        }
    if purchase_price <= 0:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {
                "code": "PROPERTY_TRACKER_INVALID_INPUT",
                "message": "purchase_price must be greater than zero.",
            },
        }

    effective_value = current_value if current_value is not None else purchase_price
    equity = round(effective_value - mortgage_balance, 2)
    equity_pct = round((equity / effective_value * 100), 2) if effective_value > 0 else 0.0
    appreciation = round(effective_value - purchase_price, 2)
    appreciation_pct = round((appreciation / purchase_price * 100), 2) if purchase_price > 0 else 0.0

    prop_id = _next_id()
    record = {
        "id": prop_id,
        "address": address.strip(),
        "property_type": property_type,
        "purchase_price": purchase_price,
        "purchase_date": purchase_date,
        "current_value": effective_value,
        "mortgage_balance": mortgage_balance,
        "equity": equity,
        "equity_pct": equity_pct,
        "appreciation": appreciation,
        "appreciation_pct": appreciation_pct,
        "county_key": county_key,
        "added_at": datetime.utcnow().isoformat(),
    }
    _property_store[prop_id] = record

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "status": "added",
            "property": record,
            "message": (
                f"Property recorded: {address.strip()}. "
                f"Current equity: ${equity:,.0f} "
                f"({equity_pct:.1f}% of ${effective_value:,.0f} value)."
            ),
        },
    }


async def list_properties() -> dict:
    """
    Returns all stored properties with per-property equity and portfolio totals.
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_list_{int(datetime.utcnow().timestamp())}"
    properties = list(_property_store.values())

    if not properties:
        return {
            "tool_name": "property_tracker",
            "success": True,
            "tool_result_id": tool_result_id,
            "timestamp": datetime.utcnow().isoformat(),
            "result": {
                "properties": [],
                "summary": {
                    "property_count": 0,
                    "total_purchase_price": 0,
                    "total_current_value": 0,
                    "total_mortgage_balance": 0,
                    "total_equity": 0,
                    "total_equity_pct": 0.0,
                },
                "message": (
                    "No properties tracked yet. "
                    "Add a property with: \"Add my property at [address], "
                    "purchased for $X, worth $Y, mortgage $Z.\""
                ),
            },
        }

    total_purchase = sum(p["purchase_price"] for p in properties)
    total_value = sum(p["current_value"] for p in properties)
    total_mortgage = sum(p["mortgage_balance"] for p in properties)
    total_equity = round(total_value - total_mortgage, 2)
    total_equity_pct = round((total_equity / total_value * 100), 2) if total_value > 0 else 0.0

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "properties": properties,
            "summary": {
                "property_count": len(properties),
                "total_purchase_price": total_purchase,
                "total_current_value": total_value,
                "total_mortgage_balance": total_mortgage,
                "total_equity": total_equity,
                "total_equity_pct": total_equity_pct,
            },
        },
    }


async def get_real_estate_equity() -> dict:
    """
    Returns total real estate equity across all tracked properties.
    Designed to be combined with portfolio_analysis for net worth calculation.
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_equity_{int(datetime.utcnow().timestamp())}"
    properties = list(_property_store.values())

    total_value = sum(p["current_value"] for p in properties)
    total_mortgage = sum(p["mortgage_balance"] for p in properties)
    total_equity = round(total_value - total_mortgage, 2)

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "property_count": len(properties),
            "total_real_estate_value": total_value,
            "total_mortgage_balance": total_mortgage,
            "total_real_estate_equity": total_equity,
        },
    }


async def remove_property(property_id: str) -> dict:
    """
    Removes a property from the store by its ID (e.g. 'prop_001').
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_remove_{int(datetime.utcnow().timestamp())}"
    prop_id = property_id.strip().lower()

    if prop_id not in _property_store:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {
                "code": "PROPERTY_TRACKER_NOT_FOUND",
                "message": (
                    f"Property '{property_id}' not found. "
                    "Use list_properties() to see valid IDs."
                ),
            },
        }

    removed = _property_store.pop(prop_id)
    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "status": "removed",
            "property_id": prop_id,
            "address": removed["address"],
            "message": f"Property removed: {removed['address']}.",
        },
    }
