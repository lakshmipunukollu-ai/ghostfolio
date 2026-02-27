"""
Wealth Gap Visualizer
Compares actual net worth against Federal Reserve median wealth by age group.
Projects retirement income and shows what-if scenarios.
Source: Federal Reserve Survey of Consumer Finances 2022
"""

FED_WEALTH_DATA = {
    "under_35": {
        "median": 39000, "p25": 7000,
        "p75": 168000, "p90": 466000,
    },
    "35_to_44": {
        "median": 135000, "p25": 22000,
        "p75": 461000, "p90": 1100000,
    },
    "45_to_54": {
        "median": 247000, "p25": 43000,
        "p75": 791000, "p90": 1900000,
    },
    "55_to_64": {
        "median": 365000, "p25": 71000,
        "p75": 1200000, "p90": 2900000,
    },
    "65_to_74": {
        "median": 409000, "p25": 83000,
        "p75": 1380000, "p90": 3200000,
    },
}

SAVINGS_GRADES = {
    "exceptional": (0.30, "You are building wealth aggressively"),
    "excellent":   (0.20, "You are on track for most goals"),
    "good":        (0.15, "Solid progress"),
    "minimum":     (0.10, "Basic — consider increasing"),
    "critical":    (0.05, "Below recommended — increase urgently"),
    "low":         (0.0,  "Saving very little — prioritize this"),
}


def _get_age_bracket(age: int) -> str:
    if age < 35:
        return "under_35"
    elif age < 45:
        return "35_to_44"
    elif age < 55:
        return "45_to_54"
    elif age < 65:
        return "55_to_64"
    else:
        return "65_to_74"


def analyze_wealth_position(
    portfolio_value: float,
    age: int,
    annual_income: float,
    annual_savings: float = None,
    target_retirement_age: int = 65,
    real_estate_equity: float = 0,
) -> dict:
    """Compare net worth against Fed Reserve benchmarks and project retirement."""

    # Step 2: Total net worth
    total_net_worth = portfolio_value + real_estate_equity

    # Step 3: Percentile position
    bracket_key = _get_age_bracket(age)
    bracket = FED_WEALTH_DATA[bracket_key]

    if total_net_worth >= bracket["p90"]:
        position = "top 10%"
    elif total_net_worth >= bracket["p75"]:
        position = "75th-90th percentile"
    elif total_net_worth >= bracket["median"]:
        position = "50th-75th percentile"
    elif total_net_worth >= bracket["p25"]:
        position = "25th-50th percentile"
    else:
        position = "bottom 25%"

    diff_from_median = total_net_worth - bracket["median"]
    if diff_from_median >= 0:
        vs_median = f"+${diff_from_median:,.0f} above median"
    else:
        vs_median = f"${abs(diff_from_median):,.0f} below median"

    # Step 4: Savings analysis
    savings = annual_savings if annual_savings is not None else annual_income * 0.15
    savings_rate = savings / annual_income if annual_income > 0 else 0

    grade = "low"
    for g, (threshold, _) in SAVINGS_GRADES.items():
        if savings_rate >= threshold:
            grade = g
            break

    # Step 5: Retirement projection
    years = max(1, target_retirement_age - age)
    growth_rate = 0.07

    future_portfolio = portfolio_value * ((1 + growth_rate) ** years)
    future_savings = savings * (
        ((1 + growth_rate) ** years - 1) / growth_rate
    )
    total_at_retirement = future_portfolio + future_savings
    monthly_retirement_income = (total_at_retirement * 0.04) / 12

    # Step 6: What-if scenarios
    # Scenario 1: save 5% more
    extra_annual = annual_income * 0.05
    extra_future = extra_annual * (
        ((1 + growth_rate) ** years - 1) / growth_rate
    )
    extra_monthly = (extra_future * 0.04) / 12

    # Scenario 2: retire 5 years earlier
    years_early = max(1, years - 5)
    early_portfolio = portfolio_value * ((1 + growth_rate) ** years_early)
    early_savings_val = savings * (
        ((1 + growth_rate) ** years_early - 1) / growth_rate
    )
    early_monthly = ((early_portfolio + early_savings_val) * 0.04) / 12

    # Build honest assessment
    peer_clause = f"You are in the {position} for your age group."
    retirement_clause = (
        f"At your current savings rate, you can expect "
        f"${round(monthly_retirement_income):,}/mo at retirement."
    )
    honest_assessment = f"{peer_clause} {retirement_clause}"

    return {
        "current_position": {
            "age": age,
            "total_net_worth": total_net_worth,
            "portfolio_value": portfolio_value,
            "real_estate_equity": real_estate_equity,
            "vs_peers": position,
            "median_for_age": bracket["median"],
            "you_vs_median": vs_median,
            "percentile_estimate": position,
        },
        "savings_analysis": {
            "annual_savings_used": savings,
            "savings_rate": round(savings_rate, 3),
            "savings_grade": grade,
            "assessment": SAVINGS_GRADES[grade][1],
        },
        "retirement_projection": {
            "target_retirement_age": target_retirement_age,
            "years_to_retirement": years,
            "projected_total_at_retirement": round(total_at_retirement),
            "monthly_income_at_retirement": round(monthly_retirement_income),
            "assumptions": "7% annual growth, 4% withdrawal rate",
        },
        "what_if_scenarios": [
            {
                "scenario": "Save 5% more per year",
                "extra_monthly_at_retirement": round(extra_monthly),
                "description": (
                    f"Adding ${extra_annual:,.0f}/yr gives "
                    f"${round(extra_monthly):,} more per month at retirement"
                ),
            },
            {
                "scenario": f"Retire 5 years earlier (age {target_retirement_age - 5})",
                "monthly_income": round(early_monthly),
                "vs_normal_retirement": round(early_monthly - monthly_retirement_income),
            },
        ],
        "honest_assessment": honest_assessment,
        "data_source": "Federal Reserve Survey of Consumer Finances 2022",
    }
