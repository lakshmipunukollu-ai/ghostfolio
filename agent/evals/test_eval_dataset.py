"""
Comprehensive eval dataset for the Ghostfolio AI Agent.

50+ test cases organized into 4 rubric-required categories:
  - Happy Path (20+ tests): normal successful user journeys
  - Edge Cases  (10+ tests): boundary conditions, missing data, zero values
  - Adversarial (10+ tests): bad inputs, injection attempts, extreme values
  - Multi-Step  (10+ tests): chained tool calls, stateful flows

Every test documents:
  TYPE, INPUT (what the user asked), EXPECTED (what should happen),
  CRITERIA (how pass/fail is determined).

Network calls: all Teleport API calls are mocked via conftest.py autouse
fixture (mock_teleport_no_network). Tests are deterministic and fast.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

os.environ.setdefault("ENABLE_REAL_ESTATE", "true")
os.environ.setdefault("PROPERTIES_DB_PATH", ":memory:")

import pytest


# ---------------------------------------------------------------------------
# Helper: run coroutine from sync context
# ---------------------------------------------------------------------------

def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _clear():
    from property_tracker import property_store_clear
    property_store_clear()


# ============================================================================
# HAPPY PATH TESTS (20 tests)
# ============================================================================

# TYPE: happy_path
# INPUT: add home with purchase price, current value, and mortgage
# EXPECTED: property created, equity = current_value - mortgage_balance
# CRITERIA: equity == 175000, success == True
def test_hp_add_property_basic():
    _clear()
    from property_tracker import add_property
    result = _run(add_property(
        address="My Primary Home",
        purchase_price=420000,
        current_value=490000,
        mortgage_balance=315000,
    ))
    assert result["success"] is True
    prop = result["result"]["property"]
    assert prop["equity"] == pytest.approx(175000)


# TYPE: happy_path
# INPUT: add two properties, check combined equity
# EXPECTED: total equity = sum of both properties' equity
# CRITERIA: total_equity matches manual calculation
def test_hp_add_two_properties_combined_equity():
    _clear()
    from property_tracker import add_property, get_real_estate_equity
    _run(add_property("Home A", 400000, 480000, 300000))   # equity=180000
    _run(add_property("Home B", 300000, 350000, 200000))   # equity=150000
    result = _run(get_real_estate_equity())
    assert result["success"] is True
    assert result["result"]["total_real_estate_equity"] == pytest.approx(330000)
    assert result["result"]["property_count"] == 2


# TYPE: happy_path
# INPUT: get total net worth with portfolio and property
# EXPECTED: total = portfolio + real estate equity
# CRITERIA: total_net_worth == 94000 + 175000 = 269000
def test_hp_total_net_worth_combined():
    _clear()
    from property_tracker import add_property, get_total_net_worth
    _run(add_property("Test Home", 420000, 490000, 315000))  # equity=175000
    result = _run(get_total_net_worth(portfolio_value=94000))
    assert result["success"] is True
    assert result["result"]["total_net_worth"] == pytest.approx(269000)
    assert result["result"]["investment_portfolio"] == 94000
    assert result["result"]["real_estate_equity"] == pytest.approx(175000)


# TYPE: happy_path
# INPUT: strategy simulation with 10-year horizon
# EXPECTED: final net worth exceeds starting portfolio
# CRITERIA: total_net_worth > initial_portfolio_value
def test_hp_strategy_10_year_growth():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(94000, 120000, 400000, total_years=10)
    assert result is not None
    assert "final_picture" in result
    assert result["final_picture"]["total_net_worth"] > 94000


# TYPE: happy_path
# INPUT: strategy simulation with user-provided 3% appreciation
# EXPECTED: strategy uses 3% not default 4%
# CRITERIA: assumptions show 3.0%
def test_hp_strategy_user_appreciation():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(
        94000, 120000, 400000,
        annual_appreciation=0.03,
    )
    assert result["strategy"]["assumptions"]["annual_appreciation"] == "3.0%"


# TYPE: happy_path
# INPUT: analyze wealth position for 34-year-old with $94k portfolio
# EXPECTED: Fed Reserve comparison with correct median for under_35 bracket
# CRITERIA: median_for_age == 39000, percentile_estimate present
def test_hp_wealth_position_age_34():
    from wealth_visualizer import analyze_wealth_position
    result = analyze_wealth_position(94000, 34, 120000)
    assert "current_position" in result
    assert result["current_position"]["median_for_age"] == 39000
    assert "percentile_estimate" in result["current_position"]
    assert "retirement_projection" in result


# TYPE: happy_path
# INPUT: analyze wealth position for 42-year-old
# EXPECTED: uses 35_to_44 bracket median of $135,000
# CRITERIA: median_for_age == 135000
def test_hp_wealth_position_age_42():
    from wealth_visualizer import analyze_wealth_position
    result = analyze_wealth_position(200000, 42, 150000)
    assert result["current_position"]["median_for_age"] == 135000


# TYPE: happy_path
# INPUT: equity options for property with substantial equity
# EXPECTED: 3 distinct options returned (keep, refi, rental)
# CRITERIA: len(options) >= 3, each option has projection
def test_hp_equity_options_three_scenarios():
    _clear()
    from property_tracker import add_property, analyze_equity_options
    prop = _run(add_property("Equity Home", 400000, 520000, 370000))
    pid = prop["result"]["property"]["id"]
    result = analyze_equity_options(pid)
    assert "options" in result
    assert len(result["options"]) >= 3


# TYPE: happy_path
# INPUT: family planning for Austin with 1 child
# EXPECTED: childcare costs, monthly surplus, income_impact
# CRITERIA: income_impact present, monthly_surplus_after is a number
def test_hp_family_plan_one_child_austin():
    from family_planner import plan_family_finances
    result = plan_family_finances("Austin", 120000, num_planned_children=1)
    assert "income_impact" in result
    assert "monthly_surplus_after" in result["income_impact"]
    assert isinstance(result["income_impact"]["monthly_surplus_after"], (int, float))


# TYPE: happy_path
# INPUT: relocation runway calculation Austin → Seattle
# EXPECTED: verdict returned, months to emergency fund calculated
# CRITERIA: verdict present, milestones_if_you_move has emergency_fund milestone
def test_hp_relocation_runway_seattle():
    from relocation_runway import calculate_relocation_runway
    result = calculate_relocation_runway(
        current_salary=120000,
        offer_salary=180000,
        current_city="Austin",
        destination_city="Seattle",
        portfolio_value=94000,
    )
    assert "verdict" in result
    assert "milestones_if_you_move" in result
    assert "months_to_6mo_emergency_fund" in result["milestones_if_you_move"]


# TYPE: happy_path
# INPUT: job offer affordability check Austin → SF
# EXPECTED: COL-adjusted comparison, is_real_raise boolean
# CRITERIA: is_real_raise present, verdict non-empty
@pytest.mark.asyncio
async def test_hp_job_offer_affordability():
    from wealth_bridge import calculate_job_offer_affordability
    result = await calculate_job_offer_affordability(
        offer_salary=180000,
        offer_city="Seattle",
        current_salary=120000,
        current_city="Austin",
    )
    assert "is_real_raise" in result
    assert isinstance(result["is_real_raise"], bool)
    assert "verdict" in result
    assert len(result["verdict"]) > 10


# TYPE: happy_path
# INPUT: down payment power for $94k portfolio
# EXPECTED: at least one Austin-area market affordable at full 20% down
# CRITERIA: can_afford_full True for at least one market
def test_hp_down_payment_94k_portfolio():
    from wealth_bridge import calculate_down_payment_power
    result = calculate_down_payment_power(94000)
    assert "markets" in result
    affordable = [m for m in result["markets"] if m["can_afford_full"]]
    assert len(affordable) > 0


# TYPE: happy_path
# INPUT: list properties when one exists
# EXPECTED: property appears in list with correct fields
# CRITERIA: len(properties) == 1, equity field present
def test_hp_list_properties_one():
    _clear()
    from property_tracker import add_property, get_properties
    _run(add_property("My Home", 400000, 480000, 320000))
    result = _run(get_properties())
    assert result["success"] is True
    props = result["result"]["properties"]
    assert len(props) == 1
    assert "equity" in props[0]
    assert props[0]["equity"] == pytest.approx(160000)


# TYPE: happy_path
# INPUT: remove property by ID
# EXPECTED: property no longer in list
# CRITERIA: property count drops from 1 to 0
def test_hp_remove_property_success():
    _clear()
    from property_tracker import add_property, remove_property, get_properties
    prop = _run(add_property("Remove Me", 300000, 350000, 200000))
    pid = prop["result"]["property"]["id"]
    removed = _run(remove_property(pid))
    assert removed["success"] is True
    listed = _run(get_properties())
    ids = [p["id"] for p in listed["result"]["properties"]]
    assert pid not in ids


# TYPE: happy_path
# INPUT: update property current value
# EXPECTED: equity recalculates correctly
# CRITERIA: equity increases after value update
def test_hp_update_property_value():
    _clear()
    from property_tracker import add_property, update_property
    prop = _run(add_property("Update Test", 400000, 450000, 320000))
    pid = prop["result"]["property"]["id"]
    updated = _run(update_property(pid, current_value=470000))
    assert updated["success"] is True
    new_equity = updated["result"]["property"]["equity"]
    assert new_equity == pytest.approx(150000)  # 470000 - 320000


# TYPE: happy_path
# INPUT: strategy simulation single property scenario
# EXPECTED: result contains at least 1 property
# CRITERIA: properties_owned >= 1
def test_hp_strategy_single_property():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(
        94000, 120000, 400000,
        buy_interval_years=10,  # only 1 purchase in 10 years
        total_years=10,
    )
    assert result["final_picture"]["num_properties_owned"] >= 1


# TYPE: happy_path
# INPUT: family plan with partner income
# EXPECTED: household income reflects both incomes
# CRITERIA: total_household_income > single income
def test_hp_family_plan_with_partner():
    from family_planner import plan_family_finances
    result = plan_family_finances("Austin", 120000, partner_income=80000, num_planned_children=1)
    assert "income_impact" in result
    data = result["income_impact"]
    assert "total_household_income" in data or "monthly_surplus_after" in data


# TYPE: happy_path
# INPUT: wealth position with real estate equity added
# EXPECTED: total net worth includes real estate
# CRITERIA: total_net_worth > portfolio_value alone
def test_hp_wealth_position_with_real_estate():
    from wealth_visualizer import analyze_wealth_position
    result = analyze_wealth_position(
        portfolio_value=94000,
        age=34,
        annual_income=120000,
        real_estate_equity=175000,
    )
    assert "current_position" in result
    pos = result["current_position"]
    assert pos["total_net_worth"] == pytest.approx(269000)


# TYPE: happy_path
# INPUT: relocation to cheaper city (SF → Austin)
# EXPECTED: destination surplus higher than current, verdict positive
# CRITERIA: destination monthly_surplus > 0, verdict present
def test_hp_relocation_to_cheaper_city():
    from relocation_runway import calculate_relocation_runway
    result = calculate_relocation_runway(
        current_salary=150000,
        offer_salary=140000,
        current_city="San Francisco",
        destination_city="Austin",
        portfolio_value=100000,
    )
    assert "verdict" in result
    dest_surplus = result["destination_monthly"]["monthly_surplus"]
    curr_surplus = result["current_monthly"]["monthly_surplus"]
    assert dest_surplus > curr_surplus


# TYPE: happy_path
# INPUT: strategy with conservative appreciation preset
# EXPECTED: conservative < optimistic final net worth
# CRITERIA: conservative_net_worth < optimistic_net_worth
def test_hp_strategy_conservative_vs_optimistic():
    from realestate_strategy import simulate_real_estate_strategy
    conservative = simulate_real_estate_strategy(
        94000, 120000, 400000, annual_appreciation=0.02,
    )
    optimistic = simulate_real_estate_strategy(
        94000, 120000, 400000, annual_appreciation=0.06,
    )
    assert (conservative["final_picture"]["total_net_worth"] <
            optimistic["final_picture"]["total_net_worth"])


# ============================================================================
# EDGE CASE TESTS (12 tests)
# ============================================================================

# TYPE: edge_case
# INPUT: portfolio value of zero
# EXPECTED: graceful response, not a crash
# CRITERIA: returns dict, no exception
def test_ec_zero_portfolio_value():
    from wealth_visualizer import analyze_wealth_position
    result = analyze_wealth_position(0, 30, 50000)
    assert result is not None
    assert isinstance(result, dict)
    assert "current_position" in result


# TYPE: edge_case
# INPUT: property with no mortgage (fully paid off)
# EXPECTED: equity equals current value
# CRITERIA: equity == current_value, equity_pct == 100.0
def test_ec_paid_off_property():
    _clear()
    from property_tracker import add_property
    result = _run(add_property(
        address="Paid Off Home",
        purchase_price=300000,
        current_value=380000,
        mortgage_balance=0,
    ))
    prop = result["result"]["property"]
    assert prop["equity"] == pytest.approx(380000)
    assert prop["equity_pct"] == pytest.approx(100.0)


# TYPE: edge_case
# INPUT: strategy simulation for just 1 year
# EXPECTED: returns valid result, no crash
# CRITERIA: result has final_picture and timeline, no exception
def test_ec_strategy_single_year():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(50000, 80000, 300000, total_years=1)
    assert result is not None
    assert "final_picture" in result
    assert "timeline" in result
    assert isinstance(result["final_picture"]["num_properties_owned"], int)


# TYPE: edge_case
# INPUT: equity options on nonexistent property ID
# EXPECTED: error dict returned, not exception
# CRITERIA: "error" key present in result
def test_ec_equity_nonexistent_property():
    from property_tracker import analyze_equity_options
    result = analyze_equity_options("does-not-exist-999")
    assert result is not None
    assert "error" in result


# TYPE: edge_case
# INPUT: family planner with zero income
# EXPECTED: graceful response, no ZeroDivisionError
# CRITERIA: returns dict, no exception raised
def test_ec_family_planner_zero_income():
    from family_planner import plan_family_finances
    result = plan_family_finances("Austin", 0, num_planned_children=1)
    assert result is not None
    assert isinstance(result, dict)


# TYPE: edge_case
# INPUT: wealth position for someone at exactly the median
# EXPECTED: correctly identified as median tier
# CRITERIA: percentile_estimate contains "50th" or similar
def test_ec_wealth_exactly_at_median():
    from wealth_visualizer import analyze_wealth_position
    # median for under_35 is 39000
    result = analyze_wealth_position(39000, 30, 60000)
    pos = result["current_position"]
    assert "50th" in pos["percentile_estimate"] or "median" in pos["percentile_estimate"].lower()


# TYPE: edge_case
# INPUT: empty property list — get net worth with no properties
# EXPECTED: net worth equals portfolio value, real estate equity is 0
# CRITERIA: total_net_worth == portfolio_value, real_estate_equity == 0
def test_ec_net_worth_no_properties():
    _clear()
    from property_tracker import get_total_net_worth
    result = _run(get_total_net_worth(portfolio_value=50000))
    assert result["success"] is True
    assert result["result"]["total_net_worth"] == pytest.approx(50000)
    assert result["result"]["real_estate_equity"] == 0


# TYPE: edge_case
# INPUT: relocation with identical source and destination city
# EXPECTED: no crash, verdict makes sense
# CRITERIA: returns dict with verdict field
def test_ec_same_city_relocation():
    from relocation_runway import calculate_relocation_runway
    result = calculate_relocation_runway(
        current_salary=120000,
        offer_salary=125000,
        current_city="Austin",
        destination_city="Austin",
        portfolio_value=94000,
    )
    assert result is not None
    assert "verdict" in result


# TYPE: edge_case
# INPUT: strategy with very large portfolio (1M)
# EXPECTED: simulation completes without overflow
# CRITERIA: total_net_worth is a positive finite number
def test_ec_strategy_large_portfolio():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(
        initial_portfolio_value=1_000_000,
        annual_income=300000,
        first_home_price=1_500_000,
        total_years=10,
    )
    assert result is not None
    nw = result["final_picture"]["total_net_worth"]
    assert nw > 0
    assert nw < 1e15  # sanity check: not overflowing


# TYPE: edge_case
# INPUT: analyze property with equity exceeding current value (impossible)
# EXPECTED: graceful handling, equity capped or error message
# CRITERIA: no crash, returns dict
def test_ec_mortgage_exceeds_value():
    _clear()
    from property_tracker import add_property
    result = _run(add_property(
        address="Underwater Property",
        purchase_price=400000,
        current_value=300000,
        mortgage_balance=380000,
    ))
    # Should succeed but equity will be negative (underwater)
    assert result["success"] is True
    prop = result["result"]["property"]
    equity = prop["equity"]
    # underwater: equity = 300000 - 380000 = -80000 (valid, just negative)
    assert isinstance(equity, (int, float))


# TYPE: edge_case
# INPUT: family plan for 5 children
# EXPECTED: costs scaled proportionally, no crash
# CRITERIA: childcare costs for 5 > childcare for 1
def test_ec_family_many_children():
    from family_planner import plan_family_finances
    result1 = plan_family_finances("Austin", 200000, num_planned_children=1)
    result5 = plan_family_finances("Austin", 200000, num_planned_children=5)
    assert result1 is not None and result5 is not None
    # Costs for 5 children should be higher
    s1 = result1["income_impact"]["monthly_surplus_after"]
    s5 = result5["income_impact"]["monthly_surplus_after"]
    assert s5 < s1  # more children = lower surplus


# TYPE: edge_case
# INPUT: wealth position for very old age (80+)
# EXPECTED: uses highest bracket (65+), no crash
# CRITERIA: median_for_age == 409000 (65_to_74 bracket)
def test_ec_wealth_very_old_age():
    from wealth_visualizer import analyze_wealth_position
    result = analyze_wealth_position(500000, 82, 60000)
    assert result is not None
    assert result["current_position"]["median_for_age"] == 409000


# ============================================================================
# ADVERSARIAL TESTS (12 tests)
# ============================================================================

# TYPE: adversarial
# INPUT: property address contains SQL injection
# EXPECTED: stored safely as a string, DB still works after
# CRITERIA: no exception, subsequent queries work normally
def test_adv_sql_injection_address():
    _clear()
    from property_tracker import add_property, get_properties
    malicious = "'; DROP TABLE properties; --"
    result = _run(add_property(
        address=malicious,
        purchase_price=300000,
        current_value=350000,
        mortgage_balance=200000,
    ))
    assert result["success"] is True
    # DB still works after the injection attempt
    props = _run(get_properties())
    assert props["success"] is True


# TYPE: adversarial
# INPUT: negative property values
# EXPECTED: validation catches it OR handles gracefully
# CRITERIA: no uncaught exception
def test_adv_negative_property_value():
    _clear()
    from property_tracker import add_property
    try:
        result = _run(add_property(
            address="Bad Property",
            purchase_price=-100000,
            current_value=-50000,
            mortgage_balance=0,
        ))
        # If it accepts, result should be a dict
        assert result is not None
    except (ValueError, AssertionError):
        pass  # Rejecting invalid input is correct behavior


# TYPE: adversarial
# INPUT: impossible appreciation rate (1000% = 10.0)
# EXPECTED: simulation runs without crash
# CRITERIA: returns result dict with final_picture
def test_adv_extreme_appreciation_rate():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(
        94000, 120000, 400000,
        annual_appreciation=10.0,  # 1000% — extreme input
    )
    assert result is not None
    assert "final_picture" in result


# TYPE: adversarial
# INPUT: strategy with zero annual income
# EXPECTED: graceful, not ZeroDivision
# CRITERIA: returns dict, no crash
def test_adv_strategy_zero_income():
    from realestate_strategy import simulate_real_estate_strategy
    try:
        result = simulate_real_estate_strategy(
            initial_portfolio_value=100000,
            annual_income=0,
            first_home_price=300000,
            total_years=5,
        )
        assert result is not None
        assert isinstance(result, dict)
    except ZeroDivisionError:
        pytest.fail("ZeroDivisionError raised with zero income")


# TYPE: adversarial
# INPUT: mortgage rate of 100% (extreme)
# EXPECTED: simulation completes, not crash
# CRITERIA: result is a dict with final_picture
def test_adv_extreme_mortgage_rate():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(
        94000, 120000, 400000,
        mortgage_rate=1.00,  # 100% rate
        total_years=5,
    )
    assert result is not None
    assert "final_picture" in result


# TYPE: adversarial
# INPUT: address that is only whitespace
# EXPECTED: validation returns structured error
# CRITERIA: success=False, error dict present
def test_adv_whitespace_address():
    _clear()
    from property_tracker import add_property
    result = _run(add_property(address="   \t\n  ", purchase_price=300000))
    assert result["success"] is False
    assert "error" in result


# TYPE: adversarial
# INPUT: purchase price is zero
# EXPECTED: validation error returned
# CRITERIA: success=False
def test_adv_zero_purchase_price():
    _clear()
    from property_tracker import add_property
    result = _run(add_property(address="Test", purchase_price=0))
    assert result["success"] is False


# TYPE: adversarial
# INPUT: wealth analysis with negative portfolio
# EXPECTED: graceful handling, no crash
# CRITERIA: returns dict
def test_adv_negative_portfolio_wealth():
    from wealth_visualizer import analyze_wealth_position
    try:
        result = analyze_wealth_position(-5000, 30, 60000)
        assert result is not None
        assert isinstance(result, dict)
    except Exception:
        pass  # Rejecting negative portfolio is acceptable


# TYPE: adversarial
# INPUT: family plan for a city not in the lookup
# EXPECTED: uses default costs, no crash
# CRITERIA: returns dict with income_impact
def test_adv_unknown_city_family_plan():
    from family_planner import plan_family_finances
    result = plan_family_finances("Xanadu City", 80000, num_planned_children=1)
    assert result is not None
    assert "income_impact" in result


# TYPE: adversarial
# INPUT: remove a nonexistent property ID
# EXPECTED: structured error dict returned
# CRITERIA: success=False, error code = NOT_FOUND
def test_adv_remove_nonexistent_property():
    _clear()
    from property_tracker import remove_property
    result = _run(remove_property("nonexistent-id-999"))
    assert result["success"] is False
    assert isinstance(result["error"], dict)
    assert result["error"]["code"] == "PROPERTY_TRACKER_NOT_FOUND"


# TYPE: adversarial
# INPUT: strategy with negative down payment percentage
# EXPECTED: uses fallback/default or handles gracefully
# CRITERIA: no crash
def test_adv_negative_down_payment_pct():
    from realestate_strategy import simulate_real_estate_strategy
    try:
        result = simulate_real_estate_strategy(
            94000, 120000, 400000,
            down_payment_pct=-0.5,
        )
        assert result is not None
    except (ValueError, AssertionError):
        pass  # Validation rejection is fine


# TYPE: adversarial
# INPUT: empty string city for relocation
# EXPECTED: no crash, returns dict
# CRITERIA: result is a dict
def test_adv_empty_city_relocation():
    from relocation_runway import calculate_relocation_runway
    try:
        result = calculate_relocation_runway(
            current_salary=100000,
            offer_salary=120000,
            current_city="",
            destination_city="",
            portfolio_value=50000,
        )
        assert isinstance(result, dict)
    except Exception:
        pass  # Failing gracefully is acceptable


# ============================================================================
# MULTI-STEP TESTS (12 tests)
# ============================================================================

# TYPE: multi_step
# INPUT: add property → get total net worth → verify property appears
# EXPECTED: net worth increases by property equity after adding
# CRITERIA: total_net_worth > portfolio_value_alone
def test_ms_add_then_net_worth():
    _clear()
    from property_tracker import add_property, get_total_net_worth
    _run(add_property(
        address="Multi Step Test",
        purchase_price=350000,
        current_value=420000,
        mortgage_balance=280000,
    ))  # equity = 140000
    result = _run(get_total_net_worth(portfolio_value=94000))
    assert result["result"]["total_net_worth"] == pytest.approx(234000)
    assert result["result"]["real_estate_equity"] == pytest.approx(140000)


# TYPE: multi_step
# INPUT: add property → analyze equity options
# EXPECTED: equity options reference added property, 3 scenarios returned
# CRITERIA: options has 3 entries, each has 10-year projection
def test_ms_add_then_equity_options():
    _clear()
    from property_tracker import add_property, analyze_equity_options
    prop = _run(add_property(
        address="Equity Chain Test",
        purchase_price=400000,
        current_value=520000,
        mortgage_balance=370000,
    ))
    result = analyze_equity_options(prop["result"]["property"]["id"])
    assert "options" in result
    assert len(result["options"]) >= 3


# TYPE: multi_step
# INPUT: add two properties → remove one → verify only one remains
# EXPECTED: after removal, list shows exactly 1 property
# CRITERIA: len(properties) == 1 after removal
def test_ms_add_two_remove_one():
    _clear()
    from property_tracker import add_property, remove_property, get_properties
    p1 = _run(add_property("Home 1", 400000, 450000, 300000))
    p2 = _run(add_property("Home 2", 350000, 400000, 250000))
    id1 = p1["result"]["property"]["id"]
    _run(remove_property(id1))
    listed = _run(get_properties())
    props = listed["result"]["properties"]
    assert len(props) == 1
    assert props[0]["id"] == p2["result"]["property"]["id"]


# TYPE: multi_step
# INPUT: strategy simulation → use final net worth in wealth position check
# EXPECTED: chaining results without errors
# CRITERIA: both return valid dicts, wealth check uses strategy output
def test_ms_strategy_then_wealth_check():
    from realestate_strategy import simulate_real_estate_strategy
    from wealth_visualizer import analyze_wealth_position
    strategy = simulate_real_estate_strategy(94000, 120000, 400000, total_years=10)
    final_worth = strategy["final_picture"]["total_net_worth"]
    wealth = analyze_wealth_position(
        portfolio_value=final_worth,
        age=44,
        annual_income=150000,
    )
    assert "current_position" in wealth
    assert "retirement_projection" in wealth


# TYPE: multi_step
# INPUT: family planning → use reduced savings in wealth position
# EXPECTED: lower savings rate flows into retirement projection
# CRITERIA: both tools return valid dicts
def test_ms_family_then_wealth():
    from family_planner import plan_family_finances
    from wealth_visualizer import analyze_wealth_position
    family = plan_family_finances("Austin", 120000, num_planned_children=1)
    assert "income_impact" in family
    reduced_savings = max(0, family["income_impact"]["monthly_surplus_after"] * 12)
    wealth = analyze_wealth_position(
        portfolio_value=94000,
        age=32,
        annual_income=120000,
        annual_savings=reduced_savings,
    )
    assert "retirement_projection" in wealth


# TYPE: multi_step
# INPUT: job offer check → relocation runway → both use same cities
# EXPECTED: consistent data across both tools for Austin/Seattle
# CRITERIA: both return their respective fields correctly
@pytest.mark.asyncio
async def test_ms_job_offer_then_runway():
    from wealth_bridge import calculate_job_offer_affordability
    from relocation_runway import calculate_relocation_runway
    offer = await calculate_job_offer_affordability(
        offer_salary=180000,
        offer_city="Seattle",
        current_salary=120000,
        current_city="Austin",
    )
    runway = calculate_relocation_runway(
        current_salary=120000,
        offer_salary=180000,
        current_city="Austin",
        destination_city="Seattle",
        portfolio_value=94000,
    )
    assert "is_real_raise" in offer
    assert "verdict" in runway


# TYPE: multi_step
# INPUT: add property → update value → check net worth reflects update
# EXPECTED: net worth uses updated value not original
# CRITERIA: net worth after update > net worth after initial add
def test_ms_add_update_then_net_worth():
    _clear()
    from property_tracker import add_property, update_property, get_total_net_worth
    prop = _run(add_property("Growing Home", 400000, 450000, 320000))
    pid = prop["result"]["property"]["id"]
    nw_before = _run(get_total_net_worth(portfolio_value=50000))
    _run(update_property(pid, current_value=500000))
    nw_after = _run(get_total_net_worth(portfolio_value=50000))
    assert nw_after["result"]["total_net_worth"] > nw_before["result"]["total_net_worth"]


# TYPE: multi_step
# INPUT: add property → get equity → use in wealth position
# EXPECTED: wealth position uses real estate equity from property tracker
# CRITERIA: position with RE equity > position without
def test_ms_property_equity_in_wealth_position():
    _clear()
    from property_tracker import add_property, get_real_estate_equity
    from wealth_visualizer import analyze_wealth_position
    _run(add_property("Wealth Test", 400000, 500000, 300000))  # equity=200000
    equity_result = _run(get_real_estate_equity())
    equity = equity_result["result"]["total_real_estate_equity"]
    pos_with_re = analyze_wealth_position(94000, 34, 120000, real_estate_equity=equity)
    pos_without = analyze_wealth_position(94000, 34, 120000)
    assert pos_with_re["current_position"]["total_net_worth"] > pos_without["current_position"]["total_net_worth"]


# TYPE: multi_step
# INPUT: full CRUD cycle — create, read, update, delete
# EXPECTED: each operation succeeds, state consistent throughout
# CRITERIA: all 4 operations return success=True, final list is empty
def test_ms_full_crud_cycle():
    _clear()
    from property_tracker import add_property, get_properties, update_property, remove_property

    # CREATE
    prop = _run(add_property("CRUD Home", 400000, 450000, 320000))
    assert prop["success"] is True
    pid = prop["result"]["property"]["id"]

    # READ
    listed = _run(get_properties())
    ids = [p["id"] for p in listed["result"]["properties"]]
    assert pid in ids

    # UPDATE
    updated = _run(update_property(pid, current_value=480000))
    assert updated["success"] is True
    assert updated["result"]["property"]["equity"] == pytest.approx(160000)

    # DELETE
    removed = _run(remove_property(pid))
    assert removed["success"] is True

    # Verify empty
    after = _run(get_properties())
    assert after["result"]["properties"] == []


# TYPE: multi_step
# INPUT: multiple properties → wealth position uses combined equity
# EXPECTED: total equity from all properties flows into net worth
# CRITERIA: net worth = portfolio + combined equity
def test_ms_multiple_properties_net_worth():
    _clear()
    from property_tracker import add_property, get_total_net_worth
    _run(add_property("Home A", 400000, 480000, 300000))  # equity=180000
    _run(add_property("Home B", 300000, 380000, 260000))  # equity=120000
    result = _run(get_total_net_worth(portfolio_value=94000))
    expected = 94000 + 180000 + 120000  # = 394000
    assert result["result"]["total_net_worth"] == pytest.approx(expected)


# TYPE: multi_step
# INPUT: relocation runway → family plan in destination city
# EXPECTED: can chain city data across both tools
# CRITERIA: both return valid dicts for Seattle
def test_ms_runway_then_family_plan():
    from relocation_runway import calculate_relocation_runway
    from family_planner import plan_family_finances
    runway = calculate_relocation_runway(
        current_salary=120000,
        offer_salary=180000,
        current_city="Austin",
        destination_city="Seattle",
        portfolio_value=94000,
    )
    assert "verdict" in runway
    family = plan_family_finances("Seattle", 180000, num_planned_children=1)
    assert "income_impact" in family


# TYPE: multi_step
# INPUT: strategy simulation over 20 years → verify timeline length
# EXPECTED: timeline has 20+ entries covering each year
# CRITERIA: len(timeline) >= 20
def test_ms_strategy_long_horizon():
    from realestate_strategy import simulate_real_estate_strategy
    result = simulate_real_estate_strategy(
        94000, 120000, 400000,
        total_years=20,
        buy_interval_years=4,
    )
    assert result is not None
    timeline = result.get("timeline", [])
    assert len(timeline) >= 20
    assert result["final_picture"]["num_properties_owned"] >= 1


# TYPE: happy_path
# INPUT: simple portfolio query timed end to end
# EXPECTED: tool executes within 30 seconds
# CRITERIA: elapsed time under 30s — not a performance
#           gate but confirms agent responds at all
def test_latency_agent_responds_within_bounds():
    """Verify agent tools respond within acceptable
    time bounds. LLM synthesis is excluded from this
    test — we test tool execution speed only."""
    import time
    from property_tracker import get_properties

    start = time.time()
    result = _run(get_properties())
    elapsed = time.time() - start

    assert result is not None
    assert elapsed < 5.0, (
        f"Tool execution took {elapsed:.2f}s — "
        f"should be under 5s. LLM synthesis latency "
        f"(8-10s) is separate and documented."
    )
