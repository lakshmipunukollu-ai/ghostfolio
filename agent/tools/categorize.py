import datetime


async def transaction_categorize(activities: list) -> dict:
    """
    Categorizes raw activity list into trading patterns and summaries.
    Parameters:
        activities: list of activity dicts from transaction_query (each has type, symbol,
                    quantity, unitPrice, fee, date fields)
    Returns:
        summary counts, per-symbol breakdown, most-traded top 5, and pattern flags
        (is_buy_and_hold, has_dividends, high_fee_ratio)
    """
    tool_result_id = f"categorize_{int(datetime.datetime.utcnow().timestamp())}"

    try:
        categories: dict[str, list] = {
            "BUY": [], "SELL": [], "DIVIDEND": [],
            "FEE": [], "INTEREST": [],
        }
        total_invested = 0.0
        total_fees = 0.0
        by_symbol: dict[str, dict] = {}

        for activity in activities:
            atype = activity.get("type", "BUY")
            symbol = activity.get("symbol") or "UNKNOWN"
            quantity = activity.get("quantity") or 0
            unit_price = activity.get("unitPrice") or 0
            value = quantity * unit_price
            fee = activity.get("fee") or 0

            if atype in categories:
                categories[atype].append(activity)
            else:
                categories.setdefault(atype, []).append(activity)

            total_fees += fee

            if symbol not in by_symbol:
                by_symbol[symbol] = {
                    "buy_count": 0,
                    "sell_count": 0,
                    "dividend_count": 0,
                    "total_invested": 0.0,
                }

            if atype == "BUY":
                total_invested += value
                by_symbol[symbol]["buy_count"] += 1
                by_symbol[symbol]["total_invested"] += value
            elif atype == "SELL":
                by_symbol[symbol]["sell_count"] += 1
            elif atype == "DIVIDEND":
                by_symbol[symbol]["dividend_count"] += 1

        most_traded = sorted(
            by_symbol.items(),
            key=lambda x: x[1]["buy_count"],
            reverse=True,
        )

        return {
            "tool_name": "transaction_categorize",
            "success": True,
            "tool_result_id": tool_result_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "result": {
                "summary": {
                    "total_transactions": len(activities),
                    "total_invested_usd": round(total_invested, 2),
                    "total_fees_usd": round(total_fees, 2),
                    "buy_count": len(categories.get("BUY", [])),
                    "sell_count": len(categories.get("SELL", [])),
                    "dividend_count": len(categories.get("DIVIDEND", [])),
                },
                "by_symbol": {
                    sym: {**data, "total_invested": round(data["total_invested"], 2)}
                    for sym, data in by_symbol.items()
                },
                "most_traded": [
                    {"symbol": s, **d, "total_invested": round(d["total_invested"], 2)}
                    for s, d in most_traded[:5]
                ],
                "patterns": {
                    "is_buy_and_hold": len(categories.get("SELL", [])) == 0,
                    "has_dividends": len(categories.get("DIVIDEND", [])) > 0,
                    "high_fee_ratio": (total_fees / max(total_invested, 1)) > 0.01,
                },
            },
        }

    except Exception as e:
        return {
            "tool_name": "transaction_categorize",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "CATEGORIZE_ERROR",
            "message": f"Transaction categorization failed: {str(e)}",
        }
