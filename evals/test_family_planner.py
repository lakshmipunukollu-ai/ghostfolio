import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
from family_planner import plan_family_finances


def test_family_plan_austin_one_child():
    result = plan_family_finances(
        current_city="Austin",
        annual_income=120000,
        portfolio_value=94000,
        num_planned_children=1,
    )
    assert result is not None
    assert result["monthly_cost_breakdown"]["childcare_monthly"] > 0
    assert result["monthly_cost_breakdown"]["total_new_monthly_costs"] > 1000
    assert "honest_assessment" in result
    assert "alternatives" in result
    assert "is_feasible" in result["income_impact"]


def test_family_plan_two_children():
    result = plan_family_finances(
        current_city="Austin",
        annual_income=120000,
        partner_income=80000,
        num_planned_children=2,
    )
    one_child = plan_family_finances("Austin", 120000, num_planned_children=1)
    assert (
        result["monthly_cost_breakdown"]["childcare_monthly"]
        > one_child["monthly_cost_breakdown"]["childcare_monthly"]
    )


def test_family_plan_partner_reduces_hours():
    result = plan_family_finances(
        current_city="Austin",
        annual_income=150000,
        partner_income=80000,
        partner_work_reduction=0.5,
        num_planned_children=1,
    )
    assert result["monthly_cost_breakdown"]["income_reduction_monthly"] > 0


def test_family_plan_international_cheaper():
    result_berlin = plan_family_finances("Berlin", 120000, num_planned_children=1)
    result_austin = plan_family_finances("Austin", 120000, num_planned_children=1)
    assert (
        result_berlin["monthly_cost_breakdown"]["childcare_monthly"]
        < result_austin["monthly_cost_breakdown"]["childcare_monthly"]
    )


def test_family_plan_shows_alternatives():
    result = plan_family_finances("Austin", 120000, num_planned_children=1)
    assert "alternatives" in result
    # Austin should suggest Williamson County as cheaper
    assert len(result["alternatives"]) > 0


def test_family_plan_what_helps():
    result = plan_family_finances("Austin", 80000, num_planned_children=1)
    assert "what_helps" in result
    assert len(result["what_helps"]) > 0
    assert "disclaimer" in result
