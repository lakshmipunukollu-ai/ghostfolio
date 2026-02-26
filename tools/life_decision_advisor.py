"""
Life Decision Advisor
Orchestrates multiple financial tools into a single recommendation
for any major life decision: job offer, relocation, home purchase,
rent vs buy, or general financial guidance.
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from wealth_bridge import (
        calculate_job_offer_affordability,
        calculate_down_payment_power,
    )
    WEALTH_BRIDGE_AVAILABLE = True
except ImportError:
    WEALTH_BRIDGE_AVAILABLE = False

try:
    from relocation_runway import calculate_relocation_runway
    RUNWAY_AVAILABLE = True
except ImportError:
    RUNWAY_AVAILABLE = False

try:
    from wealth_visualizer import analyze_wealth_position
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False

try:
    from real_estate import get_neighborhood_snapshot
    RE_AVAILABLE = True
except ImportError:
    RE_AVAILABLE = False


def _run_async(coro):
    """Run an async coroutine from sync context safely."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(coro)
    except Exception:
        try:
            return asyncio.run(coro)
        except Exception as e:
            return {"error": str(e)}


def analyze_life_decision(decision_type: str, user_context: dict) -> dict:
    """
    Orchestrate all financial tools into a single recommendation.

    decision_type: "job_offer" | "relocation" | "home_purchase" |
                   "rent_or_buy" | "general"
    user_context: dict with optional keys:
        current_salary, offer_salary, current_city, destination_city,
        portfolio_value, age, annual_income, has_family, num_dependents,
        timeline_years, priority
    """
    ctx = user_context or {}
    tools_used = []
    data_sources = []
    results = {}

    # ── Job Offer decision ────────────────────────────────────────────────────
    if decision_type == "job_offer":
        current_salary = ctx.get("current_salary")
        offer_salary = ctx.get("offer_salary")
        current_city = ctx.get("current_city", "")
        destination_city = ctx.get("destination_city", "")
        portfolio_value = ctx.get("portfolio_value", 0)
        age = ctx.get("age")
        annual_income = ctx.get("annual_income", offer_salary or current_salary or 0)

        # COL comparison via wealth_bridge
        if (WEALTH_BRIDGE_AVAILABLE and current_salary and offer_salary
                and current_city and destination_city):
            try:
                col_result = _run_async(
                    calculate_job_offer_affordability(
                        current_salary=current_salary,
                        offer_salary=offer_salary,
                        current_city=current_city,
                        destination_city=destination_city,
                    )
                )
                if col_result and "error" not in col_result:
                    results["col"] = col_result
                    tools_used.append("wealth_bridge")
                    data_sources.append("Cost of living index")
            except Exception as e:
                results["col"] = {"error": str(e)}

        # Relocation runway
        if (RUNWAY_AVAILABLE and current_salary and offer_salary
                and current_city and destination_city):
            try:
                runway_result = calculate_relocation_runway(
                    current_salary=current_salary,
                    offer_salary=offer_salary,
                    current_city=current_city,
                    destination_city=destination_city,
                    portfolio_value=portfolio_value or 0,
                )
                if runway_result and "error" not in runway_result:
                    results["runway"] = runway_result
                    if "relocation_runway" not in tools_used:
                        tools_used.append("relocation_runway")
                    data_sources.append("ACTRIS MLS + Teleport API")
            except Exception as e:
                results["runway"] = {"error": str(e)}

        # Wealth position
        if VISUALIZER_AVAILABLE and age and portfolio_value:
            try:
                wealth_result = analyze_wealth_position(
                    portfolio_value=portfolio_value,
                    age=age,
                    annual_income=annual_income,
                )
                if wealth_result:
                    results["wealth"] = wealth_result
                    tools_used.append("wealth_visualizer")
                    data_sources.append("Federal Reserve SCF 2022")
            except Exception as e:
                results["wealth"] = {"error": str(e)}

        return _synthesize_job_offer(
            ctx, results, tools_used, data_sources
        )

    # ── Home Purchase decision ────────────────────────────────────────────────
    elif decision_type == "home_purchase":
        portfolio_value = ctx.get("portfolio_value", 0)
        current_city = ctx.get("current_city", "Austin")
        age = ctx.get("age")
        annual_income = ctx.get("annual_income", 0)

        if WEALTH_BRIDGE_AVAILABLE and portfolio_value:
            try:
                dp_result = calculate_down_payment_power(
                    portfolio_value=portfolio_value
                )
                if dp_result:
                    results["down_payment"] = dp_result
                    tools_used.append("wealth_bridge")
                    data_sources.append("ACTRIS MLS Jan 2026")
            except Exception as e:
                results["down_payment"] = {"error": str(e)}

        if VISUALIZER_AVAILABLE and age and annual_income:
            try:
                wealth_result = analyze_wealth_position(
                    portfolio_value=portfolio_value,
                    age=age,
                    annual_income=annual_income,
                )
                results["wealth"] = wealth_result
                tools_used.append("wealth_visualizer")
            except Exception as e:
                results["wealth"] = {"error": str(e)}

        return _synthesize_home_purchase(ctx, results, tools_used, data_sources)

    # ── Rent or Buy decision ──────────────────────────────────────────────────
    elif decision_type == "rent_or_buy":
        portfolio_value = ctx.get("portfolio_value", 0)
        current_city = ctx.get("current_city", "Austin")
        annual_income = ctx.get("annual_income", 0)

        if WEALTH_BRIDGE_AVAILABLE and portfolio_value:
            try:
                dp_result = calculate_down_payment_power(
                    portfolio_value=portfolio_value
                )
                results["down_payment"] = dp_result
                tools_used.append("wealth_bridge")
                data_sources.append("ACTRIS MLS Jan 2026")
            except Exception as e:
                results["down_payment"] = {"error": str(e)}

        return _synthesize_rent_or_buy(ctx, results, tools_used, data_sources)

    # ── Relocation decision ───────────────────────────────────────────────────
    elif decision_type == "relocation":
        current_salary = ctx.get("current_salary")
        offer_salary = ctx.get("offer_salary", current_salary)
        current_city = ctx.get("current_city", "")
        destination_city = ctx.get("destination_city", "")
        portfolio_value = ctx.get("portfolio_value", 0)

        if (RUNWAY_AVAILABLE and current_salary and current_city
                and destination_city):
            try:
                runway_result = calculate_relocation_runway(
                    current_salary=current_salary,
                    offer_salary=offer_salary,
                    current_city=current_city,
                    destination_city=destination_city,
                    portfolio_value=portfolio_value,
                )
                results["runway"] = runway_result
                tools_used.append("relocation_runway")
                data_sources.append("ACTRIS MLS + Teleport API")
            except Exception as e:
                results["runway"] = {"error": str(e)}

        return _synthesize_relocation(ctx, results, tools_used, data_sources)

    # ── General / unknown ─────────────────────────────────────────────────────
    else:
        return {
            "decision_type": "general",
            "summary": (
                "I can help you with any major financial life decision. "
                "Tell me what you're considering and I'll run the numbers."
            ),
            "message": (
                "Please share more context. I can help with: "
                "(1) Job offer evaluation — is it a real raise after cost of living? "
                "(2) Relocation planning — how long until you're financially stable? "
                "(3) Home purchase — can your portfolio cover a down payment? "
                "(4) Rent vs buy — what makes sense right now? "
                "Just describe your situation and I'll analyze it."
            ),
            "recommendation": (
                "Share your current salary, any offer details, and your city to get started."
            ),
            "financial_verdict": "Need more context",
            "confidence": "low",
            "key_numbers": {},
            "tradeoffs": [],
            "next_steps": [
                "Tell me your current salary and city",
                "Describe the decision you're facing",
                "Share your portfolio value if relevant",
            ],
            "tools_used": [],
            "data_sources": [],
        }


