#!/usr/bin/env python3
"""
Seed a Ghostfolio account with realistic demo portfolio data.

Usage:
  # Create a brand-new user and seed it (prints the access token when done):
  python seed_demo.py --base-url https://ghostfolio-production-01e0.up.railway.app

  # Seed an existing account (supply its auth JWT):
  python seed_demo.py --base-url https://... --auth-token eyJ...

The script creates:
  - 1 brokerage account ("Demo Portfolio")
  - 18 realistic BUY/SELL/DIVIDEND transactions spanning 2021-2024
    covering AAPL, MSFT, NVDA, GOOGL, AMZN, VTI (ETF)
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

DEFAULT_BASE_URL = "https://ghostfolio-production-01e0.up.railway.app"
_base_url = DEFAULT_BASE_URL

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    url = _base_url.rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        print(f"  HTTP {e.code} on {method} {path}: {body_text}", file=sys.stderr)
        return {"error": body_text, "statusCode": e.code}


# ---------------------------------------------------------------------------
# Step 1 – auth
# ---------------------------------------------------------------------------

def create_user() -> tuple[str, str]:
    """Create a new anonymous user. Returns (accessToken, authToken)."""
    print("Creating new demo user …")
    resp = _request("POST", "/api/v1/user", {})
    if "authToken" not in resp:
        print(f"Failed to create user: {resp}", file=sys.stderr)
        sys.exit(1)
    print(f"  User created  •  accessToken: {resp['accessToken']}")
    return resp["accessToken"], resp["authToken"]


def get_auth_token(access_token: str) -> str:
    """Exchange an access token for a JWT."""
    resp = _request("GET", f"/api/v1/auth/anonymous/{access_token}")
    if "authToken" not in resp:
        print(f"Failed to authenticate: {resp}", file=sys.stderr)
        sys.exit(1)
    return resp["authToken"]


# ---------------------------------------------------------------------------
# Step 2 – create brokerage account
# ---------------------------------------------------------------------------

def create_account(jwt: str) -> str:
    """Create a brokerage account and return its ID."""
    print("Creating brokerage account …")
    resp = _request("POST", "/api/v1/account", {
        "balance": 0,
        "currency": "USD",
        "isExcluded": False,
        "name": "Demo Portfolio",
        "platformId": None
    }, token=jwt)
    if "id" not in resp:
        print(f"Failed to create account: {resp}", file=sys.stderr)
        sys.exit(1)
    print(f"  Account ID: {resp['id']}")
    return resp["id"]


# ---------------------------------------------------------------------------
# Step 3 – import activities
# ---------------------------------------------------------------------------

ACTIVITIES = [
    # AAPL — built position over 2021-2022, partial sell in 2023
    {"type": "BUY",      "symbol": "AAPL",  "quantity": 10,  "unitPrice": 134.18, "fee": 0, "currency": "USD", "date": "2021-03-15"},
    {"type": "BUY",      "symbol": "AAPL",  "quantity": 5,   "unitPrice": 148.56, "fee": 0, "currency": "USD", "date": "2021-09-10"},
    {"type": "DIVIDEND", "symbol": "AAPL",  "quantity": 1,   "unitPrice": 3.44,   "fee": 0, "currency": "USD", "date": "2022-02-04"},
    {"type": "SELL",     "symbol": "AAPL",  "quantity": 5,   "unitPrice": 183.12, "fee": 0, "currency": "USD", "date": "2023-06-20"},
    {"type": "DIVIDEND", "symbol": "AAPL",  "quantity": 1,   "unitPrice": 3.66,   "fee": 0, "currency": "USD", "date": "2023-08-04"},

    # MSFT — steady accumulation
    {"type": "BUY",      "symbol": "MSFT",  "quantity": 8,   "unitPrice": 242.15, "fee": 0, "currency": "USD", "date": "2021-05-20"},
    {"type": "BUY",      "symbol": "MSFT",  "quantity": 4,   "unitPrice": 299.35, "fee": 0, "currency": "USD", "date": "2022-01-18"},
    {"type": "DIVIDEND", "symbol": "MSFT",  "quantity": 1,   "unitPrice": 9.68,   "fee": 0, "currency": "USD", "date": "2022-06-09"},
    {"type": "DIVIDEND", "symbol": "MSFT",  "quantity": 1,   "unitPrice": 10.40,  "fee": 0, "currency": "USD", "date": "2023-06-08"},

    # NVDA — bought cheap, rode the AI wave
    {"type": "BUY",      "symbol": "NVDA",  "quantity": 6,   "unitPrice": 143.25, "fee": 0, "currency": "USD", "date": "2021-11-05"},
    {"type": "BUY",      "symbol": "NVDA",  "quantity": 4,   "unitPrice": 166.88, "fee": 0, "currency": "USD", "date": "2022-07-12"},

    # GOOGL
    {"type": "BUY",      "symbol": "GOOGL", "quantity": 3,   "unitPrice": 2718.96,"fee": 0, "currency": "USD", "date": "2021-08-03"},
    {"type": "BUY",      "symbol": "GOOGL", "quantity": 5,   "unitPrice": 102.30, "fee": 0, "currency": "USD", "date": "2022-08-15"},

    # AMZN
    {"type": "BUY",      "symbol": "AMZN",  "quantity": 4,   "unitPrice": 168.54, "fee": 0, "currency": "USD", "date": "2023-02-08"},

    # VTI — ETF core holding
    {"type": "BUY",      "symbol": "VTI",   "quantity": 15,  "unitPrice": 207.38, "fee": 0, "currency": "USD", "date": "2021-04-06"},
    {"type": "BUY",      "symbol": "VTI",   "quantity": 10,  "unitPrice": 183.52, "fee": 0, "currency": "USD", "date": "2022-10-14"},
    {"type": "DIVIDEND", "symbol": "VTI",   "quantity": 1,   "unitPrice": 10.28,  "fee": 0, "currency": "USD", "date": "2022-12-27"},
    {"type": "DIVIDEND", "symbol": "VTI",   "quantity": 1,   "unitPrice": 11.42,  "fee": 0, "currency": "USD", "date": "2023-12-27"},
]


def import_activities(jwt: str, account_id: str) -> None:
    print(f"Importing {len(ACTIVITIES)} activities (YAHOO first, MANUAL fallback) …")
    imported = 0
    for a in ACTIVITIES:
        for data_source in ("YAHOO", "MANUAL"):
            payload = {
                "accountId":  account_id,
                "currency":   a["currency"],
                "dataSource": data_source,
                "date":       f"{a['date']}T00:00:00.000Z",
                "fee":        a["fee"],
                "quantity":   a["quantity"],
                "symbol":     a["symbol"],
                "type":       a["type"],
                "unitPrice":  a["unitPrice"],
            }
            resp = _request("POST", "/api/v1/import", {"activities": [payload]}, token=jwt)
            if not resp.get("error") and resp.get("statusCode", 200) < 400:
                imported += 1
                print(f"  ✓ {a['type']:8} {a['symbol']:5} ({data_source})")
                break
        else:
            print(f"  ✗ {a['type']:8} {a['symbol']:5} — skipped (both sources failed)", file=sys.stderr)

    print(f"  Imported {imported}/{len(ACTIVITIES)} activities successfully")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Ghostfolio base URL")
    parser.add_argument("--auth-token", default=None, help="Existing JWT (skip user creation)")
    parser.add_argument("--access-token", default=None, help="Existing access token to exchange for JWT")
    args = parser.parse_args()

    global _base_url
    _base_url = args.base_url.rstrip("/")

    # Resolve JWT
    if args.auth_token:
        jwt = args.auth_token
        access_token = "(provided)"
        print(f"Using provided auth token.")
    elif args.access_token:
        print(f"Exchanging access token for JWT …")
        jwt = get_auth_token(args.access_token)
        access_token = args.access_token
    else:
        access_token, jwt = create_user()

    account_id = create_account(jwt)
    import_activities(jwt, account_id)

    print()
    print("=" * 60)
    print("  Demo account seeded successfully!")
    print("=" * 60)
    print(f"  Login URL   : {_base_url}/en/register")
    print(f"  Access token: {access_token}")
    print(f"  Auth JWT    : {jwt}")
    print()
    print("  To use with the agent, set:")
    print(f"    GHOSTFOLIO_BEARER_TOKEN={jwt}")
    print("=" * 60)


if __name__ == "__main__":
    main()
