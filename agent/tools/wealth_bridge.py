"""
Wealth Bridge Tool — AgentForge integration
============================================
Bridges live Ghostfolio portfolio data with real estate purchasing power.

Three capabilities:
  1. calculate_down_payment_power(portfolio_value, target_cities)
       — which markets can your portfolio fund a 20% down payment?
  2. calculate_job_offer_affordability(offer_salary, offer_city,
                                       current_salary, current_city)
       — is the job offer a real raise in purchasing power terms?
  3. get_portfolio_real_estate_summary(target_cities)
       — master function: reads live portfolio then runs down payment calc

Data routing:
  Austin TX areas → _MOCK_SNAPSHOTS in real_estate.py (real ACTRIS data)
  All other cities → teleport_api.py (live Teleport API + fallback)

Mortgage assumption: 30-year fixed at 6.95%, 20% down, payment × 1.25
  for estimated taxes + insurance.
"""

import asyncio
import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from real_estate import _MOCK_SNAPSHOTS, _normalize_city
except ImportError:
    from agent.tools.real_estate import _MOCK_SNAPSHOTS, _normalize_city

try:
    from teleport_api import (
        HARDCODED_FALLBACK,
        _is_austin_area,
        get_city_housing_data,
    )
except ImportError:
    from agent.tools.teleport_api import (
        HARDCODED_FALLBACK,
        _is_austin_area,
        get_city_housing_data,
    )

# ---------------------------------------------------------------------------
# COL index values for Austin TX sub-markets (ACTRIS coverage areas)
# National average = 100; lower = more affordable
# ---------------------------------------------------------------------------

_AUSTIN_COL_INDEX: dict[str, float] = {
    "austin": 95.4,
    "travis_county": 95.4,
    "austin_msa": 91.0,
    "williamson_county": 88.2,
    "hays_county": 82.1,
    "bastrop_county": 78.3,
    "caldwell_county": 71.2,
}

# State income tax lookup (no tax = not in this dict)
_STATE_INCOME_TAX: dict[str, float] = {
    "CA": 0.093, "NY": 0.0685, "OR": 0.099, "MN": 0.0985,
    "NJ": 0.1075, "VT": 0.0875, "DC": 0.0895, "HI": 0.11,
    "ME": 0.0715, "IA": 0.0575, "SC": 0.07, "CT": 0.0699,
    "WI": 0.0765, "MA": 0.05, "IL": 0.0495, "IN": 0.032,
    "MI": 0.0425, "GA": 0.055, "NC": 0.0499, "VA": 0.0575,
    "MD": 0.0575, "CO": 0.044, "AZ": 0.025, "UT": 0.0485,
    "KS": 0.057, "MO": 0.0495, "OH": 0.0399, "PA": 0.0307,
    "NM": 0.059, "LA": 0.06, "MS": 0.05, "AL": 0.05,
    "AR": 0.044, "NE": 0.0664, "ID": 0.058, "MT": 0.069,
    "ND": 0.029, "OK": 0.0475, "KY": 0.045,
}

_NO_INCOME_TAX_STATES = {"TX", "WA", "FL", "NV", "WY", "SD", "AK", "NH", "TN"}

# Default target markets (all 7 Austin ACTRIS areas)
_DEFAULT_AUSTIN_MARKETS = [
    "austin", "travis_county", "williamson_county",
    "hays_county", "bastrop_county", "caldwell_county", "austin_msa",
]

# Mortgage constants
_MORTGAGE_RATE = 0.0695
_MORTGAGE_TERM = 360  # 30 years in months
_TAX_INSURANCE_MULTIPLIER = 1.25


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _monthly_payment(price: float) -> float:
    """Calculates estimated total monthly payment (PITI) at 6.95% 30yr, 20% down."""
    principal = price * 0.80
    r = _MORTGAGE_RATE / 12
    n = _MORTGAGE_TERM
    base_payment = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return round(base_payment * _TAX_INSURANCE_MULTIPLIER, 0)


def _get_austin_data(city_key: str) -> Optional[dict]:
    """Reads ACTRIS snapshot for a given city_key from real_estate._MOCK_SNAPSHOTS."""
    return _MOCK_SNAPSHOTS.get(city_key)


