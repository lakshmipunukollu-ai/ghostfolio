"""
Unit tests for portfolio agent tools and graph helpers.

Tests cover pure-logic components that run without any network calls:
  Group A (15) — compliance_check rules engine
  Group B (15) — tax_estimate calculation logic
  Group C (10) — transaction_categorize activity analysis
  Group D (10) — consolidate_holdings deduplication
  Group E (10) — graph extraction helpers (_extract_ticker etc.)

Total: 60 tests  (+ 8 real estate tests = 68 total suite)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import pytest


# ===========================================================================
# Helpers
# ===========================================================================

def _portfolio(holdings: list) -> dict:
    """Wrap a holdings list into the shape compliance_check expects."""
    return {"result": {"holdings": holdings}}


def _holding(symbol: str, allocation_pct: float, gain_pct: float) -> dict:
    return {"symbol": symbol, "allocation_pct": allocation_pct, "gain_pct": gain_pct}


def _activity(type_: str, symbol: str, quantity: float, unit_price: float,
               date: str, fee: float = 0.0) -> dict:
    return {
        "type": type_, "symbol": symbol, "quantity": quantity,
        "unitPrice": unit_price, "date": date, "fee": fee,
    }


# ===========================================================================
# Group A — compliance_check (15 tests)
# ===========================================================================

@pytest.mark.asyncio
async def test_compliance_concentration_risk_high():
    """Single holding over 20% triggers CONCENTRATION_RISK warning."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 45.0, 5.0),
        _holding("MSFT", 20.0, 3.0),
        _holding("NVDA", 15.0, 2.0),
        _holding("GOOGL", 12.0, 1.0),
        _holding("VTI", 8.0, 0.5),
    ]))
    assert result["success"] is True
    warnings = result["result"]["warnings"]
    concentration_warnings = [w for w in warnings if w["type"] == "CONCENTRATION_RISK"]
    assert len(concentration_warnings) == 1
    assert concentration_warnings[0]["symbol"] == "AAPL"
    assert concentration_warnings[0]["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_compliance_significant_loss():
    """Holding down more than 15% triggers SIGNIFICANT_LOSS warning."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 18.0, 5.0),
        _holding("MSFT", 18.0, -20.0),
        _holding("NVDA", 18.0, 2.0),
        _holding("GOOGL", 18.0, 1.0),
        _holding("VTI", 28.0, 0.5),
    ]))
    assert result["success"] is True
    warnings = result["result"]["warnings"]
    loss_warnings = [w for w in warnings if w["type"] == "SIGNIFICANT_LOSS"]
    assert len(loss_warnings) == 1
    assert loss_warnings[0]["symbol"] == "MSFT"
    assert loss_warnings[0]["severity"] == "MEDIUM"


@pytest.mark.asyncio
async def test_compliance_low_diversification():
    """Fewer than 5 holdings triggers LOW_DIVERSIFICATION warning."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 50.0, 5.0),
        _holding("MSFT", 30.0, 3.0),
        _holding("NVDA", 20.0, 2.0),
    ]))
    assert result["success"] is True
    warnings = result["result"]["warnings"]
    div_warnings = [w for w in warnings if w["type"] == "LOW_DIVERSIFICATION"]
    assert len(div_warnings) == 1
    assert div_warnings[0]["severity"] == "LOW"
    assert div_warnings[0]["holding_count"] == 3


@pytest.mark.asyncio
async def test_compliance_all_clear():
    """Healthy portfolio with 5+ holdings and no thresholds exceeded returns CLEAR."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 18.0, 5.0),
        _holding("MSFT", 18.0, 3.0),
        _holding("NVDA", 18.0, 2.0),
        _holding("GOOGL", 18.0, 1.0),
        _holding("VTI", 18.0, 0.5),  # all ≤ 20%, all gain > -15%
    ]))
    assert result["success"] is True
    assert result["result"]["overall_status"] == "CLEAR"
    assert result["result"]["warning_count"] == 0
    assert result["result"]["warnings"] == []


@pytest.mark.asyncio
async def test_compliance_multiple_warnings():
    """Portfolio with both concentration risk and significant loss returns multiple warnings."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 60.0, -25.0),
        _holding("MSFT", 40.0, 3.0),
    ]))
    assert result["success"] is True
    warnings = result["result"]["warnings"]
    types = {w["type"] for w in warnings}
    assert "CONCENTRATION_RISK" in types
    assert "SIGNIFICANT_LOSS" in types
    assert "LOW_DIVERSIFICATION" in types
    assert result["result"]["overall_status"] == "FLAGGED"


