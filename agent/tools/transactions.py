import httpx
import os
from datetime import datetime


async def transaction_query(symbol: str = None, limit: int = 50, token: str = None) -> dict:
    """
    Fetches activity/transaction history from Ghostfolio.
    Note: Ghostfolio's activities are at /api/v1/order endpoint.
    """
    base_url = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")
    token = token or os.getenv("GHOSTFOLIO_BEARER_TOKEN", "")
    tool_result_id = f"tx_{int(datetime.utcnow().timestamp())}"

    params = {}
    if symbol:
        params["symbol"] = symbol.upper()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{base_url}/api/v1/order",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

            activities = data.get("activities", [])

            if symbol:
                activities = [
                    a for a in activities
                    if a.get("SymbolProfile", {}).get("symbol", "").upper() == symbol.upper()
                ]

            activities = activities[:limit]

            simplified = sorted(
                [
                    {
                        "type": a.get("type"),
                        "symbol": a.get("SymbolProfile", {}).get("symbol"),
                        "name": a.get("SymbolProfile", {}).get("name"),
                        "quantity": a.get("quantity"),
                        "unitPrice": a.get("unitPrice"),
                        "fee": a.get("fee"),
                        "currency": a.get("currency"),
                        "date": a.get("date", "")[:10],
                        "value": a.get("valueInBaseCurrency"),
                        "id": a.get("id"),
                    }
                    for a in activities
                ],
                key=lambda x: x.get("date", ""),
                reverse=True,  # newest-first so "recent" queries see latest data before truncation
            )

            return {
                "tool_name": "transaction_query",
                "success": True,
                "tool_result_id": tool_result_id,
                "timestamp": datetime.utcnow().isoformat(),
                "endpoint": "/api/v1/order",
                "result": simplified,
                "count": len(simplified),
                "filter_symbol": symbol,
            }

    except httpx.TimeoutException:
        return {
            "tool_name": "transaction_query",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "TIMEOUT",
            "message": "Ghostfolio API timed out after 5 seconds.",
        }
    except Exception as e:
        return {
            "tool_name": "transaction_query",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "API_ERROR",
            "message": f"Failed to fetch transactions: {str(e)}",
        }