def _resolve_city_data_sync(city_name: str) -> tuple[str, dict]:
    """
    Synchronously resolves city data for wealth bridge calculations.
    Returns (display_name, data_dict).

    Austin areas: uses _MOCK_SNAPSHOTS (real ACTRIS data, sync)
    Other cities: uses HARDCODED_FALLBACK (sync) or generic estimate
    """
    if _is_austin_area(city_name):
        city_key = _normalize_city(city_name)
        snap = _MOCK_SNAPSHOTS.get(city_key, {})
        display = snap.get("city", city_name)
        return display, snap

    # Non-Austin: look up in fallback dict
    lower = city_name.lower().strip()
    slug_guess = lower.replace(" ", "-")
    # Direct slug match
    if slug_guess in HARDCODED_FALLBACK:
        return HARDCODED_FALLBACK[slug_guess]["city"], dict(HARDCODED_FALLBACK[slug_guess])
    # Partial match
    for slug, data in HARDCODED_FALLBACK.items():
        if lower in data["city"].lower() or slug.replace("-", " ") in lower:
            return data["city"], dict(data)
    # Generic
    return city_name, {
        "city": city_name,
        "median_price": 500_000,
        "MedianRentMonthly": 2000,
        "col_index": 100.0,
        "AffordabilityScore": 5.0,
        "data_source": "Estimate (city not in database)",
    }


def _col_index_for_city(city_name: str, city_data: dict) -> float:
    """
    Returns the COL index for a city (100 = US average).
    Austin areas: use _AUSTIN_COL_INDEX table.
    Others: use col_index from city_data, or derive from Teleport col_score.
    """
    if _is_austin_area(city_name):
        city_key = _normalize_city(city_name)
        return _AUSTIN_COL_INDEX.get(city_key, 95.4)

    if "col_index" in city_data:
        return float(city_data["col_index"])

    # Derive from Teleport col_score (0–10): 10=cheap, 0=expensive
    col_score = city_data.get("col_score", 5.0)
    return round((10.0 - col_score) * 18.0 + 20.0, 1)