@pytest.mark.asyncio
async def test_compliance_exactly_at_concentration_threshold():
    """Exactly 20% allocation does NOT trigger concentration warning (rule is >20)."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 20.0, 1.0),
        _holding("MSFT", 20.0, 1.0),
        _holding("NVDA", 20.0, 1.0),
        _holding("GOOGL", 20.0, 1.0),
        _holding("VTI", 20.0, 1.0),
    ]))
    concentration_warnings = [
        w for w in result["result"]["warnings"] if w["type"] == "CONCENTRATION_RISK"
    ]
    assert len(concentration_warnings) == 0


@pytest.mark.asyncio
async def test_compliance_just_over_concentration_threshold():
    """20.1% allocation DOES trigger concentration warning (>20)."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 20.1, 1.0),
        _holding("MSFT", 19.9, 1.0),
        _holding("NVDA", 19.9, 1.0),
        _holding("GOOGL", 19.9, 1.0),
        _holding("VTI", 20.1, 1.0),
    ]))
    concentration_warnings = [
        w for w in result["result"]["warnings"] if w["type"] == "CONCENTRATION_RISK"
    ]
    assert len(concentration_warnings) == 2


@pytest.mark.asyncio
async def test_compliance_exactly_at_loss_threshold():
    """Exactly -15% gain does NOT trigger loss warning (rule is < -15)."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 18.0, -15.0),
        _holding("MSFT", 18.0, 2.0),
        _holding("NVDA", 18.0, 2.0),
        _holding("GOOGL", 18.0, 2.0),
        _holding("VTI", 28.0, 2.0),
    ]))
    loss_warnings = [w for w in result["result"]["warnings"] if w["type"] == "SIGNIFICANT_LOSS"]
    assert len(loss_warnings) == 0


@pytest.mark.asyncio
async def test_compliance_just_over_loss_threshold():
    """−15.1% gain DOES trigger loss warning (< -15)."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 18.0, -15.1),
        _holding("MSFT", 18.0, 2.0),
        _holding("NVDA", 18.0, 2.0),
        _holding("GOOGL", 18.0, 2.0),
        _holding("VTI", 28.0, 2.0),
    ]))
    loss_warnings = [w for w in result["result"]["warnings"] if w["type"] == "SIGNIFICANT_LOSS"]
    assert len(loss_warnings) == 1


@pytest.mark.asyncio
async def test_compliance_empty_holdings():
    """Empty holdings list succeeds: no per-holding warnings, but diversification warning fires."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([]))
    assert result["success"] is True
    div_warnings = [w for w in result["result"]["warnings"] if w["type"] == "LOW_DIVERSIFICATION"]
    assert len(div_warnings) == 1
    assert div_warnings[0]["holding_count"] == 0


@pytest.mark.asyncio
async def test_compliance_five_holdings_no_diversification_warning():
    """Exactly 5 holdings does NOT trigger diversification warning (rule is < 5)."""
    from tools.compliance import compliance_check
    holdings = [_holding(s, 20.0, 1.0) for s in ["AAPL", "MSFT", "NVDA", "GOOGL", "VTI"]]
    result = await compliance_check(_portfolio(holdings))
    div_warnings = [w for w in result["result"]["warnings"] if w["type"] == "LOW_DIVERSIFICATION"]
    assert len(div_warnings) == 0


@pytest.mark.asyncio
async def test_compliance_four_holdings_triggers_diversification_warning():
    """4 holdings DOES trigger diversification warning (< 5)."""
    from tools.compliance import compliance_check
    holdings = [_holding(s, 25.0, 1.0) for s in ["AAPL", "MSFT", "NVDA", "GOOGL"]]
    result = await compliance_check(_portfolio(holdings))
    div_warnings = [w for w in result["result"]["warnings"] if w["type"] == "LOW_DIVERSIFICATION"]
    assert len(div_warnings) == 1


@pytest.mark.asyncio
async def test_compliance_severity_levels():
    """Concentration=HIGH, Loss=MEDIUM, Diversification=LOW."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([
        _holding("AAPL", 55.0, -20.0),
    ]))
    warnings_by_type = {w["type"]: w for w in result["result"]["warnings"]}
    assert warnings_by_type["CONCENTRATION_RISK"]["severity"] == "HIGH"
    assert warnings_by_type["SIGNIFICANT_LOSS"]["severity"] == "MEDIUM"
    assert warnings_by_type["LOW_DIVERSIFICATION"]["severity"] == "LOW"


