"""
Property Tracker Tool — AgentForge integration
===============================================
Feature flag: set ENABLE_REAL_ESTATE=true in .env to activate.
(Shares the same flag as the real estate market data tool.)

Allows users to track real estate properties they own alongside
their financial portfolio. Equity is computed as:
    equity = current_value - mortgage_balance

Seven capabilities:
  1. add_property(...)            — record a property you own
  2. get_properties()             — show all active properties with equity
  3. list_properties()            — alias for get_properties()
  4. update_property(...)         — update current value, mortgage, or rent
  5. remove_property(id)          — soft-delete (set is_active = 0)
  6. get_real_estate_equity()     — total equity across all properties
  7. get_total_net_worth(...)      — portfolio + real estate combined

Storage: SQLite at agent/data/properties.db
  (override path with PROPERTIES_DB_PATH env var — used in tests for :memory:)

All functions return the standard tool result envelope:
  {tool_name, success, tool_result_id, timestamp, result}  — on success
  {tool_name, success, tool_result_id, error: {code, message}}  — on failure
"""

import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

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
# SQLite connection helpers
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS properties (
        id TEXT PRIMARY KEY,
        address TEXT NOT NULL,
        property_type TEXT DEFAULT 'Single Family',
        purchase_price REAL NOT NULL,
        purchase_date TEXT,
        current_value REAL NOT NULL,
        mortgage_balance REAL DEFAULT 0,
        monthly_rent REAL DEFAULT 0,
        county_key TEXT DEFAULT 'austin',
        is_active INTEGER DEFAULT 1,
        created_at TEXT,
        updated_at TEXT
    )
"""

# Module-level cached connection for :memory: databases.
# SQLite :memory: creates a fresh DB per connection — we must reuse the same one.
_MEMORY_CONN: Optional[sqlite3.Connection] = None


def _db_path() -> str:
    """Returns the SQLite database path (configurable via PROPERTIES_DB_PATH)."""
    env_path = os.getenv("PROPERTIES_DB_PATH")
    if env_path:
        return env_path
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    agent_dir = os.path.dirname(tools_dir)
    data_dir = os.path.join(agent_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "properties.db")


def _get_conn() -> sqlite3.Connection:
    """
    Returns a SQLite connection with the schema initialized.
    For :memory: databases, returns the same connection every time so
    data persists across calls within a session / test run.
    """
    global _MEMORY_CONN
    path = _db_path()

    if path == ":memory:":
        if _MEMORY_CONN is None:
            _MEMORY_CONN = sqlite3.connect(":memory:", check_same_thread=False)
            _MEMORY_CONN.row_factory = sqlite3.Row
            _MEMORY_CONN.execute(_SCHEMA_SQL)
            _MEMORY_CONN.commit()
        return _MEMORY_CONN

    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(_SCHEMA_SQL)
    conn.commit()
    return conn


def _close_conn(conn: sqlite3.Connection) -> None:
    """Closes file-based connections; leaves :memory: connection open."""
    if _db_path() != ":memory:":
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Converts a sqlite3.Row to a plain dict with computed equity/appreciation fields."""
    d = dict(row)
    current_value = d.get("current_value", 0) or 0
    mortgage_balance = d.get("mortgage_balance", 0) or 0
    purchase_price = d.get("purchase_price", 0) or 0

    equity = round(current_value - mortgage_balance, 2)
    equity_pct = round((equity / current_value * 100), 2) if current_value > 0 else 0.0
    appreciation = round(current_value - purchase_price, 2)
    appreciation_pct = (
        round((appreciation / purchase_price * 100), 2) if purchase_price > 0 else 0.0
    )

    d["equity"] = equity
    d["equity_pct"] = equity_pct
    d["appreciation"] = appreciation
    d["appreciation_pct"] = appreciation_pct
    # Backward-compat alias: existing tests check for "added_at"
    d["added_at"] = d.get("created_at")
    return d


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def property_store_clear() -> None:
    """
    Wipes ALL property records. Used in tests to reset state between cases.
    For :memory: databases, deletes all rows from the shared connection.
    """
    global _MEMORY_CONN
    path = _db_path()
    try:
        if path == ":memory:":
            if _MEMORY_CONN is not None:
                _MEMORY_CONN.execute("DELETE FROM properties")
                _MEMORY_CONN.commit()
        else:
            conn = _get_conn()
            conn.execute("DELETE FROM properties")
            conn.commit()
            _close_conn(conn)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