def _state_tax_note(city_a: str, city_b: str) -> str:
    """Builds a human-readable state income tax note for two cities."""
    def _state_code(city: str) -> Optional[str]:
        # Simple heuristics from known cities
        city_lower = city.lower()
        state_map = {
            "tx": "TX", "austin": "TX", "dallas": "TX", "houston": "TX", "san antonio": "TX",
            "wa": "WA", "seattle": "WA",
            "fl": "FL", "miami": "FL", "orlando": "FL", "tampa": "FL",
            "nv": "NV", "las vegas": "NV",
            "ca": "CA", "san francisco": "CA", "los angeles": "CA", "san diego": "CA",
            "ny": "NY", "new york": "NY", "brooklyn": "NY",
            "co": "CO", "denver": "CO",
            "il": "IL", "chicago": "IL",
            "ma": "MA", "boston": "MA",
            "tn": "TN", "nashville": "TN",
            "ga": "GA", "atlanta": "GA",
            "or": "OR", "portland": "OR",
            "az": "AZ", "phoenix": "AZ",
            "mn": "MN", "minneapolis": "MN",
            "nc": "NC", "charlotte": "NC",
            "va": "VA", "arlington": "VA",
        }
        for keyword, code in state_map.items():
            if keyword in city_lower:
                return code
        return None

    state_a = _state_code(city_a)
    state_b = _state_code(city_b)

    if not state_a or not state_b:
        return "State income tax comparison not available for one or both cities."

    a_notax = state_a in _NO_INCOME_TAX_STATES
    b_notax = state_b in _NO_INCOME_TAX_STATES

    if a_notax and b_notax:
        return (
            f"Both {state_a} and {state_b} have no state income tax, "
            "so this does not affect the comparison."
        )
    if a_notax and not b_notax:
        rate = _STATE_INCOME_TAX.get(state_b, 0.05) * 100
        return (
            f"{state_a} has no state income tax. {state_b} charges ~{rate:.1f}% — "
            "this makes the offer worth even less than the purchasing power calculation shows."
        )
    if not a_notax and b_notax:
        rate = _STATE_INCOME_TAX.get(state_a, 0.05) * 100
        return (
            f"{state_b} has no state income tax vs {state_a}'s ~{rate:.1f}% — "
            "the move actually improves your after-tax position beyond the COL calculation."
        )
    rate_a = _STATE_INCOME_TAX.get(state_a, 0.05) * 100
    rate_b = _STATE_INCOME_TAX.get(state_b, 0.05) * 100
    return (
        f"{state_a} taxes income at ~{rate_a:.1f}%, {state_b} at ~{rate_b:.1f}%. "
        "Factor this into your take-home pay comparison."
    )


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def calculate_down_payment_power(
    portfolio_value: float,
    target_cities: Optional[list[str]] = None,
) -> dict:
    """
    Calculates which housing markets a portfolio can fund at 20% down.

    Scenarios:
      full         = portfolio_value (liquidate everything)
      conservative = portfolio_value * 0.80 (keep 20% buffer)
      safe         = portfolio_value * 0.60 (maintain diversification)

    Args:
        portfolio_value: Total liquid portfolio value in USD.
        target_cities:   List of city names. Defaults to all 7 Austin ACTRIS markets.

    Returns:
        Dict with portfolio_value, down_payment_scenarios, markets list,
        top_recommendation, mortgage_assumptions, data_source.
    """
    full = portfolio_value
    conservative = round(portfolio_value * 0.80, 2)
    safe = round(portfolio_value * 0.60, 2)

    if target_cities is None:
        # Default: all 7 Austin ACTRIS markets (from _MOCK_SNAPSHOTS directly)
        city_keys = _DEFAULT_AUSTIN_MARKETS
        markets_data = [
            (key, _MOCK_SNAPSHOTS[key])
            for key in city_keys
            if key in _MOCK_SNAPSHOTS
        ]
    else:
        markets_data = []
        for city in target_cities:
            display, data = _resolve_city_data_sync(city)
            markets_data.append((city, data))

    markets_out = []
    affordable_markets = []

    for city_ref, snap in markets_data:
        price = snap.get("median_price") or snap.get("ListPrice") or 500_000
        rent = snap.get("MedianRentMonthly") or snap.get("median_rent") or 0
        area_name = snap.get("region") or snap.get("city") or city_ref
        ds = snap.get("data_source", "estimate")

        required_down_20 = round(price * 0.20, 2)
        can_full = full >= required_down_20
        can_conservative = conservative >= required_down_20
        can_safe = safe >= required_down_20

        monthly_payment = _monthly_payment(price)
        rent_vs_buy_diff = round(monthly_payment - rent, 0) if rent else None
        rent_vs_buy_verdict = (
            f"Buying costs ${abs(rent_vs_buy_diff):,.0f}/mo "
            f"{'more' if rent_vs_buy_diff > 0 else 'less'} than renting"
            if rent_vs_buy_diff is not None else "Rental data unavailable"
        )

        # Simple break-even: closing costs ~3% + transaction costs ~6% = ~9% of price
        # Break even = (9% of price) / monthly_savings_vs_rent
        monthly_savings = -(rent_vs_buy_diff or 1)
        if monthly_savings > 0 and rent_vs_buy_diff is not None:
            break_even_years = round((price * 0.09) / (monthly_savings * 12), 1)
        elif rent_vs_buy_diff is not None and rent_vs_buy_diff <= 0:
            break_even_years = 0.0  # Already cheaper to buy
        else:
            break_even_years = None

        entry = {
            "area": area_name,
            "city_ref": city_ref,
            "median_price": price,
            "required_down_20pct": required_down_20,
            "can_afford_full": can_full,
            "can_afford_conservative": can_conservative,
            "can_afford_safe": can_safe,
            "monthly_payment_estimate": int(monthly_payment),
            "median_rent": rent,
            "rent_vs_buy_monthly_diff": rent_vs_buy_diff,
            "rent_vs_buy_verdict": rent_vs_buy_verdict,
            "break_even_years": break_even_years,
            "data_source": ds,
        }
        markets_out.append(entry)

        if can_full:
            affordable_markets.append(area_name)

    # Build recommendation
    max_home_price = round(portfolio_value / 0.20, 0)
    affordable_conservatively = [
        m for m in markets_out if m["can_afford_conservative"]
    ]

    if not affordable_markets and not affordable_conservatively:
        recommendation = (
            f"Your ${portfolio_value:,.0f} portfolio covers 20% down on homes up to "
            f"${max_home_price:,.0f}. None of the target markets fall below this threshold. "
            "Consider markets in Caldwell County ($237,491) or increase savings before buying."
        )
    else:
        reachable_names = [m["area"] for m in affordable_conservatively] or affordable_markets
        recommendation = (
            f"Your ${portfolio_value:,.0f} portfolio could fund a 20% down payment on "
            f"homes up to ${max_home_price:,.0f}. "
            + (
                f"Reachable markets (conservatively): {', '.join(reachable_names[:3])}."
                if reachable_names else
                f"Reachable with full liquidation: {', '.join(affordable_markets[:3])}."
            )
        )

    return {
        "portfolio_value": portfolio_value,
        "down_payment_scenarios": {
            "full": full,
            "conservative": conservative,
            "safe": safe,
        },
        "markets": markets_out,
        "top_recommendation": recommendation,
        "mortgage_assumptions": {
            "rate": _MORTGAGE_RATE,
            "term_years": 30,
            "down_payment_pct": 20,
            "disclaimer": "Rate is an estimate (6.95% 30yr fixed). Verify with lender.",
        },
        "data_source": (
            "ACTRIS/Unlock MLS Jan 2026 (Austin areas) + Teleport API (other cities)"
        ),
    }