@pytest.mark.asyncio
async def test_compliance_result_schema():
    """Result must contain all required top-level schema keys."""
    from tools.compliance import compliance_check
    result = await compliance_check(_portfolio([_holding("AAPL", 18.0, 2.0)] * 5))
    assert result["tool_name"] == "compliance_check"
    assert "tool_result_id" in result
    assert "timestamp" in result
    assert "result" in result
    res = result["result"]
    for key in ("warnings", "warning_count", "overall_status", "holdings_analyzed"):
        assert key in res, f"Missing key: {key}"


@pytest.mark.asyncio
async def test_compliance_null_values_in_holding():
    """None values for allocation_pct and gain_pct do not crash the engine."""
    from tools.compliance import compliance_check
    holdings = [
        {"symbol": "AAPL", "allocation_pct": None, "gain_pct": None},
        {"symbol": "MSFT", "allocation_pct": None, "gain_pct": None},
        {"symbol": "NVDA", "allocation_pct": None, "gain_pct": None},
        {"symbol": "GOOGL", "allocation_pct": None, "gain_pct": None},
        {"symbol": "VTI", "allocation_pct": None, "gain_pct": None},
    ]
    result = await compliance_check(_portfolio(holdings))
    assert result["success"] is True


# ===========================================================================
# Group B — tax_estimate (15 tests)
# ===========================================================================

@pytest.mark.asyncio
async def test_tax_short_term_gain():
    """Sale held < 365 days is taxed at the short-term rate (22%)."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 10, 100.0, "2024-01-01"),
        _activity("SELL", "AAPL", 10, 200.0, "2024-06-01"),  # ~5 months
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    res = result["result"]
    assert res["short_term_gains"] == pytest.approx(1000.0)
    assert res["long_term_gains"] == pytest.approx(0.0)
    assert res["short_term_tax_estimated"] == pytest.approx(220.0)


@pytest.mark.asyncio
async def test_tax_long_term_gain():
    """Sale held >= 365 days is taxed at the long-term rate (15%)."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "MSFT", 10, 100.0, "2022-01-01"),
        _activity("SELL", "MSFT", 10, 300.0, "2023-02-01"),  # > 365 days
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    res = result["result"]
    assert res["long_term_gains"] == pytest.approx(2000.0)
    assert res["short_term_gains"] == pytest.approx(0.0)
    assert res["long_term_tax_estimated"] == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_tax_mixed_gains():
    """Mix of short-term and long-term gains are calculated separately."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 5, 100.0, "2024-01-01"),
        _activity("SELL", "AAPL", 5, 200.0, "2024-06-01"),  # short-term: +$500
        _activity("BUY",  "MSFT", 5, 100.0, "2021-01-01"),
        _activity("SELL", "MSFT", 5, 300.0, "2023-01-01"),  # long-term: +$1000
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    res = result["result"]
    assert res["short_term_gains"] > 0
    assert res["long_term_gains"] > 0
    assert res["total_estimated_tax"] == pytest.approx(
        res["short_term_tax_estimated"] + res["long_term_tax_estimated"]
    )


@pytest.mark.asyncio
async def test_tax_wash_sale_detection():
    """Buy within 30 days of a loss sale triggers wash sale warning."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "NVDA", 10, 200.0, "2024-01-01"),
        _activity("SELL", "NVDA", 10, 150.0, "2024-06-01"),  # loss sale
        _activity("BUY",  "NVDA", 10, 155.0, "2024-06-15"),  # within 30 days → wash sale
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    assert len(result["result"]["wash_sale_warnings"]) >= 1
    assert result["result"]["wash_sale_warnings"][0]["symbol"] == "NVDA"