async def add_property(
    address: str,
    purchase_price: float,
    current_value: Optional[float] = None,
    mortgage_balance: float = 0.0,
    monthly_rent: float = 0.0,
    county_key: str = "austin",
    property_type: str = "Single Family",
    purchase_date: Optional[str] = None,
) -> dict:
    """
    Records a property in the SQLite store.

    Args:
        address:          Full street address.
        purchase_price:   Original purchase price in USD.
        current_value:    Current estimated market value. Defaults to purchase_price.
        mortgage_balance: Outstanding mortgage balance. Defaults to 0.
        monthly_rent:     Monthly rental income if a rental property. Defaults to 0.
        county_key:       ACTRIS area key (e.g. "austin", "travis_county").
        property_type:    "Single Family", "Condo", "Townhouse", etc.
        purchase_date:    Optional ISO date string (YYYY-MM-DD).
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_add_{int(datetime.utcnow().timestamp())}"

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
    prop_id = f"prop_{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()

    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO properties
               (id, address, property_type, purchase_price, purchase_date,
                current_value, mortgage_balance, monthly_rent, county_key,
                is_active, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (
                prop_id, address.strip(), property_type, purchase_price,
                purchase_date, effective_value, mortgage_balance, monthly_rent,
                county_key, now, now,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM properties WHERE id = ?", (prop_id,)
        ).fetchone()
        _close_conn(conn)
        record = _row_to_dict(row)
    except Exception as exc:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {"code": "PROPERTY_TRACKER_DB_ERROR", "message": str(exc)},
        }

    equity = record["equity"]
    equity_pct = record["equity_pct"]

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": now,
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


async def get_properties() -> dict:
    """
    Returns all active properties with per-property equity and portfolio totals.
    Primary read function. list_properties() is kept as an alias.
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_list_{int(datetime.utcnow().timestamp())}"

    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT * FROM properties WHERE is_active = 1 ORDER BY created_at"
        ).fetchall()
        _close_conn(conn)
        properties = [_row_to_dict(row) for row in rows]
    except Exception as exc:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {"code": "PROPERTY_TRACKER_DB_ERROR", "message": str(exc)},
        }

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
                    "total_monthly_rent": 0,
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
    total_equity_pct = (
        round((total_equity / total_value * 100), 2) if total_value > 0 else 0.0
    )
    total_rent = sum(p.get("monthly_rent", 0) or 0 for p in properties)

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
                "total_monthly_rent": total_rent,
            },
        },
    }


async def list_properties() -> dict:
    """Alias for get_properties() — kept for backward compatibility."""
    return await get_properties()


