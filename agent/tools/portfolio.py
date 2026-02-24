import asyncio
import httpx
import os
import time
from datetime import datetime

# In-memory price cache: {symbol: {"data": {...}, "expires_at": float}}
_price_cache: dict[str, dict] = {}
_CACHE_TTL_SECONDS = 1800

# In-memory portfolio result cache with 60-second TTL.
# Keyed by token so each user gets their own cached result.
_portfolio_cache: dict[str, dict] = {}
_PORTFOLIO_CACHE_TTL = 60


async def _fetch_prices(client: httpx.AsyncClient, symbol: str) -> dict:
    """
    Fetches current price and YTD start price (Jan 2, 2026) from Yahoo Finance.
    Caches results for _CACHE_TTL_SECONDS to avoid rate limiting during eval runs.
    Returns dict with 'current' and 'ytd_start' prices (both may be None on failure).
    """
    cached = _price_cache.get(symbol)
    if cached and cached["expires_at"] > time.time():
        return cached["data"]

    result = {"current": None, "ytd_start": None}
    try:
        resp = await client.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"interval": "1d", "range": "1y"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8.0,
        )
        if resp.status_code != 200:
            return result
        data = resp.json()
        chart_result = data.get("chart", {}).get("result", [{}])[0]
        meta = chart_result.get("meta", {})
        timestamps = chart_result.get("timestamp", [])
        closes = chart_result.get("indicators", {}).get("quote", [{}])[0].get("close", [])

        result["current"] = float(meta.get("regularMarketPrice") or meta.get("previousClose") or 0) or None

        # Find the first trading day of 2026 (Jan 2, 2026 = 1735776000 unix)
        ytd_start_ts = 1735776000  # Jan 2, 2026 00:00 UTC
        ytd_price = None
        for ts, close in zip(timestamps, closes):
            if ts >= ytd_start_ts and close:
                ytd_price = float(close)
                break
        result["ytd_start"] = ytd_price
    except Exception:
        pass

    _price_cache[symbol] = {"data": result, "expires_at": time.time() + _CACHE_TTL_SECONDS}
    return result