async def calculate_job_offer_affordability(
    offer_salary: float,
    offer_city: str,
    current_salary: float,
    current_city: str,
) -> dict:
    """
    Determines whether a job offer is a real raise in purchasing power terms.

    Works for any two cities worldwide:
      - Austin TX areas: uses ACTRIS COL index (real data)
      - All other cities: uses Teleport API live data (or fallback)

    Args:
        offer_salary:   Gross annual salary of the new offer, in USD.
        offer_city:     Destination city for the offer.
        current_salary: Current gross annual salary, in USD.
        current_city:   Current city of residence.

    Returns:
        Full comparison dict including adjusted purchasing power, verdict,
        break-even salary, state tax note, and housing cost comparison.
    """
    # Fetch city data (async for Teleport; sync-cached for Austin)
    async def _get_data(city: str) -> tuple[float, dict]:
        if _is_austin_area(city):
            city_key = _normalize_city(city)
            snap = _MOCK_SNAPSHOTS.get(city_key, {})
            col = _AUSTIN_COL_INDEX.get(city_key, 95.4)
            return col, snap
        data = await get_city_housing_data(city)
        col = _col_index_for_city(city, data)
        return col, data

    current_col, current_data = await _get_data(current_city)
    offer_col, offer_data = await _get_data(offer_city)

    # Core purchasing power calculation
    adjusted_offer = round(offer_salary * (current_col / offer_col), 2)
    real_raise = round(adjusted_offer - current_salary, 2)
    is_real_raise = real_raise > 0
    pct_change = round((real_raise / current_salary), 4) if current_salary > 0 else 0.0
    breakeven_salary = round(current_salary * (offer_col / current_col), 2)

    current_city_display = current_data.get("city") or current_city
    offer_city_display = offer_data.get("city") or offer_city

    # Housing comparison
    current_rent = (
        current_data.get("MedianRentMonthly")
        or current_data.get("median_rent")
        or 0
    )
    offer_rent = (
        offer_data.get("MedianRentMonthly")
        or offer_data.get("median_rent")
        or 0
    )
    rent_diff = round(offer_rent - current_rent, 0) if current_rent and offer_rent else None

    # Verdict
    if is_real_raise:
        verdict = (
            f"The {offer_city_display} offer is a REAL raise. "
            f"${offer_salary:,.0f}/yr in {offer_city_display} is worth "
            f"${adjusted_offer:,.0f} in {current_city_display} purchasing power terms — "
            f"a genuine ${real_raise:,.0f} improvement ({pct_change * 100:.1f}%)."
        )
    else:
        verdict = (
            f"Despite looking like a ${offer_salary - current_salary:,.0f} raise, "
            f"the {offer_city_display} offer is worth ${abs(real_raise):,.0f} LESS "
            f"than your {current_city_display} salary in real purchasing power. "
            f"You would need ${breakeven_salary:,.0f} in {offer_city_display} "
            f"to match your current lifestyle."
        )

    tax_note = _state_tax_note(current_city, offer_city)

    return {
        "current_salary": current_salary,
        "current_city": current_city_display,
        "current_col_index": current_col,
        "offer_salary": offer_salary,
        "offer_city": offer_city_display,
        "offer_col_index": offer_col,
        "adjusted_offer_in_current_city_terms": adjusted_offer,
        "real_raise_amount": real_raise,
        "is_real_raise": is_real_raise,
        "percentage_real_change": pct_change,
        "breakeven_salary_needed": breakeven_salary,
        "verdict": verdict,
        "tax_note": tax_note,
        "housing_comparison": {
            "current_city_median_rent": current_rent,
            "offer_city_median_rent": offer_rent,
            "monthly_rent_difference": rent_diff,
        },
        "data_source": (
            f"ACTRIS MLS (Austin areas) + Teleport API ({offer_city_display})"
        ),
        "offer_data_source": offer_data.get("data_source", ""),
        "current_data_source": current_data.get("data_source", ""),
    }