async def update_property(
    property_id: str,
    current_value: Optional[float] = None,
    mortgage_balance: Optional[float] = None,
    monthly_rent: Optional[float] = None,
) -> dict:
    """
    Updates a tracked property's current value, mortgage balance, or monthly rent.

    Args:
        property_id:      ID of the property to update (e.g. 'prop_a1b2c3d4').
        current_value:    New current market value in USD.
        mortgage_balance: Updated outstanding mortgage balance in USD.
        monthly_rent:     Updated monthly rental income in USD.

    Returns:
        Updated property record with recalculated equity.
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_update_{int(datetime.utcnow().timestamp())}"
    prop_id = property_id.strip()

    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT * FROM properties WHERE id = ? AND is_active = 1", (prop_id,)
        ).fetchone()

        if row is None:
            _close_conn(conn)
            return {
                "tool_name": "property_tracker",
                "success": False,
                "tool_result_id": tool_result_id,
                "error": {
                    "code": "PROPERTY_TRACKER_NOT_FOUND",
                    "message": (
                        f"Property '{property_id}' not found. "
                        "Use get_properties() to see valid IDs."
                    ),
                },
            }

        updates = []
        params = []
        if current_value is not None:
            updates.append("current_value = ?")
            params.append(current_value)
        if mortgage_balance is not None:
            updates.append("mortgage_balance = ?")
            params.append(mortgage_balance)
        if monthly_rent is not None:
            updates.append("monthly_rent = ?")
            params.append(monthly_rent)

        if not updates:
            _close_conn(conn)
            return {
                "tool_name": "property_tracker",
                "success": False,
                "tool_result_id": tool_result_id,
                "error": {
                    "code": "PROPERTY_TRACKER_INVALID_INPUT",
                    "message": (
                        "At least one of current_value, mortgage_balance, "
                        "or monthly_rent must be provided."
                    ),
                },
            }

        now = datetime.utcnow().isoformat()
        updates.append("updated_at = ?")
        params.append(now)
        params.append(prop_id)

        conn.execute(
            f"UPDATE properties SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()

        updated_row = conn.execute(
            "SELECT * FROM properties WHERE id = ?", (prop_id,)
        ).fetchone()
        _close_conn(conn)
        record = _row_to_dict(updated_row)
    except Exception as exc:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {"code": "PROPERTY_TRACKER_DB_ERROR", "message": str(exc)},
        }

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "status": "updated",
            "property": record,
            "message": (
                f"Property updated: {record['address']}. "
                f"New equity: ${record['equity']:,.0f}."
            ),
        },
    }


async def remove_property(property_id: str) -> dict:
    """
    Soft-deletes a property by setting is_active = 0.
    Data is preserved for audit purposes.
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_remove_{int(datetime.utcnow().timestamp())}"
    prop_id = property_id.strip().lower()

    try:
        conn = _get_conn()
        row = conn.execute(
            "SELECT * FROM properties WHERE id = ? AND is_active = 1", (prop_id,)
        ).fetchone()

        if row is None:
            _close_conn(conn)
            return {
                "tool_name": "property_tracker",
                "success": False,
                "tool_result_id": tool_result_id,
                "error": {
                    "code": "PROPERTY_TRACKER_NOT_FOUND",
                    "message": (
                        f"Property '{property_id}' not found. "
                        "Use get_properties() to see valid IDs."
                    ),
                },
            }

        address = row["address"]
        conn.execute(
            "UPDATE properties SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), prop_id),
        )
        conn.commit()
        _close_conn(conn)
    except Exception as exc:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {"code": "PROPERTY_TRACKER_DB_ERROR", "message": str(exc)},
        }

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "status": "removed",
            "property_id": prop_id,
            "address": address,
            "message": f"Property removed: {address}.",
        },
    }


