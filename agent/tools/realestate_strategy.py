"""
Real Estate Strategy Simulator

Simulates a multi-property buy-and-rent strategy over time using
user-provided assumptions. All rate parameters default to None —
users are encouraged to provide their own assumptions rather than
relying on generic defaults.

The defaults (appreciation=4%, rent yield=8%, etc.) are starting
points for exploration only. They are not predictions.
"""

from __future__ import annotations

from typing import Optional


def simulate_real_estate_strategy(
    initial_portfolio_value: float,
    annual_income: float,
    first_home_price: float,
    down_payment_pct: float = 0.20,
    buy_interval_years: int = 2,
    total_years: int = 10,
    annual_appreciation: Optional[float] = None,
    annual_rent_yield: Optional[float] = None,
    mortgage_rate: Optional[float] = None,
    annual_market_return: Optional[float] = None,
) -> dict:
    """
    Simulate buying a home every N years, renting previous ones.

    Parameters
    ----------
    initial_portfolio_value : float
        Starting investment portfolio value (e.g. 94000)
    annual_income : float
        Annual gross income used to estimate savings contributions
    first_home_price : float
        Purchase price of the first property
    down_payment_pct : float
        Down payment fraction (default 0.20 = 20%)
    buy_interval_years : int
        How many years between each property purchase
    total_years : int
        How many years to run the simulation
    annual_appreciation : float | None
        Annual home value appreciation rate. None → uses 0.04 default.
    annual_rent_yield : float | None
        Annual gross rent as fraction of property value. None → uses 0.08.
    mortgage_rate : float | None
        Annual mortgage interest rate. None → uses 0.0695 (current avg).
    annual_market_return : float | None
        Annual return on investment portfolio. None → uses 0.07.
    """

    # ── User-provided assumptions with sensible defaults ──────────────────────
    # Defaults are NOT predictions — they are starting points.
    # Users should adjust these to match their expectations.

    appreciation = annual_appreciation if annual_appreciation is not None else 0.04
    rent_yield = annual_rent_yield if annual_rent_yield is not None else 0.08
    rate = mortgage_rate if mortgage_rate is not None else 0.0695
    market_return = annual_market_return if annual_market_return is not None else 0.07

    # ── Mortgage helper ───────────────────────────────────────────────────────
    monthly_rate = rate / 12
    loan_term_months = 360  # 30-year fixed

    def monthly_payment(loan_amount: float) -> float:
        if loan_amount <= 0 or monthly_rate == 0:
            return 0.0
        return loan_amount * (
            monthly_rate * (1 + monthly_rate) ** loan_term_months
        ) / ((1 + monthly_rate) ** loan_term_months - 1)

    def remaining_balance(loan_amount: float, years_paid: int) -> float:
        """Outstanding mortgage balance after years_paid years."""
        if loan_amount <= 0 or monthly_rate == 0:
            return 0.0
        n = years_paid * 12
        return loan_amount * (
            (1 + monthly_rate) ** loan_term_months
            - (1 + monthly_rate) ** n
        ) / ((1 + monthly_rate) ** loan_term_months - 1)

    # ── Simulation ────────────────────────────────────────────────────────────
    portfolio = float(initial_portfolio_value)
    properties: list[dict] = []   # {purchase_year, price, loan, is_rental}
    timeline: list[dict] = []

    # Estimate annual savings as ~20% of income (rough rule of thumb)
    annual_savings = annual_income * 0.20

    next_buy_year = 0  # first purchase at year 0 (start)
    prop_num = 0

    for year in range(total_years + 1):
        # ── Buy a property this year? ─────────────────────────────────────────
        if year == next_buy_year:
            # Price grows with appreciation from first home price
            price = first_home_price * ((1 + appreciation) ** year)
            down = price * down_payment_pct
            loan = price - down

            if portfolio >= down:
                portfolio -= down
                # Mark previous property as rental
                if properties:
                    properties[-1]["is_rental"] = True

                properties.append({
                    "purchase_year": year,
                    "price": price,
                    "loan": loan,
                    "is_rental": False,
                })
                prop_num += 1
                next_buy_year = year + buy_interval_years

        # ── Grow portfolio ────────────────────────────────────────────────────
        portfolio = portfolio * (1 + market_return) + annual_savings

        # ── Compute current values ────────────────────────────────────────────
        total_re_equity = 0.0
        total_rental_income = 0.0
        total_mortgage_payments = 0.0

        prop_snapshots = []
        for p in properties:
            years_held = year - p["purchase_year"]
            current_value = p["price"] * ((1 + appreciation) ** years_held)
            bal = remaining_balance(p["loan"], years_held)
            equity = max(0.0, current_value - bal)
            total_re_equity += equity

            mpay = monthly_payment(p["loan"])
            annual_mpay = mpay * 12
            total_mortgage_payments += annual_mpay

            if p["is_rental"]:
                gross_rent = current_value * rent_yield
                net_rent = gross_rent * 0.65  # ~35% for expenses/vacancy
                total_rental_income += net_rent

            prop_snapshots.append({
                "purchase_year": p["purchase_year"],
                "current_value": round(current_value),
                "mortgage_balance": round(bal),
                "equity": round(equity),
                "is_rental": p["is_rental"],
                "annual_mortgage_payment": round(annual_mpay),
            })

        total_net_worth = portfolio + total_re_equity

        timeline.append({
            "year": year,
            "portfolio_value": round(portfolio),
            "total_real_estate_equity": round(total_re_equity),
            "total_net_worth": round(total_net_worth),
            "num_properties": len(properties),
            "annual_rental_income": round(total_rental_income),
            "annual_mortgage_payments": round(total_mortgage_payments),
            "properties": prop_snapshots,
        })

    final = timeline[-1]
    final_props = final["properties"]

    return {
        "strategy": {
            "buy_interval_years": buy_interval_years,
            "total_years": total_years,
            "properties_purchased": len(properties),
            "down_payment_pct": f"{down_payment_pct * 100:.0f}%",
            "assumptions": {
                "annual_appreciation": f"{appreciation * 100:.1f}%",
                "rent_yield": f"{rent_yield * 100:.1f}%",
                "mortgage_rate": f"{rate * 100:.2f}%",
                "market_return": f"{market_return * 100:.1f}%",
                "user_provided": annual_appreciation is not None,
                "note": (
                    "These are YOUR assumptions — not market predictions. "
                    "Adjust them to match your expectations. "
                    "Real estate performance varies by location, timing, "
                    "and economic conditions."
                ),
            },
        },
        "timeline": timeline,
        "final_picture": {
            "year": total_years,
            "investment_portfolio": final["portfolio_value"],
            "total_real_estate_equity": final["total_real_estate_equity"],
            "total_net_worth": final["total_net_worth"],
            "num_properties_owned": final["num_properties"],
            "annual_rental_income": final["annual_rental_income"],
            "properties": final_props,
        },
        "how_to_adjust": (
            "Want to see a different scenario? Try asking: "
            "'Run the same simulation but with 3% appreciation' "
            "or 'What if rent yield is only 6%?' "
            "or 'Show me a conservative scenario with 2% appreciation "
            "and 5% market return.'"
        ),
        "disclaimer": (
            "This projection uses the assumptions you provided. "
            "It is a planning tool, not a prediction. "
            "Real appreciation, rental rates, and investment returns "
            "vary significantly and cannot be guaranteed. "
            "Consult a licensed financial advisor before making "
            "real estate investment decisions."
        ),
    }