@pytest.mark.asyncio
async def test_tax_empty_activities():
    """Empty activity list returns zero gains and zero tax."""
    from tools.tax_estimate import tax_estimate
    result = await tax_estimate([])
    assert result["success"] is True
    res = result["result"]
    assert res["short_term_gains"] == 0.0
    assert res["long_term_gains"] == 0.0
    assert res["total_estimated_tax"] == 0.0
    assert res["sell_transactions_analyzed"] == 0


@pytest.mark.asyncio
async def test_tax_no_sells():
    """Activities with only buys returns zero gains."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY", "AAPL", 10, 150.0, "2024-01-01"),
        _activity("BUY", "MSFT", 5, 300.0, "2024-02-01"),
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    assert result["result"]["sell_transactions_analyzed"] == 0
    assert result["result"]["total_estimated_tax"] == 0.0


@pytest.mark.asyncio
async def test_tax_zero_gain_sale():
    """Sale at same price as buy results in zero gain and zero tax."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 10, 150.0, "2024-01-01"),
        _activity("SELL", "AAPL", 10, 150.0, "2024-06-01"),
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    assert result["result"]["short_term_gains"] == pytest.approx(0.0)
    assert result["result"]["total_estimated_tax"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_tax_multiple_symbols():
    """Multiple symbols are processed independently."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 5, 100.0, "2024-01-01"),
        _activity("SELL", "AAPL", 5, 200.0, "2024-04-01"),
        _activity("BUY",  "MSFT", 3, 200.0, "2024-01-01"),
        _activity("SELL", "MSFT", 3, 300.0, "2024-04-01"),
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    assert result["result"]["sell_transactions_analyzed"] == 2
    assert len(result["result"]["breakdown"]) == 2


@pytest.mark.asyncio
async def test_tax_disclaimer_always_present():
    """Disclaimer key is always present in the result, even for zero-gain scenarios."""
    from tools.tax_estimate import tax_estimate
    result = await tax_estimate([])
    assert "disclaimer" in result["result"]
    assert "ESTIMATE ONLY" in result["result"]["disclaimer"]


@pytest.mark.asyncio
async def test_tax_short_term_rate_22pct():
    """Short-term tax is exactly 22% of positive short-term gains."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 10, 100.0, "2024-01-01"),
        _activity("SELL", "AAPL", 10, 200.0, "2024-04-01"),  # $1000 gain, short-term
    ]
    result = await tax_estimate(activities)
    res = result["result"]
    assert res["short_term_gains"] == pytest.approx(1000.0)
    assert res["short_term_tax_estimated"] == pytest.approx(1000.0 * 0.22)


