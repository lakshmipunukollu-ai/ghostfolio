"""
Relocation Runway Calculator
Answers: "How long until I feel financially stable if I move?"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from real_estate import MOCK_DATA as AUSTIN_DATA
except ImportError:
    AUSTIN_DATA = {}

try:
    from teleport_api import get_city_housing_data
    TELEPORT_AVAILABLE = True
except ImportError:
    TELEPORT_AVAILABLE = False

    def get_city_housing_data(city):
        return {"MedianRentMonthly": 2000, "median_price": 400000}


def estimate_take_home(annual_salary: float, city_name: str = "") -> float:
    if annual_salary <= 44725:
        federal_rate = 0.12
    elif annual_salary <= 95375:
        federal_rate = 0.22
    elif annual_salary <= 200000:
        federal_rate = 0.24
    else:
        federal_rate = 0.32

    fica = 0.0765

    no_income_tax = [
        "tx", "wa", "fl", "nv", "tn", "wy", "sd", "ak",
        "texas", "washington", "florida", "nevada",
        "tennessee", "wyoming", "south dakota", "alaska",
        "austin", "seattle", "miami", "nashville",
        "dallas", "houston", "san antonio",
    ]

    city_lower = city_name.lower()
    has_state_tax = not any(s in city_lower for s in no_income_tax)
    state_rate = 0.05 if has_state_tax else 0.0

    total_rate = federal_rate + fica + state_rate
    annual_take_home = annual_salary * (1 - total_rate)
    return annual_take_home / 12


def get_city_data_safe(city_name: str) -> dict:
    """Gets city data from ACTRIS for Austin areas, Teleport for everything else.
    Never crashes."""
    austin_keywords = [
        "austin", "travis", "williamson", "hays", "bastrop",
        "caldwell", "round rock", "cedar park", "georgetown",
        "kyle", "buda", "san marcos", "lockhart", "bastrop",
        "elgin", "leander", "pflugerville", "manor", "del valle",
    ]

    city_lower = city_name.lower()

    for keyword in austin_keywords:
        if keyword in city_lower:
            if any(k in city_lower for k in [
                "round rock", "cedar park", "georgetown", "leander", "williamson"
            ]):
                return AUSTIN_DATA.get(
                    "williamson_county",
                    {"MedianRentMonthly": 1995, "median_price": 403500},
                )
            elif any(k in city_lower for k in ["kyle", "buda", "san marcos", "wimberley", "hays"]):
                return AUSTIN_DATA.get(
                    "hays_county",
                    {"MedianRentMonthly": 1937, "median_price": 344500},
                )
            elif any(k in city_lower for k in ["bastrop", "elgin"]):
                return AUSTIN_DATA.get(
                    "bastrop_county",
                    {"MedianRentMonthly": 1860, "median_price": 335970},
                )
            elif any(k in city_lower for k in ["lockhart", "caldwell"]):
                return AUSTIN_DATA.get(
                    "caldwell_county",
                    {"MedianRentMonthly": 1750, "median_price": 237491},
                )
            else:
                return AUSTIN_DATA.get(
                    "austin",
                    {"MedianRentMonthly": 2100, "median_price": 522500},
                )

    if TELEPORT_AVAILABLE:
        try:
            import asyncio
            # get_city_housing_data is async — run it synchronously
            data = asyncio.run(get_city_housing_data(city_name))
            if data and "MedianRentMonthly" in data:
                return data
        except Exception:
            pass

    FALLBACK_RENTS = {
        "san francisco": {"MedianRentMonthly": 3200, "median_price": 1350000},
        "seattle": {"MedianRentMonthly": 2400, "median_price": 850000},
        "new york": {"MedianRentMonthly": 3800, "median_price": 750000},
        "denver": {"MedianRentMonthly": 1900, "median_price": 565000},
        "chicago": {"MedianRentMonthly": 1850, "median_price": 380000},
        "miami": {"MedianRentMonthly": 2800, "median_price": 620000},
        "boston": {"MedianRentMonthly": 3100, "median_price": 720000},
        "los angeles": {"MedianRentMonthly": 2900, "median_price": 950000},
        "nashville": {"MedianRentMonthly": 1800, "median_price": 450000},
        "dallas": {"MedianRentMonthly": 1700, "median_price": 380000},
        "london": {"MedianRentMonthly": 2800, "median_price": 720000},
        "toronto": {"MedianRentMonthly": 2300, "median_price": 980000},
        "sydney": {"MedianRentMonthly": 2600, "median_price": 1100000},
        "berlin": {"MedianRentMonthly": 1600, "median_price": 520000},
        "tokyo": {"MedianRentMonthly": 1800, "median_price": 650000},
        "paris": {"MedianRentMonthly": 2200, "median_price": 800000},
    }

    for key, val in FALLBACK_RENTS.items():
        if key in city_lower:
            return val

    return {
        "MedianRentMonthly": 2000,
        "median_price": 450000,
        "city": city_name,
        "data_source": "estimate",
    }


def calculate_relocation_runway(
    current_salary: float,
    offer_salary: float,
    current_city: str,
    destination_city: str,
    portfolio_value: float,
    current_savings_rate: float = 0.15,
) -> dict:
    """Calculate how long until financially stable after relocating."""

    # Step 1: Get city data
    dest_data = get_city_data_safe(destination_city)
    curr_data = get_city_data_safe(current_city)

    # Step 2: Monthly take-home
    dest_take_home = estimate_take_home(offer_salary, destination_city)
    curr_take_home = estimate_take_home(current_salary, current_city)

    # Step 3: Monthly costs
    def _monthly_costs(city_data: dict) -> tuple:
        rent = city_data.get("MedianRentMonthly", 2000)
        food_transport = rent * 0.8
        utilities_misc = rent * 0.3
        total = rent + food_transport + utilities_misc
        return rent, total

    dest_rent, dest_total_costs = _monthly_costs(dest_data)
    curr_rent, curr_total_costs = _monthly_costs(curr_data)

    # Step 4: Monthly surplus
    dest_surplus = dest_take_home - dest_total_costs
    curr_surplus = curr_take_home - curr_total_costs
    dest_surplus_warning = dest_surplus <= 0

    # Step 5: Milestones for destination
    dest_price = dest_data.get("ListPrice", dest_data.get("median_price", 500000))
    dest_down_payment = dest_price * 0.20
    dest_emergency_3mo = dest_total_costs * 3
    dest_emergency_6mo = dest_total_costs * 6
    portfolio_liquid = portfolio_value * 0.1
    portfolio_down = portfolio_value * 0.2

    if dest_surplus > 0:
        months_to_3mo_dest = int(max(0, (dest_emergency_3mo - portfolio_liquid) / dest_surplus))
        months_to_6mo_dest = int(max(0, (dest_emergency_6mo - portfolio_liquid) / dest_surplus))
        months_to_down_dest = int(max(0, (dest_down_payment - portfolio_down) / dest_surplus))
    else:
        months_to_3mo_dest = months_to_6mo_dest = months_to_down_dest = 9999

    # Step 6: Milestones for current city
    curr_price = curr_data.get("ListPrice", curr_data.get("median_price", 500000))
    curr_down_payment = curr_price * 0.20
    curr_emergency_3mo = curr_total_costs * 3
    curr_emergency_6mo = curr_total_costs * 6

    if curr_surplus > 0:
        months_to_3mo_curr = int(max(0, (curr_emergency_3mo - portfolio_liquid) / curr_surplus))
        months_to_6mo_curr = int(max(0, (curr_emergency_6mo - portfolio_liquid) / curr_surplus))
        months_to_down_curr = int(max(0, (curr_down_payment - portfolio_down) / curr_surplus))
    else:
        months_to_3mo_curr = months_to_6mo_curr = months_to_down_curr = 9999

    # Step 7: Build verdict
    salary_delta = offer_salary - current_salary
    salary_pct = (salary_delta / current_salary) * 100 if current_salary > 0 else 0
    surplus_delta = dest_surplus - curr_surplus

    if dest_surplus_warning:
        verdict = (
            f"Warning: The ${offer_salary:,.0f} offer in {destination_city} leaves you "
            f"with negative monthly surplus. The cost of living exceeds take-home pay."
        )
        key_insight = (
            f"You would need at least ${dest_total_costs * 12:,.0f}/yr just to cover "
            f"basic living costs in {destination_city}."
        )
    elif surplus_delta > 500:
        verdict = (
            f"Strong move: The {destination_city} offer gives you "
            f"${dest_surplus:,.0f}/mo surplus vs ${curr_surplus:,.0f}/mo now — "
            f"${surplus_delta:,.0f}/mo improvement."
        )
        key_insight = (
            f"Despite the higher cost of living, the {salary_pct:+.1f}% salary bump "
            f"in {destination_city} meaningfully improves your monthly runway."
        )
    elif surplus_delta > 0:
        verdict = (
            f"Marginal improvement: {destination_city} gives slightly more surplus "
            f"(${dest_surplus:,.0f}/mo vs ${curr_surplus:,.0f}/mo now)."
        )
        key_insight = (
            f"The salary increase is mostly absorbed by {destination_city}'s higher costs. "
            f"Negotiate for more before accepting."
        )
    elif surplus_delta > -300:
        verdict = (
            f"Roughly equivalent: {destination_city} surplus (${dest_surplus:,.0f}/mo) "
            f"is close to your current (${curr_surplus:,.0f}/mo)."
        )
        key_insight = (
            f"The {salary_pct:+.1f}% salary change is offset by {destination_city}'s cost "
            f"of living. Non-financial factors should decide this."
        )
    else:
        verdict = (
            f"Financial step back: Moving to {destination_city} reduces your monthly "
            f"surplus by ${abs(surplus_delta):,.0f}/mo."
        )
        key_insight = (
            f"The higher salary does not cover {destination_city}'s cost premium. "
            f"You would need ~${offer_salary - salary_delta + abs(surplus_delta) * 12:,.0f}/yr "
            f"to maintain your current financial position."
        )

    return {
        "scenario": {
            "current": {"city": current_city, "salary": current_salary},
            "offer": {"city": destination_city, "salary": offer_salary},
        },
        "destination_monthly": {
            "take_home": round(dest_take_home),
            "housing_cost": round(dest_rent),
            "total_living_costs": round(dest_total_costs),
            "monthly_surplus": round(dest_surplus),
            "monthly_surplus_warning": dest_surplus_warning,
        },
        "current_monthly": {
            "take_home": round(curr_take_home),
            "housing_cost": round(curr_rent),
            "total_living_costs": round(curr_total_costs),
            "monthly_surplus": round(curr_surplus),
        },
        "milestones_if_you_move": {
            "months_to_3mo_emergency_fund": months_to_3mo_dest,
            "months_to_6mo_emergency_fund": months_to_6mo_dest,
            "months_to_down_payment_20pct": months_to_down_dest,
            "down_payment_target": round(dest_down_payment),
            "destination_median_home_price": round(dest_price),
        },
        "milestones_if_you_stay": {
            "months_to_3mo_emergency_fund": months_to_3mo_curr,
            "months_to_6mo_emergency_fund": months_to_6mo_curr,
            "months_to_down_payment_20pct": months_to_down_curr,
            "down_payment_target": round(curr_down_payment),
            "current_median_home_price": round(curr_price),
        },
        "verdict": verdict,
        "key_insight": key_insight,
        "data_source": "ACTRIS MLS Jan 2026 (Austin) + Teleport API (global) + fallback estimates",
    }