# ── Synthesis helpers ──────────────────────────────────────────────────────────

def _synthesize_job_offer(ctx, results, tools_used, data_sources):
    offer_salary = ctx.get("offer_salary", 0)
    current_salary = ctx.get("current_salary", 0)
    destination_city = ctx.get("destination_city", "destination city")
    current_city = ctx.get("current_city", "current city")

    # Extract key numbers
    key_numbers = {}
    tradeoffs = []
    verdict = "Need more context"
    confidence = "low"

    runway = results.get("runway")
    col = results.get("col")
    wealth = results.get("wealth")

    if runway and "error" not in runway:
        dest_monthly = runway.get("destination_monthly", {})
        curr_monthly = runway.get("current_monthly", {})
        dest_surplus = dest_monthly.get("monthly_surplus", 0)
        curr_surplus = curr_monthly.get("monthly_surplus", 0)
        surplus_delta = dest_surplus - curr_surplus

        key_numbers["destination_monthly_surplus"] = dest_surplus
        key_numbers["current_monthly_surplus"] = curr_surplus
        key_numbers["surplus_change"] = surplus_delta

        milestones = runway.get("milestones_if_you_move", {})
        months_down = milestones.get("months_to_down_payment_20pct", 9999)
        if months_down < 9999:
            key_numbers["months_to_down_payment"] = months_down

        if surplus_delta > 500:
            verdict = "Take it"
            confidence = "high"
            tradeoffs.append(f"PRO: ${surplus_delta:,.0f}/mo more surplus than now")
        elif surplus_delta > 0:
            verdict = "Negotiate"
            confidence = "medium"
            tradeoffs.append(f"NEUTRAL: Marginal improvement (${surplus_delta:,.0f}/mo more)")
        elif dest_monthly.get("monthly_surplus_warning"):
            verdict = "Pass"
            confidence = "high"
            tradeoffs.append("CON: Monthly costs exceed take-home pay at destination")
        else:
            verdict = "Negotiate"
            confidence = "medium"
            tradeoffs.append(f"CON: ${abs(surplus_delta):,.0f}/mo less surplus than now")

        tradeoffs.append(
            f"NEUTRAL: {destination_city} median home ${runway['milestones_if_you_move'].get('destination_median_home_price', 'N/A'):,}"
            if isinstance(runway['milestones_if_you_move'].get('destination_median_home_price'), (int, float))
            else f"NEUTRAL: Moving to {destination_city}"
        )

    if col and "error" not in col:
        is_real = col.get("is_real_raise", col.get("verdict", {}).get("is_real_raise"))
        if is_real is not None:
            key_numbers["is_real_raise"] = is_real
            if is_real:
                tradeoffs.append("PRO: Salary increase beats cost of living difference")
            else:
                tradeoffs.append("CON: Higher cost of living erodes salary increase")

    if wealth and "error" not in wealth:
        peer_pos = wealth.get("current_position", {}).get("vs_peers", "")
        if peer_pos:
            tradeoffs.append(f"NEUTRAL: You are currently {peer_pos} vs peers")

    salary_pct = ((offer_salary - current_salary) / current_salary * 100
                  if current_salary else 0)
    key_numbers["salary_increase_pct"] = round(salary_pct, 1)

    summary = (
        f"You have a {salary_pct:+.1f}% salary offer (${offer_salary:,} vs "
        f"${current_salary:,}) with a move from {current_city} to {destination_city}. "
    )
    if runway and "error" not in runway:
        summary += runway.get("verdict", "")

    recommendation = (
        f"Verdict: {verdict}. "
        + (runway.get("key_insight", "") if runway and "error" not in runway else
           f"Consider negotiating to at least ${int(current_salary * 1.15):,} to account for relocation costs.")
    )

    next_steps = [
        f"Calculate your exact take-home after {destination_city} taxes",
        "Negotiate relocation assistance and signing bonus",
        f"Research {destination_city} neighborhoods within your budget",
    ]

    return {
        "decision_type": "job_offer",
        "summary": summary,
        "financial_verdict": verdict,
        "confidence": confidence,
        "key_numbers": key_numbers,
        "tradeoffs": tradeoffs,
        "recommendation": recommendation,
        "next_steps": next_steps,
        "tools_used": tools_used,
        "data_sources": data_sources,
    }


