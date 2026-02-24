TOOL_REGISTRY = {
    "portfolio_analysis": {
        "name": "portfolio_analysis",
        "description": (
            "Fetches holdings, allocation percentages, and performance metrics from Ghostfolio. "
            "Enriches each holding with live prices from Yahoo Finance."
        ),
        "parameters": {
            "date_range": "ytd | 1y | max | mtd | wtd",
            "token": "optional Ghostfolio bearer token",
        },
        "returns": "holdings list, allocation %, gain/loss %, total portfolio value, YTD performance",
    },
    "transaction_query": {
        "name": "transaction_query",
        "description": "Retrieves trade history filtered by symbol, type, or date from Ghostfolio.",
        "parameters": {
            "symbol": "optional ticker to filter (e.g. AAPL)",
            "limit": "max results to return (default 50)",
            "token": "optional Ghostfolio bearer token",
        },
        "returns": "list of activities with date, type, quantity, unitPrice, fee, currency",
    },
    "compliance_check": {
        "name": "compliance_check",
        "description": (
            "Runs domain rules against portfolio — concentration risk (>20%), "
            "significant loss flags (>15% down), and diversification check (<5 holdings)."
        ),
        "parameters": {
            "portfolio_data": "result dict from portfolio_analysis tool",
        },
        "returns": "warnings list with severity levels, overall_status (CLEAR/FLAGGED)",
    },
    "market_data": {
        "name": "market_data",
        "description": "Fetches live price and market metrics from Yahoo Finance.",
        "parameters": {
            "symbol": "ticker symbol e.g. AAPL, MSFT, SPY",
        },
        "returns": "current price, previous close, change_pct, currency, exchange",
    },
    "tax_estimate": {
        "name": "tax_estimate",
        "description": (
            "Estimates capital gains tax from sell activity history. "
            "Distinguishes short-term (22%) vs long-term (15%) rates. "
            "Checks for wash-sale rule violations. "
            "Always includes disclaimer: ESTIMATE ONLY — consult a tax professional."
        ),
        "parameters": {
            "activities": "list of activities from transaction_query",
            "additional_income": "optional float for other income context",
        },
        "returns": (
            "short_term_gains, long_term_gains, estimated tax, wash_sale_warnings, "
            "per-symbol breakdown, rates used, disclaimer"
        ),
    },
    "transaction_categorize": {
        "name": "transaction_categorize",
        "description": (
            "Categorizes transaction history into patterns: buy/sell/dividend/fee counts, "
            "most-traded symbols, total invested, total fees, trading style detection."
        ),
        "parameters": {
            "activities": "list of activities from transaction_query",
        },
        "returns": (
            "summary counts (buy/sell/dividend), by_symbol breakdown, "
            "most_traded top 5, patterns (buy-and-hold, dividends, high-fee-ratio)"
        ),
    },
    "market_overview": {
        "name": "market_overview",
        "description": "Fetches a quick snapshot of major indices and top tech stocks from Yahoo Finance.",
        "parameters": {},
        "returns": "list of symbols with current price and daily change %",
    },
}
