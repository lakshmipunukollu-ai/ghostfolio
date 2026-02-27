"""
Write tools for recording transactions in Ghostfolio.
All tools POST to /api/v1/import and return structured result dicts.
These tools are NEVER called directly — they are only called after
the user confirms via the write_confirm gate in graph.py.
"""
import httpx
import os
from datetime import date, datetime


def _today_str() -> str:
    return date.today().strftime("%Y-%m-%d")


async def _execute_import(payload: dict, token: str = None) -> dict:
    """
    POSTs an activity payload to Ghostfolio /api/v1/import.
    Returns a structured success/failure dict matching other tools.
    """
    base_url = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")
    token = token or os.getenv("GHOSTFOLIO_BEARER_TOKEN", "")
    tool_result_id = f"write_{int(datetime.utcnow().timestamp())}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base_url}/api/v1/import",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()

        activity = payload.get("activities", [{}])[0]
        return {
            "tool_name": "write_transaction",
            "success": True,
            "tool_result_id": tool_result_id,
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "/api/v1/import",
            "result": {
                "status": "recorded",
                "type": activity.get("type"),
                "symbol": activity.get("symbol"),
                "quantity": activity.get("quantity"),
                "unitPrice": activity.get("unitPrice"),
                "date": activity.get("date", "")[:10],
                "fee": activity.get("fee", 0),
                "currency": activity.get("currency"),
            },
        }

    except httpx.HTTPStatusError as e:
        return {
            "tool_name": "write_transaction",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "API_ERROR",
            "message": (
                f"Ghostfolio rejected the transaction: "
                f"{e.response.status_code} — {e.response.text[:300]}"
            ),
        }
    except httpx.TimeoutException:
        return {
            "tool_name": "write_transaction",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "TIMEOUT",
            "message": "Ghostfolio API timed out. Transaction was NOT recorded.",
        }
    except Exception as e:
        return {
            "tool_name": "write_transaction",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "API_ERROR",
            "message": f"Failed to record transaction: {str(e)}",
        }


async def buy_stock(
    symbol: str,
    quantity: float,
    price: float,
    date_str: str = None,
    fee: float = 0,
    token: str = None,
) -> dict:
    """Record a BUY transaction in Ghostfolio."""
    date_str = date_str or _today_str()
    payload = {
        "activities": [{
            "currency": "USD",
            "dataSource": "YAHOO",
            "date": f"{date_str}T00:00:00.000Z",
            "fee": fee,
            "quantity": quantity,
            "symbol": symbol.upper(),
            "type": "BUY",
            "unitPrice": price,
        }]
    }
    return await _execute_import(payload, token=token)


async def sell_stock(
    symbol: str,
    quantity: float,
    price: float,
    date_str: str = None,
    fee: float = 0,
    token: str = None,
) -> dict:
    """Record a SELL transaction in Ghostfolio."""
    date_str = date_str or _today_str()
    payload = {
        "activities": [{
            "currency": "USD",
            "dataSource": "YAHOO",
            "date": f"{date_str}T00:00:00.000Z",
            "fee": fee,
            "quantity": quantity,
            "symbol": symbol.upper(),
            "type": "SELL",
            "unitPrice": price,
        }]
    }
    return await _execute_import(payload, token=token)


async def add_transaction(
    symbol: str,
    quantity: float,
    price: float,
    transaction_type: str,
    date_str: str = None,
    fee: float = 0,
    token: str = None,
) -> dict:
    """Record any transaction type: BUY | SELL | DIVIDEND | FEE | INTEREST."""
    valid_types = {"BUY", "SELL", "DIVIDEND", "FEE", "INTEREST"}
    transaction_type = transaction_type.upper()
    if transaction_type not in valid_types:
        tool_result_id = f"write_{int(datetime.utcnow().timestamp())}"
        return {
            "tool_name": "write_transaction",
            "success": False,
            "tool_result_id": tool_result_id,
            "error": "INVALID_TYPE",
            "message": (
                f"Invalid transaction type '{transaction_type}'. "
                f"Must be one of: {sorted(valid_types)}"
            ),
        }

    date_str = date_str or _today_str()
    data_source = "YAHOO" if transaction_type in {"BUY", "SELL"} else "MANUAL"
    payload = {
        "activities": [{
            "currency": "USD",
            "dataSource": data_source,
            "date": f"{date_str}T00:00:00.000Z",
            "fee": fee,
            "quantity": quantity,
            "symbol": symbol.upper(),
            "type": transaction_type,
            "unitPrice": price,
        }]
    }
    return await _execute_import(payload, token=token)


async def add_cash(
    amount: float,
    currency: str = "USD",
    account_id: str = None,
    token: str = None,
) -> dict:
    """
    Add cash to the portfolio by recording an INTEREST transaction on CASH.
    account_id is accepted but not forwarded (Ghostfolio import does not support it
    via the import API — cash goes to the default account).
    """
    date_str = _today_str()
    payload = {
        "activities": [{
            "currency": currency.upper(),
            "dataSource": "MANUAL",
            "date": f"{date_str}T00:00:00.000Z",
            "fee": 0,
            "quantity": amount,
            "symbol": "CASH",
            "type": "INTEREST",
            "unitPrice": 1,
        }]
    }
    return await _execute_import(payload, token=token)
