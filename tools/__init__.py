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
    # --- Real Estate tools (feature-flagged: ENABLE_REAL_ESTATE=true) ---
    "real_estate_neighborhood": {
        "name": "real_estate_neighborhood",
        "description": (
            "Returns housing market statistics for a US city or neighborhood: "
            "median price, price/sqft, days on market, YoY price change, "
            "inventory level, walk score, and rental yield estimate. "
            "Requires ENABLE_REAL_ESTATE=true."
        ),
        "parameters": {
            "location": "city or neighborhood name (e.g. 'Austin', 'San Francisco', 'Denver')",
        },
        "returns": (
            "median_price, price_per_sqft, median_days_on_market, "
            "price_change_yoy_pct, inventory_level, walk_score, "
            "gross_rental_yield_pct, market_summary"
        ),
    },
    "real_estate_search": {
        "name": "real_estate_search",
        "description": (
            "Searches active real estate listings by city or neighborhood. "
            "Returns up to 5 normalized listings with price, bedrooms, sqft, "
            "days on market, estimated rent, and cap rate. "
            "Requires ENABLE_REAL_ESTATE=true."
        ),
        "parameters": {
            "query": "city or neighborhood name (e.g. 'Austin TX', 'Seattle', 'New York')",
        },
        "returns": "list of listings: id, address, price, bedrooms, bathrooms, sqft, DOM, cap_rate",
    },
    "real_estate_compare": {
        "name": "real_estate_compare",
        "description": (
            "Compares two US cities or neighborhoods side by side on affordability, "
            "rental yield, walkability, price trend, and inventory. "
            "Ideal for questions like 'compare Austin vs Denver for investment'. "
            "Requires ENABLE_REAL_ESTATE=true."
        ),
        "parameters": {
            "location_a": "first city/neighborhood (e.g. 'Austin')",
            "location_b": "second city/neighborhood (e.g. 'Denver')",
        },
        "returns": (
            "side-by-side comparison of median_price, price_per_sqft, "
            "rental_yield, days_on_market, walk_score, YoY price change, "
            "inventory level, and market summaries for both locations"
        ),
    },
}
