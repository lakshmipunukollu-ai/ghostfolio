"""
Family Financial Planner
Models the financial impact of having children for any city worldwide.
Source: US Dept of Labor + Care.com 2024 averages
"""

CHILDCARE_ANNUAL = {
    "san francisco": 31000, "san-francisco": 31000,
    "seattle": 26000,
    "new york": 29000, "new-york": 29000, "nyc": 29000,
    "boston": 28000,
    "washington dc": 27000, "dc": 27000,
    "los angeles": 24000, "la": 24000,
    "chicago": 22000,
    "portland": 22000,
    "denver": 20000,
    "minneapolis": 20000,
    "austin": 18000,
    "travis county": 18000,
    "atlanta": 18000,
    "miami": 19000,
    "nashville": 17000,
    "raleigh": 17000,
    "williamson county": 16000,
    "round rock": 16000,
    "cedar park": 16000,
    "dallas": 16000,
    "houston": 16000,
    "hays county": 15000,
    "san marcos": 15000,
    "kyle": 15000,
    "phoenix": 15000,
    "bastrop county": 14000,
    "caldwell county": 13000,
    "lockhart": 13000,
    "london": 22000,
    "toronto": 18000,
    "sydney": 16000,
    "berlin": 4000,
    "paris": 5000,
    "tokyo": 8000,
    "amsterdam": 6000,
    "stockholm": 5000,
    "default": 18000,
}


def _estimate_monthly_take_home(annual_salary: float, city: str = "") -> float:
    if annual_salary <= 44725:
        federal = 0.12
    elif annual_salary <= 95375:
        federal = 0.22
    elif annual_salary <= 200000:
        federal = 0.24
    else:
        federal = 0.32
    fica = 0.0765
    no_tax = [
        "tx", "wa", "fl", "nv", "tn", "wy", "sd", "ak",
        "texas", "washington", "florida", "austin", "seattle",
        "dallas", "houston", "nashville", "miami",
    ]
    state = 0.0 if any(s in city.lower() for s in no_tax) else 0.05
    return (annual_salary * (1 - federal - fica - state)) / 12