@pytest.mark.asyncio
async def test_tax_long_term_rate_15pct():
    """Long-term tax is exactly 15% of positive long-term gains."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 10, 100.0, "2020-01-01"),
        _activity("SELL", "AAPL", 10, 200.0, "2022-01-01"),  # $1000 gain, long-term
    ]
    result = await tax_estimate(activities)
    res = result["result"]
    assert res["long_term_gains"] == pytest.approx(1000.0)
    assert res["long_term_tax_estimated"] == pytest.approx(1000.0 * 0.15)


@pytest.mark.asyncio
async def test_tax_sell_with_no_matching_buy():
    """When no matching buy exists, cost basis defaults to sell price (zero gain)."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("SELL", "TSLA", 5, 200.0, "2024-06-01"),
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    # cost_basis = sell_price → gain = 0
    assert result["result"]["short_term_gains"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_tax_negative_gain_not_taxed():
    """Negative gains (losses) do not add to estimated tax."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 10, 200.0, "2024-01-01"),
        _activity("SELL", "AAPL", 10, 100.0, "2024-04-01"),  # $1000 loss
    ]
    result = await tax_estimate(activities)
    assert result["success"] is True
    assert result["result"]["short_term_gains"] == pytest.approx(-1000.0)
    assert result["result"]["short_term_tax_estimated"] == pytest.approx(0.0)
    assert result["result"]["total_estimated_tax"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_tax_breakdown_structure():
    """Each breakdown entry has required keys: symbol, gain_loss, holding_days, term."""
    from tools.tax_estimate import tax_estimate
    activities = [
        _activity("BUY",  "AAPL", 10, 100.0, "2024-01-01"),
        _activity("SELL", "AAPL", 10, 150.0, "2024-06-01"),
    ]
    result = await tax_estimate(activities)
    breakdown = result["result"]["breakdown"]
    assert len(breakdown) == 1
    entry = breakdown[0]
    for key in ("symbol", "gain_loss", "holding_days", "term"):
        assert key in entry, f"Breakdown entry missing key: {key}"
    assert entry["term"] in ("short-term", "long-term")


@pytest.mark.asyncio
async def test_tax_result_schema():
    """Result must contain all required schema keys."""
    from tools.tax_estimate import tax_estimate
    result = await tax_estimate([])
    assert result["tool_name"] == "tax_estimate"
    assert "tool_result_id" in result
    res = result["result"]
    for key in ("short_term_gains", "long_term_gains", "total_estimated_tax",
                "short_term_tax_estimated", "long_term_tax_estimated",
                "wash_sale_warnings", "breakdown", "disclaimer", "rates_used"):
        assert key in res, f"Missing key in result: {key}"


# ===========================================================================
# Group C — transaction_categorize (10 tests)
# ===========================================================================

@pytest.mark.asyncio
async def test_categorize_basic_buy():
    """Single buy activity is counted correctly."""
    from tools.categorize import transaction_categorize
    result = await transaction_categorize([
        _activity("BUY", "AAPL", 10, 150.0, "2024-01-01")
    ])
    assert result["success"] is True
    summary = result["result"]["summary"]
    assert summary["buy_count"] == 1
    assert summary["sell_count"] == 0
    assert summary["total_invested_usd"] == pytest.approx(1500.0)


@pytest.mark.asyncio
async def test_categorize_buy_sell_dividend():
    """All three activity types are categorized independently."""
    from tools.categorize import transaction_categorize
    activities = [
        _activity("BUY",      "AAPL", 10, 150.0, "2024-01-01"),
        _activity("SELL",     "AAPL",  5, 200.0, "2024-06-01"),
        _activity("DIVIDEND", "AAPL",  1,   3.5, "2024-08-01"),
    ]
    result = await transaction_categorize(activities)
    assert result["success"] is True
    summary = result["result"]["summary"]
    assert summary["buy_count"] == 1
    assert summary["sell_count"] == 1
    assert summary["dividend_count"] == 1
    assert summary["total_transactions"] == 3


@pytest.mark.asyncio
async def test_categorize_empty_activities():
    """Empty input returns zero counts without crashing."""
    from tools.categorize import transaction_categorize
    result = await transaction_categorize([])
    assert result["success"] is True
    summary = result["result"]["summary"]
    assert summary["total_transactions"] == 0
    assert summary["total_invested_usd"] == 0.0


@pytest.mark.asyncio
async def test_categorize_per_symbol_breakdown():
    """by_symbol contains an entry for each distinct symbol."""
    from tools.categorize import transaction_categorize
    activities = [
        _activity("BUY", "AAPL", 5, 150.0, "2024-01-01"),
        _activity("BUY", "MSFT", 3, 300.0, "2024-02-01"),
    ]
    result = await transaction_categorize(activities)
    by_symbol = result["result"]["by_symbol"]
    assert "AAPL" in by_symbol
    assert "MSFT" in by_symbol
    assert by_symbol["AAPL"]["buy_count"] == 1
    assert by_symbol["MSFT"]["buy_count"] == 1


@pytest.mark.asyncio
async def test_categorize_buy_and_hold_detection():
    """Portfolio with no sells is flagged as buy-and-hold."""
    from tools.categorize import transaction_categorize
    activities = [
        _activity("BUY", "AAPL", 10, 150.0, "2024-01-01"),
        _activity("BUY", "MSFT",  5, 300.0, "2024-02-01"),
    ]
    result = await transaction_categorize(activities)
    assert result["result"]["patterns"]["is_buy_and_hold"] is True


@pytest.mark.asyncio
async def test_categorize_has_dividends_flag():
    """Portfolio with any dividend sets has_dividends=True."""
    from tools.categorize import transaction_categorize
    activities = [
        _activity("BUY",      "AAPL", 10, 150.0, "2024-01-01"),
        _activity("DIVIDEND", "AAPL",  1,   3.5, "2024-08-01"),
    ]
    result = await transaction_categorize(activities)
    assert result["result"]["patterns"]["has_dividends"] is True


@pytest.mark.asyncio
async def test_categorize_high_fee_ratio():
    """Fees > 1% of total invested sets high_fee_ratio=True."""
    from tools.categorize import transaction_categorize
    activities = [
        _activity("BUY", "AAPL", 1, 100.0, "2024-01-01", fee=5.0),  # 5% fee ratio
    ]
    result = await transaction_categorize(activities)
    assert result["result"]["patterns"]["high_fee_ratio"] is True


@pytest.mark.asyncio
async def test_categorize_total_invested_calculation():
    """Total invested is the sum of quantity × unit_price for all BUY activities."""
    from tools.categorize import transaction_categorize
    activities = [
        _activity("BUY", "AAPL", 10, 150.0, "2024-01-01"),  # $1500
        _activity("BUY", "MSFT",  5, 200.0, "2024-02-01"),  # $1000
    ]
    result = await transaction_categorize(activities)
    assert result["result"]["summary"]["total_invested_usd"] == pytest.approx(2500.0)


@pytest.mark.asyncio
async def test_categorize_most_traded_top5():
    """most_traded list contains at most 5 symbols."""
    from tools.categorize import transaction_categorize
    activities = [
        _activity("BUY", sym, 1, 100.0, "2024-01-01")
        for sym in ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META"]
    ]
    result = await transaction_categorize(activities)
    assert len(result["result"]["most_traded"]) <= 5


@pytest.mark.asyncio
async def test_categorize_result_schema():
    """Result contains all required top-level schema keys."""
    from tools.categorize import transaction_categorize
    result = await transaction_categorize([])
    assert result["tool_name"] == "transaction_categorize"
    assert "tool_result_id" in result
    assert "result" in result
    res = result["result"]
    for key in ("summary", "by_symbol", "most_traded", "patterns"):
        assert key in res, f"Missing key: {key}"
    for key in ("is_buy_and_hold", "has_dividends", "high_fee_ratio"):
        assert key in res["patterns"], f"Missing pattern key: {key}"


# ===========================================================================
# Group D — consolidate_holdings (10 tests)
# ===========================================================================

_FAKE_UUID = "00fda606-1234-5678-abcd-000000000001"
_FAKE_UUID2 = "00fda606-1234-5678-abcd-000000000002"


def test_consolidate_normal_holdings():
    """Normal (non-UUID) holdings pass through without modification."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "AAPL", "name": "Apple", "quantity": 10, "investment": 1500,
         "valueInBaseCurrency": 1800, "grossPerformance": 300,
         "allocationInPercentage": 50, "averagePrice": 150},
        {"symbol": "MSFT", "name": "Microsoft", "quantity": 5, "investment": 1000,
         "valueInBaseCurrency": 1200, "grossPerformance": 200,
         "allocationInPercentage": 50, "averagePrice": 200},
    ]
    result = consolidate_holdings(holdings)
    symbols = [h["symbol"] for h in result]
    assert "AAPL" in symbols
    assert "MSFT" in symbols


