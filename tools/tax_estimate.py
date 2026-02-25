from datetime import datetime


async def tax_estimate(activities: list, additional_income: float = 0) -> dict:
    """
    Estimates capital gains tax from sell activity history — no external API call.
    Parameters:
        activities: list of activity dicts from transaction_query
        additional_income: optional float for supplemental income context (unused in calculation)
    Returns:
        short_term_gains, long_term_gains, estimated taxes at 22%/15% rates,
        wash_sale_warnings, per-symbol breakdown, disclaimer
    Distinguishes short-term (<365 days held) at 22% vs long-term (>=365 days) at 15%.
    Detects potential wash-sale violations (same symbol bought within 30 days of a loss sale).
    ALWAYS includes disclaimer: ESTIMATE ONLY — not tax advice.
    """
    tool_result_id = f"tax_{int(datetime.utcnow().timestamp())}"

    try:
        today = datetime.utcnow()
        short_term_gains = 0.0
        long_term_gains = 0.0
        wash_sale_warnings = []
        breakdown = []

        sells = [a for a in activities if a.get("type") == "SELL"]
        buys = [a for a in activities if a.get("type") == "BUY"]

        for sell in sells:
            symbol = sell.get("symbol") or sell.get("SymbolProfile", {}).get("symbol", "UNKNOWN")
            raw_date = sell.get("date", today.isoformat())
            sell_date = datetime.fromisoformat(str(raw_date)[:10])
            sell_price = sell.get("unitPrice") or 0
            quantity = sell.get("quantity") or 0

            matching_buys = [b for b in buys if (b.get("symbol") or "") == symbol]
            if matching_buys:
                cost_basis = matching_buys[0].get("unitPrice") or sell_price
                buy_raw = matching_buys[0].get("date", today.isoformat())
                buy_date = datetime.fromisoformat(str(buy_raw)[:10])
            else:
                cost_basis = sell_price
                buy_date = sell_date

            gain = (sell_price - cost_basis) * quantity
            holding_days = max(0, (sell_date - buy_date).days)

            if holding_days >= 365:
                long_term_gains += gain
            else:
                short_term_gains += gain

            # Wash-sale check: bought same stock within 30 days of selling at a loss
            if gain < 0:
                recent_buys = [
                    b for b in buys
                    if (b.get("symbol") or "") == symbol
                    and abs(
                        (datetime.fromisoformat(str(b.get("date", today.isoformat()))[:10]) - sell_date).days
                    ) <= 30
                ]
                if recent_buys:
                    wash_sale_warnings.append({
                        "symbol": symbol,
                        "warning": (
                            f"Possible wash sale — bought {symbol} within 30 days of selling "
                            f"at a loss. This loss may be disallowed by IRS rules."
                        ),
                    })

            breakdown.append({
                "symbol": symbol,
                "gain_loss": round(gain, 2),
                "holding_days": holding_days,
                "term": "long-term" if holding_days >= 365 else "short-term",
            })

        short_term_tax = max(0.0, short_term_gains) * 0.22
        long_term_tax = max(0.0, long_term_gains) * 0.15
        total_estimated_tax = short_term_tax + long_term_tax

        return {
            "tool_name": "tax_estimate",
            "success": True,
            "tool_result_id": tool_result_id,
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "local_tax_engine",
            "result": {
                "disclaimer": "ESTIMATE ONLY — not tax advice. Consult a qualified tax professional.",
                "sell_transactions_analyzed": len(sells),
                "short_term_gains": round(short_term_gains, 2),
                "long_term_gains": round(long_term_gains, 2),
                "short_term_tax_estimated": round(short_term_tax, 2),
                "long_term_tax_estimated": round(long_term_tax, 2),
                "total_estimated_tax": round(total_estimated_tax, 2),
                "wash_sale_warnings": wash_sale_warnings,
                "breakdown": breakdown,
                "rates_used": {"short_term": "22%", "long_term": "15%"},
                "note": (
                    "Short-term = held <365 days (22% rate). "
                    "Long-term = held >=365 days (15% rate). "
                    "Does not account for state taxes, AMT, or tax-loss offsets."
                ),
            },
        }

    except Exception as e:
        return {
            "tool_name": "tax_estimate",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "CALCULATION_ERROR",
            "message": f"Tax estimate calculation failed: {str(e)}",
        }