def plan_family_finances(
    current_city: str,
    annual_income: float,
    partner_income: float = 0,
    portfolio_value: float = 0,
    num_planned_children: int = 1,
    timeline_years: int = 5,
    partner_work_reduction: float = 0.0,
) -> dict:
    """Model the financial impact of having children."""

    city_lower = current_city.lower()

    # Step 1: Get childcare cost
    annual_childcare = CHILDCARE_ANNUAL.get("default", 18000)
    for key in CHILDCARE_ANNUAL:
        if key in city_lower or city_lower in key:
            annual_childcare = CHILDCARE_ANNUAL[key]
            break
    monthly_childcare = (annual_childcare / 12) * num_planned_children

    # Step 2: Get median rent for city
    RENT_LOOKUP = {
        "austin": 2100, "travis": 2100,
        "williamson": 1995, "round rock": 1995,
        "hays": 1937, "san marcos": 1937,
        "bastrop": 1860, "caldwell": 1750,
        "seattle": 2400, "san francisco": 3200,
        "new york": 3800, "boston": 3100,
        "denver": 1900, "chicago": 1850,
        "miami": 2800, "nashville": 1800,
        "los angeles": 2900, "dallas": 1700,
        "london": 2800, "tokyo": 1800,
        "berlin": 1600, "paris": 2200,
    }
    rent = 2000
    for key, val in RENT_LOOKUP.items():
        if key in city_lower:
            rent = val
            break

    # Step 3: Calculate income
    total_income = annual_income + partner_income
    reduced_partner = partner_income * (1 - partner_work_reduction)
    effective_income = annual_income + reduced_partner
    income_reduction = partner_income - reduced_partner

    # Step 4: Monthly financials
    take_home_before = _estimate_monthly_take_home(total_income, current_city)
    take_home_after = _estimate_monthly_take_home(effective_income, current_city)

    food_clothing = 800 * num_planned_children
    healthcare = 300 * num_planned_children
    family_rent = rent * 1.3

    total_new_costs = monthly_childcare + food_clothing + healthcare

    surplus_before = take_home_before - (rent * 1.8)
    surplus_after = take_home_after - (family_rent * 1.6) - total_new_costs

    # Step 5: Income needed to maintain current surplus
    current_surplus = take_home_before - (rent * 1.8)
    income_needed = effective_income
    test_income = effective_income
    while True:
        test_take_home = _estimate_monthly_take_home(test_income, current_city)
        test_surplus = test_take_home - (family_rent * 1.6) - total_new_costs
        if test_surplus >= current_surplus or test_income > 500000:
            income_needed = test_income
            break
        test_income += 5000

    # Step 6: Alternatives (cheaper nearby option for Austin users)
    alternatives = []
    if "austin" in city_lower or "travis" in city_lower:
        wilco_childcare = CHILDCARE_ANNUAL.get("williamson county", 16000)
        wilco_rent = 1995
        savings = (
            (annual_childcare - wilco_childcare) / 12
            + (rent - wilco_rent)
        )
        if savings > 0:
            alternatives.append({
                "option": "Move to Williamson County",
                "monthly_savings": round(savings),
                "note": f"Saves ~${savings:,.0f}/mo vs Austin City",
            })

    # Step 7: International comparison
    intl = {
        "austin": annual_childcare,
        "berlin": CHILDCARE_ANNUAL["berlin"],
        "paris": CHILDCARE_ANNUAL["paris"],
        "stockholm": CHILDCARE_ANNUAL.get("stockholm", 5000),
        "note": "Western Europe has heavily subsidized childcare",
    }

    # Honest assessment
    if surplus_after > 0:
        honest_assessment = (
            f"Having {num_planned_children} child(ren) in {current_city} adds "
            f"~${round(total_new_costs):,}/mo in costs. "
            f"You would have ${round(surplus_after):,}/mo surplus after family expenses — "
            f"this is financially feasible."
        )
    else:
        shortfall = abs(round(surplus_after))
        honest_assessment = (
            f"Having {num_planned_children} child(ren) in {current_city} adds "
            f"~${round(total_new_costs):,}/mo in costs. "
            f"Your current income leaves a ${shortfall:,}/mo shortfall after family expenses. "
            f"You'd need ~${income_needed:,}/yr combined income to maintain your current lifestyle."
        )

    return {
        "family_plan": {
            "city": current_city,
            "num_children": num_planned_children,
            "timeline_years": timeline_years,
        },
        "monthly_cost_breakdown": {
            "childcare_monthly": round(monthly_childcare),
            "food_clothing_misc": round(food_clothing),
            "healthcare_increase": round(healthcare),
            "housing_increase_for_space": round(family_rent - rent),
            "total_new_monthly_costs": round(total_new_costs),
            "income_reduction_monthly": round(income_reduction / 12),
        },
        "income_impact": {
            "take_home_before_kids": round(take_home_before),
            "take_home_after_kids": round(take_home_after),
            "monthly_surplus_before": round(surplus_before),
            "monthly_surplus_after": round(surplus_after),
            "is_feasible": surplus_after > 0,
            "income_needed_to_maintain_surplus": round(income_needed),
        },
        "honest_assessment": honest_assessment,
        "alternatives": alternatives,
        "what_helps": [
            f"Family member childcare eliminates ${round(monthly_childcare):,}/mo in costs",
            "Nanny share splits childcare cost ~50%",
            "Employer childcare benefits (check your benefits package)",
            "Dependent Care FSA saves taxes on up to $5,000/yr",
        ],
        "international_comparison": intl,
        "disclaimer": (
            "Cost estimates vary significantly by provider. "
            "Actual costs depend on childcare type and location."
        ),
        "data_source": "US Dept of Labor + Care.com 2024 averages",
    }