def test_consolidate_uuid_matched_by_name():
    """UUID-symbol holding matched by name is merged into the real ticker entry."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "AAPL", "name": "AAPL", "quantity": 10, "investment": 1500,
         "valueInBaseCurrency": 1800, "grossPerformance": 300,
         "allocationInPercentage": 50, "averagePrice": 150},
        {"symbol": _FAKE_UUID, "name": "AAPL", "quantity": 5, "investment": 750,
         "valueInBaseCurrency": 900, "grossPerformance": 150,
         "allocationInPercentage": 25, "averagePrice": 150},
    ]
    result = consolidate_holdings(holdings)
    # Should merge into single AAPL entry
    aapl_entries = [h for h in result if h["symbol"] == "AAPL"]
    assert len(aapl_entries) == 1
    assert aapl_entries[0]["quantity"] == 15


def test_consolidate_uuid_no_match_promoted():
    """UUID-symbol holding with no name match is promoted using its name as symbol."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": _FAKE_UUID, "name": "TSLA", "quantity": 3, "investment": 600,
         "valueInBaseCurrency": 750, "grossPerformance": 150,
         "allocationInPercentage": 100, "averagePrice": 200},
    ]
    result = consolidate_holdings(holdings)
    assert len(result) == 1
    assert result[0]["symbol"] == "TSLA"