async def get_portfolio_real_estate_summary(
    target_cities: Optional[list[str]] = None,
) -> dict:
    """
    Master function: reads live Ghostfolio portfolio then runs down payment analysis.

    Steps:
      1. Calls portfolio_analysis to get total portfolio value and top holdings
      2. Passes total to calculate_down_payment_power() with target_cities
      3. Returns combined result with quick plain-English answer

    Args:
        target_cities: Optional list of cities to analyze. Defaults to all Austin markets.

    Returns:
        Combined dict with portfolio_summary, down_payment_analysis, quick_answer.
    """
    try:
        from portfolio import portfolio_analysis
    except ImportError:
        from agent.tools.portfolio import portfolio_analysis

    portfolio_result = await portfolio_analysis()

    portfolio_value = 0.0
    top_holdings: list[str] = []
    portfolio_error: Optional[str] = None

    if portfolio_result.get("success"):
        summary = portfolio_result.get("result", {}).get("summary", {})
        portfolio_value = summary.get("total_current_value_usd", 0.0)
        holdings = portfolio_result.get("result", {}).get("holdings", [])
        top_holdings = [
            h.get("symbol") or h.get("name", "")
            for h in holdings[:5]
            if h.get("symbol") or h.get("name")
        ]
    else:
        portfolio_error = portfolio_result.get("error", {}).get("message", "Unknown error")

    down_payment_analysis = calculate_down_payment_power(portfolio_value, target_cities)

    max_home_price = round(portfolio_value / 0.20, 0) if portfolio_value > 0 else 0
    affordable = [
        m for m in down_payment_analysis["markets"]
        if m["can_afford_conservative"]
    ]

    if portfolio_value == 0.0:
        quick_answer = (
            "Could not retrieve portfolio value. "
            + (f"Error: {portfolio_error}" if portfolio_error else "")
        )
    elif affordable:
        names = [m["area"] for m in affordable[:3]]
        quick_answer = (
            f"Your ${portfolio_value:,.0f} portfolio could fund a 20% down payment "
            f"on homes up to ${max_home_price:,.0f}. "
            f"Reachable markets: {', '.join(names)}."
        )
    else:
        quick_answer = (
            f"Your ${portfolio_value:,.0f} portfolio covers 20% down on homes up to "
            f"${max_home_price:,.0f}. Check Caldwell County at $237,491 — "
            "most affordable in the Austin area."
        )

    return {
        "portfolio_summary": {
            "total_value": portfolio_value,
            "top_holdings": top_holdings,
            "portfolio_error": portfolio_error,
            "allocation_note": (
                "Liquidating portfolio would trigger capital gains taxes — "
                "consult a financial advisor before using investments for a down payment."
            ),
        },
        "down_payment_analysis": down_payment_analysis,
        "quick_answer": quick_answer,
    }
