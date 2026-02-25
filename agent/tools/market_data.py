import asyncio
import httpx
from datetime import datetime

# Tickers shown for vague "what's hot / market overview" queries
MARKET_OVERVIEW_TICKERS = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]


async def market_overview() -> dict:
    """
    Fetches a quick snapshot of major indices and top tech stocks.
    Used for queries like 'what's hot today?', 'market overview', etc.
    """
    tool_result_id = f"market_overview_{int(datetime.utcnow().timestamp())}"
    results = []

    async def _fetch(sym: str):
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                    params={"interval": "1d", "range": "2d"},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                data = resp.json()
                meta = (data.get("chart", {}).get("result") or [{}])[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                prev = meta.get("chartPreviousClose") or meta.get("previousClose")
                chg = round((price - prev) / prev * 100, 2) if price and prev and prev != 0 else None
                return {"symbol": sym, "price": price, "change_pct": chg, "currency": meta.get("currency", "USD")}
        except Exception:
            return {"symbol": sym, "price": None, "change_pct": None}

    results = await asyncio.gather(*[_fetch(s) for s in MARKET_OVERVIEW_TICKERS])
    successful = [r for r in results if r["price"] is not None]

    if not successful:
        return {
            "tool_name": "market_data",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "NO_DATA",
            "message": "Could not fetch market overview data. Yahoo Finance may be temporarily unavailable.",
        }

    return {
        "tool_name": "market_data",
        "success": True,
        "tool_result_id": tool_result_id,
        "timestamp": datetime.utcnow().isoformat(),
        "result": {"overview": successful},
    }


async def market_data(symbol: str) -> dict:
    """
    Fetches current market data from Yahoo Finance (free, no API key).
    Uses the Yahoo Finance v8 chart API.
    Timeout is 8.0s — Yahoo is slower than Ghostfolio.
    """
    symbol = symbol.upper().strip()
    tool_result_id = f"market_{symbol}_{int(datetime.utcnow().timestamp())}"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                params={"interval": "1d", "range": "5d"},
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            )
            resp.raise_for_status()
            data = resp.json()

            chart_result = data.get("chart", {}).get("result", [])
            if not chart_result:
                return {
                    "tool_name": "market_data",
                    "success": False,
                    "tool_result_id": tool_result_id,
                    "error": "NO_DATA",
                    "message": f"No market data found for symbol '{symbol}'. Check the ticker is valid.",
                }

            meta = chart_result[0].get("meta", {})
            current_price = meta.get("regularMarketPrice")
            prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

            change_pct = None
            if current_price and prev_close and prev_close != 0:
                change_pct = round((current_price - prev_close) / prev_close * 100, 2)

            return {
                "tool_name": "market_data",
                "success": True,
                "tool_result_id": tool_result_id,
                "timestamp": datetime.utcnow().isoformat(),
                "endpoint": f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                "result": {
                    "symbol": symbol,
                    "current_price": current_price,
                    "previous_close": prev_close,
                    "change_pct": change_pct,
                    "currency": meta.get("currency"),
                    "exchange": meta.get("exchangeName"),
                    "instrument_type": meta.get("instrumentType"),
                },
            }

    except httpx.TimeoutException:
        return {
            "tool_name": "market_data",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "TIMEOUT",
            "message": f"Yahoo Finance timed out fetching {symbol}. Try again in a moment.",
        }
    except Exception as e:
        return {
            "tool_name": "market_data",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "API_ERROR",
            "message": f"Failed to fetch market data for {symbol}: {str(e)}",
        }
