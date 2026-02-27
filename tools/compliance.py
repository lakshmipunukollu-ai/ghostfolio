from datetime import datetime


async def compliance_check(portfolio_data: dict) -> dict:
    """
    Runs domain compliance rules against portfolio data — no external API call.
    Parameters:
        portfolio_data: result dict from portfolio_analysis tool
    Returns:
        warnings list with severity levels, overall status, holdings analyzed count
    Rules:
      1. Concentration risk: any holding > 20% of portfolio (allocation_pct field)
      2. Significant loss: any holding down > 15% (gain_pct field, already in %)
      3. Low diversification: fewer than 5 holdings
    """
    tool_result_id = f"compliance_{int(datetime.utcnow().timestamp())}"

    try:
        result = portfolio_data.get("result", {})
        holdings = result.get("holdings", [])

        warnings = []

        for holding in holdings:
            symbol = holding.get("symbol", "UNKNOWN")
            # allocation_pct is already in percentage points (e.g. 45.2 means 45.2%)
            alloc = holding.get("allocation_pct", 0) or 0
            # gain_pct is already in percentage points (e.g. -18.3 means -18.3%)
            gain_pct = holding.get("gain_pct", 0) or 0

            if alloc > 20:
                warnings.append({
                    "type": "CONCENTRATION_RISK",
                    "severity": "HIGH",
                    "symbol": symbol,
                    "allocation": f"{alloc:.1f}%",
                    "message": (
                        f"{symbol} represents {alloc:.1f}% of your portfolio — "
                        f"exceeds the 20% concentration threshold."
                    ),
                })

            if gain_pct < -15:
                warnings.append({
                    "type": "SIGNIFICANT_LOSS",
                    "severity": "MEDIUM",
                    "symbol": symbol,
                    "loss_pct": f"{gain_pct:.1f}%",
                    "message": (
                        f"{symbol} is down {abs(gain_pct):.1f}% — "
                        f"consider reviewing for tax-loss harvesting opportunities."
                    ),
                })

        if len(holdings) < 5:
            warnings.append({
                "type": "LOW_DIVERSIFICATION",
                "severity": "LOW",
                "holding_count": len(holdings),
                "message": (
                    f"Portfolio has only {len(holdings)} holding(s). "
                    f"Consider diversifying across more positions and asset classes."
                ),
            })

        return {
            "tool_name": "compliance_check",
            "success": True,
            "tool_result_id": tool_result_id,
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "local_rules_engine",
            "result": {
                "warnings": warnings,
                "warning_count": len(warnings),
                "overall_status": "FLAGGED" if warnings else "CLEAR",
                "holdings_analyzed": len(holdings),
            },
        }

    except Exception as e:
        return {
            "tool_name": "compliance_check",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "RULES_ENGINE_ERROR",
            "message": f"Compliance check failed: {str(e)}",
        }