def _synthesize_home_purchase(ctx, results, tools_used, data_sources):
    portfolio_value = ctx.get("portfolio_value", 0)
    current_city = ctx.get("current_city", "Austin")

    dp = results.get("down_payment", {})
    tradeoffs = []
    key_numbers = {}

    if dp and "error" not in dp:
        summary_data = dp.get("summary", dp)
        affordable = summary_data.get("homes_you_can_afford", [])
        if affordable:
            key_numbers["homes_in_range"] = len(affordable)
            tradeoffs.append(f"PRO: Portfolio can fund down payment on {len(affordable)} market segments")
        else:
            tradeoffs.append("CON: Portfolio may be thin for a down payment right now")

        liquid_available = summary_data.get("liquid_available_for_down_payment",
                          portfolio_value * 0.2)
        key_numbers["available_for_down_payment"] = round(liquid_available)

    tradeoffs.append("NEUTRAL: Owning builds equity; renting preserves flexibility")
    tradeoffs.append("CON: Transaction costs (3-6%) mean you need 3+ year horizon")

    verdict = "Consider it" if portfolio_value > 50000 else "Build savings first"
    confidence = "medium"

    return {
        "decision_type": "home_purchase",
        "summary": (
            f"With ${portfolio_value:,} in your portfolio, "
            f"you have options for a down payment in {current_city}."
        ),
        "financial_verdict": verdict,
        "confidence": confidence,
        "key_numbers": key_numbers,
        "tradeoffs": tradeoffs,
        "recommendation": (
            "A home purchase makes sense if you plan to stay 3+ years. "
            "Your portfolio gives you down payment flexibility — consider keeping "
            "20% in the market to avoid PMI while maintaining an emergency fund."
        ),
        "next_steps": [
            "Get pre-approved to understand your buying power",
            f"Research {current_city} neighborhoods in your price range",
            "Ensure 6-month emergency fund remains after down payment",
        ],
        "tools_used": tools_used,
        "data_sources": data_sources,
    }