async def get_real_estate_equity() -> dict:
    """
    Returns total real estate equity across all tracked active properties.
    Designed to be combined with portfolio_analysis for net worth calculation.
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_equity_{int(datetime.utcnow().timestamp())}"

    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT current_value, mortgage_balance "
            "FROM properties WHERE is_active = 1"
        ).fetchall()
        _close_conn(conn)
    except Exception as exc:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {"code": "PROPERTY_TRACKER_DB_ERROR", "message": str(exc)},
        }

    total_value = sum(r["current_value"] for r in rows)
    total_mortgage = sum(r["mortgage_balance"] for r in rows)
    total_equity = round(total_value - total_mortgage, 2)

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "property_count": len(rows),
            "total_real_estate_value": total_value,
            "total_mortgage_balance": total_mortgage,
            "total_real_estate_equity": total_equity,
        },
    }


async def get_total_net_worth(portfolio_value: float) -> dict:
    """
    Combines live investment portfolio value with real estate equity
    for a unified net worth view.

    Args:
        portfolio_value: Total liquid investment portfolio value in USD
                         (from portfolio_analysis tool result).

    Returns:
        Dict with investment_portfolio, real_estate_equity, total_net_worth,
        properties list, and plain-English summary.
    """
    if not is_property_tracking_enabled():
        return _FEATURE_DISABLED_RESPONSE

    tool_result_id = f"prop_networth_{int(datetime.utcnow().timestamp())}"

    try:
        conn = _get_conn()
        rows = conn.execute(
            "SELECT * FROM properties WHERE is_active = 1 ORDER BY created_at"
        ).fetchall()
        _close_conn(conn)
        properties = [_row_to_dict(row) for row in rows]
    except Exception as exc:
        return {
            "tool_name": "property_tracker",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": {"code": "PROPERTY_TRACKER_DB_ERROR", "message": str(exc)},
        }

    total_value = sum(p["current_value"] for p in properties)
    total_mortgage = sum(p["mortgage_balance"] for p in properties)
    real_estate_equity = round(total_value - total_mortgage, 2)
    total_net_worth = round(portfolio_value + real_estate_equity, 2)

    if properties:
        summary = (
            f"Total net worth ${total_net_worth:,.0f} across investments "
            f"(${portfolio_value:,.0f}) and real estate equity "
            f"(${real_estate_equity:,.0f})."
        )
    else:
        summary = (
            f"Investment portfolio: ${portfolio_value:,.0f}. "
            "No properties tracked yet. Add properties to include real estate equity."
        )

    return {
        "tool_name": "property_tracker",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {
            "investment_portfolio": portfolio_value,
            "real_estate_equity": real_estate_equity,
            "total_net_worth": total_net_worth,
            "properties": properties,
            "summary": summary,
        },
    }


def analyze_equity_options(
    property_id: str,
    market_return_assumption: float = 0.07,
) -> dict:
    """Analyzes 3 options for home equity: leave untouched,
    cash-out refi and invest, or use for rental property."""

    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM properties WHERE id=? AND is_active=1",
            (property_id,),
        )
        row = cur.fetchone()
        _close_conn(conn)
    except Exception as e:
        return {
            "error": f"Database error: {str(e)}",
            "property_id": property_id,
        }

    if not row:
        return {
            "error": f"Property {property_id} not found",
            "property_id": property_id,
        }

    current_value = row["current_value"]
    mortgage_balance = row["mortgage_balance"] or 0
    equity = current_value - mortgage_balance
    accessible = equity * 0.80

    if accessible <= 0:
        return {
            "property_address": row["address"],
            "current_value": current_value,
            "mortgage_balance": mortgage_balance,
            "current_equity": equity,
            "accessible_equity": 0,
            "message": "Insufficient equity for cash-out options",
            "options": {},
        }

    monthly_rate = 0.0695 / 12
    n = 360

    # Option A: Leave untouched
    projected_value_a = current_value * (1.04 ** 10)
    equity_a = projected_value_a - mortgage_balance

    # Option B: Cash-out refi + invest
    new_balance = mortgage_balance + accessible
    new_payment = new_balance * (
        monthly_rate * (1 + monthly_rate) ** n
    ) / ((1 + monthly_rate) ** n - 1)

    old_payment = (
        mortgage_balance
        * (monthly_rate * (1 + monthly_rate) ** n)
        / ((1 + monthly_rate) ** n - 1)
        if mortgage_balance > 0
        else 0
    )

    payment_increase = new_payment - old_payment
    invested_b = accessible * ((1 + market_return_assumption) ** 10)
    home_equity_b = (current_value * 1.04 ** 10) - new_balance
    total_b = home_equity_b + invested_b

    # Option C: Rental property
    rental_price = current_value * 0.9
    rental_down = accessible
    rental_mortgage_balance = rental_price - rental_down
    rental_payment = (
        rental_mortgage_balance
        * (monthly_rate * (1 + monthly_rate) ** n)
        / ((1 + monthly_rate) ** n - 1)
        if rental_mortgage_balance > 0
        else 0
    )

    monthly_rent_income = current_value * 0.007
    monthly_cash_flow = monthly_rent_income - rental_payment
    ten_yr_cash_flow = monthly_cash_flow * 120

    return {
        "property_address": row["address"],
        "current_value": current_value,
        "mortgage_balance": mortgage_balance,
        "current_equity": round(equity),
        "accessible_equity": round(accessible),
        "options": {
            "leave_untouched": {
                "label": "Option A — Do Nothing",
                "projected_equity_10yr": round(equity_a),
                "projected_home_value": round(projected_value_a),
                "upside": "No risk, no new debt, steady appreciation",
                "downside": "Equity is illiquid, not generating returns",
            },
            "cash_out_invest": {
                "label": "Option B — Cash-Out Refi + Invest",
                "cash_extracted": round(accessible),
                "monthly_payment_increase": round(payment_increase),
                "invested_value_10yr": round(invested_b),
                "total_wealth_10yr": round(total_b),
                "upside": "Equity working harder in the market",
                "downside": "Higher payment, market risk",
            },
            "rental_property": {
                "label": "Option C — Buy Rental Property",
                "monthly_cash_flow": round(monthly_cash_flow),
                "ten_year_cash_flow": round(ten_yr_cash_flow),
                "upside": "Passive income + appreciation on 2 properties",
                "downside": "Landlord responsibilities, vacancy risk",
            },
        },
        "recommendation": (
            f"Option B generates the most total wealth at "
            f"${total_b:,.0f} by year 10 if markets perform well. "
            f"Option C provides ${monthly_cash_flow:,.0f}/mo passive income. "
            f"Option A is best for simplicity and certainty."
        ),
        "disclaimer": (
            "These are projections not guarantees. "
            "Consult a financial advisor before refinancing."
        ),
        "data_source": (
            "Market assumptions: 4% home appreciation, "
            f"{market_return_assumption * 100:.0f}% investment return, "
            "6.95% mortgage rate"
        ),
    }