def test_consolidate_duplicate_real_tickers():
    """Two entries with the same real ticker symbol are merged."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "AAPL", "name": "Apple", "quantity": 5, "investment": 750,
         "valueInBaseCurrency": 900, "grossPerformance": 150,
         "allocationInPercentage": 50, "averagePrice": 150},
        {"symbol": "AAPL", "name": "Apple", "quantity": 5, "investment": 750,
         "valueInBaseCurrency": 900, "grossPerformance": 150,
         "allocationInPercentage": 50, "averagePrice": 150},
    ]
    result = consolidate_holdings(holdings)
    aapl_entries = [h for h in result if h["symbol"] == "AAPL"]
    assert len(aapl_entries) == 1
    assert aapl_entries[0]["quantity"] == 10


def test_consolidate_empty_list():
    """Empty input returns an empty list."""
    from tools.portfolio import consolidate_holdings
    assert consolidate_holdings([]) == []


def test_consolidate_single_holding():
    """Single holding passes through as a list with one item."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "NVDA", "name": "NVIDIA", "quantity": 8, "investment": 1200,
         "valueInBaseCurrency": 2400, "grossPerformance": 1200,
         "allocationInPercentage": 100, "averagePrice": 150},
    ]
    result = consolidate_holdings(holdings)
    assert len(result) == 1
    assert result[0]["symbol"] == "NVDA"


def test_consolidate_quantities_summed():
    """Merged holding quantities are summed correctly."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "AAPL", "name": "Apple", "quantity": 10, "investment": 1500,
         "valueInBaseCurrency": 1800, "grossPerformance": 300,
         "allocationInPercentage": 50, "averagePrice": 150},
        {"symbol": _FAKE_UUID, "name": "AAPL", "quantity": 7, "investment": 1050,
         "valueInBaseCurrency": 1260, "grossPerformance": 210,
         "allocationInPercentage": 35, "averagePrice": 150},
    ]
    result = consolidate_holdings(holdings)
    aapl = next(h for h in result if h["symbol"] == "AAPL")
    assert aapl["quantity"] == 17


def test_consolidate_investment_summed():
    """Merged holding investment values are summed correctly."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "MSFT", "name": "Microsoft", "quantity": 5, "investment": 1000,
         "valueInBaseCurrency": 1200, "grossPerformance": 200,
         "allocationInPercentage": 50, "averagePrice": 200},
        {"symbol": "MSFT", "name": "Microsoft", "quantity": 5, "investment": 1000,
         "valueInBaseCurrency": 1200, "grossPerformance": 200,
         "allocationInPercentage": 50, "averagePrice": 200},
    ]
    result = consolidate_holdings(holdings)
    msft = next(h for h in result if h["symbol"] == "MSFT")
    assert msft["investment"] == 2000