def _synthesize_rent_or_buy(ctx, results, tools_used, data_sources):
    portfolio_value = ctx.get("portfolio_value", 0)
    current_city = ctx.get("current_city", "Austin")
    annual_income = ctx.get("annual_income", 0)

    dp = results.get("down_payment", {})
    tradeoffs = []
    key_numbers = {}

    if dp and "error" not in dp:
        summary_data = dp.get("summary", dp)
        liquid = summary_data.get("liquid_available_for_down_payment",
                portfolio_value * 0.2)
        key_numbers["down_payment_available"] = round(liquid)

    monthly_income = annual_income / 12 if annual_income else 0
    if monthly_income > 0:
        key_numbers["monthly_gross_income"] = round(monthly_income)

    tradeoffs.extend([
        "PRO (buy): Builds equity over time, fixed payment, tax benefits",
        "PRO (rent): Flexibility, lower upfront cost, no maintenance",
        "CON (buy): Illiquid, high transaction costs, market risk",
        "CON (rent): No equity growth, rent increases possible",
    ])

    verdict = (
        "Buy if staying 3+ years"
        if portfolio_value > 40000
        else "Rent and save first"
    )

    return {
        "decision_type": "rent_or_buy",
        "summary": (
            f"The rent vs buy decision in {current_city} depends on your timeline. "
            "With current mortgage rates, buying makes sense only if you plan to stay 3+ years."
        ),
        "financial_verdict": verdict,
        "confidence": "medium",
        "key_numbers": key_numbers,
        "tradeoffs": tradeoffs,
        "recommendation": (
            "In Austin's current market (rates ~7%), the break-even for buying vs renting "
            "is roughly 3-4 years. If you're staying longer, buying locks in your housing cost "
            "and builds equity. If uncertain about your timeline, renting preserves flexibility."
        ),
        "next_steps": [
            "Calculate your 5-year break-even (buy vs rent)",
            "Check if your portfolio can cover 20% down + 6mo emergency fund",
            "Compare total cost of ownership vs equivalent rent",
        ],
        "tools_used": tools_used,
        "data_sources": data_sources,
    }


def _synthesize_relocation(ctx, results, tools_used, data_sources):
    destination_city = ctx.get("destination_city", "destination")
    current_city = ctx.get("current_city", "current city")
    runway = results.get("runway", {})

    tradeoffs = []
    key_numbers = {}
    verdict = "Evaluate carefully"
    confidence = "medium"

    if runway and "error" not in runway:
        dest = runway.get("destination_monthly", {})
        curr = runway.get("current_monthly", {})
        surplus_delta = dest.get("monthly_surplus", 0) - curr.get("monthly_surplus", 0)
        key_numbers["monthly_surplus_change"] = round(surplus_delta)
        key_numbers["destination_monthly_surplus"] = dest.get("monthly_surplus", 0)

        milestones = runway.get("milestones_if_you_move", {})
        key_numbers["months_to_stability"] = milestones.get(
            "months_to_6mo_emergency_fund", "N/A"
        )

        if surplus_delta > 0:
            verdict = "Good move financially"
            confidence = "high"
            tradeoffs.append(f"PRO: ${surplus_delta:,.0f}/mo better financially")
        else:
            verdict = "Financial step back"
            confidence = "medium"
            tradeoffs.append(f"CON: ${abs(surplus_delta):,.0f}/mo worse financially")

        tradeoffs.append(
            f"NEUTRAL: {runway.get('key_insight', '')}"
        )

    return {
        "decision_type": "relocation",
        "summary": (
            f"Relocating from {current_city} to {destination_city}. "
            + (runway.get("verdict", "") if runway and "error" not in runway else "")
        ),
        "financial_verdict": verdict,
        "confidence": confidence,
        "key_numbers": key_numbers,
        "tradeoffs": tradeoffs,
        "recommendation": (
            runway.get("key_insight", f"Evaluate the full cost of living in {destination_city} "
                       "before committing to the relocation.")
            if runway and "error" not in runway
            else f"Research cost of living in {destination_city} before deciding."
        ),
        "next_steps": [
            f"Research specific neighborhoods in {destination_city}",
            "Negotiate relocation assistance from employer",
            "Build 3-month emergency fund before the move",
        ],
        "tools_used": tools_used,
        "data_sources": data_sources,
    }
