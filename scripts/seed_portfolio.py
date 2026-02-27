"""
seed_portfolio.py — Seed a Ghostfolio account with demo holdings.

Usage:
    python scripts/seed_portfolio.py

Environment variables:
    GHOSTFOLIO_BASE_URL     (default: http://localhost:3333)
    GHOSTFOLIO_BEARER_TOKEN (required)
"""

import asyncio
import os
import sys

import httpx

GHOSTFOLIO_URL = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")
TOKEN = os.getenv("GHOSTFOLIO_BEARER_TOKEN", "")


async def seed() -> None:
    if not TOKEN:
        print("ERROR: GHOSTFOLIO_BEARER_TOKEN is not set.", file=sys.stderr)
        sys.exit(1)

    holdings = [
        {
            "symbol": "AAPL",
            "quantity": 10,
            "unitPrice": 150.00,
            "date": "2024-01-15T00:00:00.000Z",
            "type": "BUY",
            "currency": "USD",
            "dataSource": "YAHOO",
            "fee": 4.95,
        },
        {
            "symbol": "MSFT",
            "quantity": 5,
            "unitPrice": 300.00,
            "date": "2024-03-10T00:00:00.000Z",
            "type": "BUY",
            "currency": "USD",
            "dataSource": "YAHOO",
            "fee": 4.95,
        },
        {
            "symbol": "NVDA",
            "quantity": 3,
            "unitPrice": 400.00,
            "date": "2024-06-01T00:00:00.000Z",
            "type": "BUY",
            "currency": "USD",
            "dataSource": "YAHOO",
            "fee": 4.95,
        },
        {
            "symbol": "TSLA",
            "quantity": 2,
            "unitPrice": 200.00,
            "date": "2024-09-20T00:00:00.000Z",
            "type": "BUY",
            "currency": "USD",
            "dataSource": "YAHOO",
            "fee": 4.95,
        },
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{GHOSTFOLIO_URL}/api/v1/import",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"activities": holdings},
        )
        print(f"Seed result: {resp.status_code}")
        if resp.status_code == 201:
            print(f"SUCCESS — imported {len(holdings)} transactions.")
            for h in holdings:
                print(f"  ✓ {h['type']} {h['quantity']} {h['symbol']} @ ${h['unitPrice']}")
        else:
            print(f"RESPONSE: {resp.text}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(seed())