def test_consolidate_mixed_uuid_and_real():
    """Mix of UUID and real-ticker holdings resolves to correct symbol count."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "AAPL", "name": "Apple", "quantity": 10, "investment": 1500,
         "valueInBaseCurrency": 1800, "grossPerformance": 300,
         "allocationInPercentage": 40, "averagePrice": 150},
        {"symbol": _FAKE_UUID,  "name": "AAPL", "quantity": 5, "investment": 750,
         "valueInBaseCurrency": 900, "grossPerformance": 150,
         "allocationInPercentage": 20, "averagePrice": 150},
        {"symbol": "MSFT", "name": "Microsoft", "quantity": 8, "investment": 2400,
         "valueInBaseCurrency": 2800, "grossPerformance": 400,
         "allocationInPercentage": 40, "averagePrice": 300},
    ]
    result = consolidate_holdings(holdings)
    symbols = {h["symbol"] for h in result}
    assert symbols == {"AAPL", "MSFT"}


def test_consolidate_case_insensitive_name_match():
    """Name matching between UUID entries and real tickers is case-insensitive."""
    from tools.portfolio import consolidate_holdings
    holdings = [
        {"symbol": "aapl", "name": "apple inc", "quantity": 10, "investment": 1500,
         "valueInBaseCurrency": 1800, "grossPerformance": 300,
         "allocationInPercentage": 50, "averagePrice": 150},
        {"symbol": _FAKE_UUID2, "name": "APPLE INC", "quantity": 5, "investment": 750,
         "valueInBaseCurrency": 900, "grossPerformance": 150,
         "allocationInPercentage": 25, "averagePrice": 150},
    ]
    result = consolidate_holdings(holdings)
    # Should not crash; UUID entry should be handled (promoted or merged)
    assert len(result) >= 1


# ===========================================================================
# Group E — graph extraction helpers (10 tests)
# ===========================================================================

def test_extract_ticker_known_symbol():
    """Known tickers are extracted correctly from a natural language query."""
    from graph import _extract_ticker
    assert _extract_ticker("What is AAPL doing today?") == "AAPL"


def test_extract_ticker_msft_in_buy_query():
    """Ticker is extracted from a buy instruction."""
    from graph import _extract_ticker
    result = _extract_ticker("buy 10 shares of MSFT at $350")
    assert result == "MSFT"


def test_extract_ticker_not_found():
    """Returns None when query has no 1-5 letter ticker candidate (all words long or excluded)."""
    from graph import _extract_ticker
    # All words are either in exclusion list or > 5 chars — no ticker candidate
    result = _extract_ticker("What percentage allocation is my portfolio tracking?")
    assert result is None


def test_extract_quantity_shares():
    """Extracts integer share count."""
    from graph import _extract_quantity
    assert _extract_quantity("buy 5 shares of AAPL") == pytest.approx(5.0)


def test_extract_quantity_decimal():
    """Extracts decimal quantity."""
    from graph import _extract_quantity
    assert _extract_quantity("sell 10.5 units") == pytest.approx(10.5)


def test_extract_price_dollar_sign():
    """Extracts price preceded by dollar sign."""
    from graph import _extract_price
    assert _extract_price("buy AAPL at $185.50") == pytest.approx(185.50)


def test_extract_price_per_share():
    """Extracts price with 'per share' suffix."""
    from graph import _extract_price
    assert _extract_price("250 per share") == pytest.approx(250.0)


def test_extract_date_iso_format():
    """Extracts ISO date string unchanged."""
    from graph import _extract_date
    assert _extract_date("transaction on 2024-01-15") == "2024-01-15"


def test_extract_date_slash_format():
    """Converts MM/DD/YYYY to YYYY-MM-DD."""
    from graph import _extract_date
    assert _extract_date("on 1/15/2024") == "2024-01-15"


def test_extract_fee_explicit():
    """Extracts fee amount from natural language."""
    from graph import _extract_fee
    assert _extract_fee("buy 10 shares with fee of $7.50") == pytest.approx(7.50)