async def portfolio_analysis(date_range: str = "max", token: str = None) -> dict:
    """
    Fetches portfolio holdings from Ghostfolio and computes real performance
    by fetching current prices directly from Yahoo Finance.
    Ghostfolio's own performance endpoint returns zeros locally due to
    Yahoo Finance feed errors — this tool works around that.
    Results are cached for 60 seconds per token to avoid redundant API calls
    within multi-step conversations.
    """
    base_url = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")
    token = token or os.getenv("GHOSTFOLIO_BEARER_TOKEN", "")
    tool_result_id = f"portfolio_{int(datetime.utcnow().timestamp())}"

    # Return cached result if fresh enough
    cache_key = token or "__default__"
    cached = _portfolio_cache.get(cache_key)
    if cached and (time.time() - cached["timestamp"]) < _PORTFOLIO_CACHE_TTL:
        result = dict(cached["data"])
        result["from_cache"] = True
        result["tool_result_id"] = tool_result_id  # fresh ID for citation tracking
        return result

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {token}"}

            holdings_resp = await client.get(
                f"{base_url}/api/v1/portfolio/holdings",
                headers=headers,
            )
            holdings_resp.raise_for_status()
            raw = holdings_resp.json()

            # Holdings is a list directly
            holdings_list = raw if isinstance(raw, list) else raw.get("holdings", [])

            enriched_holdings = []
            total_cost_basis = 0.0
            total_current_value = 0.0
            prices_fetched = 0

            ytd_cost_basis = 0.0
            ytd_current_value = 0.0

            # Fetch all prices in parallel
            symbols = [h.get("symbol", "") for h in holdings_list]
            price_results = await asyncio.gather(
                *[_fetch_prices(client, sym) for sym in symbols],
                return_exceptions=True,
            )

            for h, prices_or_exc in zip(holdings_list, price_results):
                symbol = h.get("symbol", "")
                quantity = h.get("quantity", 0)
                cost_basis = h.get("valueInBaseCurrency", 0)
                allocation_pct = round(h.get("allocationInPercentage", 0) * 100, 2)

                prices = prices_or_exc if isinstance(prices_or_exc, dict) else {"current": None, "ytd_start": None}
                current_price = prices["current"]
                ytd_start_price = prices["ytd_start"]

                if current_price is not None:
                    current_value = round(quantity * current_price, 2)
                    gain_usd = round(current_value - cost_basis, 2)
                    gain_pct = round((gain_usd / cost_basis * 100), 2) if cost_basis > 0 else 0.0
                    prices_fetched += 1
                else:
                    current_value = cost_basis
                    gain_usd = 0.0
                    gain_pct = 0.0

                # YTD: compare Jan 2 2026 value to today
                if ytd_start_price and current_price:
                    ytd_start_value = round(quantity * ytd_start_price, 2)
                    ytd_gain_usd = round(current_value - ytd_start_value, 2)
                    ytd_gain_pct = round(ytd_gain_usd / ytd_start_value * 100, 2) if ytd_start_value else 0.0
                    ytd_cost_basis += ytd_start_value
                    ytd_current_value += current_value
                else:
                    ytd_gain_usd = None
                    ytd_gain_pct = None

                total_cost_basis += cost_basis
                total_current_value += current_value

                enriched_holdings.append({
                    "symbol": symbol,
                    "name": h.get("name", symbol),
                    "quantity": quantity,
                    "cost_basis_usd": cost_basis,
                    "current_price_usd": current_price,
                    "ytd_start_price_usd": ytd_start_price,
                    "current_value_usd": current_value,
                    "gain_usd": gain_usd,
                    "gain_pct": gain_pct,
                    "ytd_gain_usd": ytd_gain_usd,
                    "ytd_gain_pct": ytd_gain_pct,
                    "allocation_pct": allocation_pct,
                    "currency": h.get("currency", "USD"),
                    "asset_class": h.get("assetClass", ""),
                })

            total_gain_usd = round(total_current_value - total_cost_basis, 2)
            total_gain_pct = (
                round(total_gain_usd / total_cost_basis * 100, 2)
                if total_cost_basis > 0 else 0.0
            )
            ytd_total_gain_usd = round(ytd_current_value - ytd_cost_basis, 2) if ytd_cost_basis else None
            ytd_total_gain_pct = (
                round(ytd_total_gain_usd / ytd_cost_basis * 100, 2)
                if ytd_cost_basis and ytd_total_gain_usd is not None else None
            )

            # Sort holdings by current value descending
            enriched_holdings.sort(key=lambda x: x["current_value_usd"], reverse=True)

            result = {
                "tool_name": "portfolio_analysis",
                "success": True,
                "tool_result_id": tool_result_id,
                "timestamp": datetime.utcnow().isoformat(),
                "endpoint": "/api/v1/portfolio/holdings + Yahoo Finance (live prices)",
                "result": {
                    "summary": {
                        "total_cost_basis_usd": round(total_cost_basis, 2),
                        "total_current_value_usd": round(total_current_value, 2),
                        "total_gain_usd": total_gain_usd,
                        "total_gain_pct": total_gain_pct,
                        "ytd_gain_usd": ytd_total_gain_usd,
                        "ytd_gain_pct": ytd_total_gain_pct,
                        "holdings_count": len(enriched_holdings),
                        "live_prices_fetched": prices_fetched,
                        "date_range": date_range,
                        "note": (
                            "Performance uses live Yahoo Finance prices. "
                            "YTD = Jan 2 2026 to today. "
                            "Total return = purchase date to today."
                        ),
                    },
                    "holdings": enriched_holdings,
                },
            }
            _portfolio_cache[cache_key] = {"data": result, "timestamp": time.time()}
            return result

    except httpx.TimeoutException:
        return {
            "tool_name": "portfolio_analysis",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "TIMEOUT",
            "message": "Portfolio API timed out. Try again shortly.",
        }
    except Exception as e:
        return {
            "tool_name": "portfolio_analysis",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "API_ERROR",
            "message": f"Failed to fetch portfolio data: {str(e)}",
        }
