import json
import time
import os
from datetime import datetime

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

from graph import build_graph
from state import AgentState

app = FastAPI(
    title="Ghostfolio AI Agent",
    description="LangGraph-powered portfolio analysis agent on top of Ghostfolio",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

feedback_log: list[dict] = []
cost_log: list[dict] = []

COST_PER_REQUEST_USD = (2000 * 0.000003) + (500 * 0.000015)


class ChatRequest(BaseModel):
    query: str
    history: list[dict] = []
    # Clients must echo back pending_write from the previous response when
    # the user is confirming (or cancelling) a write operation.
    pending_write: dict | None = None
    # Optional: the logged-in user's Ghostfolio bearer token.
    # When provided, the agent uses THIS token for all API calls so it operates
    # on the caller's own portfolio data instead of the shared env-var token.
    bearer_token: str | None = None


class FeedbackRequest(BaseModel):
    query: str
    response: str
    rating: int
    comment: str = ""


@app.post("/chat")
async def chat(req: ChatRequest):
    start = time.time()

    # Build conversation history preserving both user AND assistant turns so
    # Claude has full context for follow-up questions.
    history_messages = []
    for m in req.history:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "user":
            history_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            history_messages.append(AIMessage(content=content))

    initial_state: AgentState = {
        "user_query": req.query,
        "messages": history_messages,
        "query_type": "",
        "portfolio_snapshot": {},
        "tool_results": [],
        "pending_verifications": [],
        "confidence_score": 1.0,
        "verification_outcome": "pass",
        "awaiting_confirmation": False,
        "confirmation_payload": None,
        # Carry forward any pending write payload the client echoed back
        "pending_write": req.pending_write,
        # Per-user token — overrides env var when present
        "bearer_token": req.bearer_token,
        "confirmation_message": None,
        "missing_fields": [],
        "final_response": None,
        "citations": [],
        "error": None,
    }

    result = await graph.ainvoke(initial_state)

    elapsed = round(time.time() - start, 2)

    cost_log.append({
        "timestamp": datetime.utcnow().isoformat(),
        "query": req.query[:80],
        "estimated_cost_usd": round(COST_PER_REQUEST_USD, 5),
        "latency_seconds": elapsed,
    })

    tools_used = [r["tool_name"] for r in result.get("tool_results", [])]

    # Extract structured comparison card when compare_neighborhoods ran
    comparison_card = None
    for r in result.get("tool_results", []):
        if (
            r.get("tool_name") == "real_estate"
            and r.get("success")
            and isinstance(r.get("result"), dict)
            and "location_a" in r["result"]
        ):
            res = r["result"]
            m = res["metrics"]
            # Count advantages per city to form a verdict
            advantages: dict[str, int] = {res["location_a"]: 0, res["location_b"]: 0}
            for metric_data in m.values():
                if isinstance(metric_data, dict):
                    for winner_key in ("more_affordable", "higher_yield", "more_walkable"):
                        winner_city = metric_data.get(winner_key)
                        if winner_city in advantages:
                            advantages[winner_city] += 1
            winner = max(advantages, key=lambda c: advantages[c])
            loser = [c for c in advantages if c != winner][0]
            verdict = (
                f"{winner} leads on affordability & yield "
                f"({advantages[winner]} vs {advantages[loser]} metrics)."
            )
            comparison_card = {
                "city_a": {
                    "name": res["location_a"],
                    "median_price": m["median_price"]["a"],
                    "price_per_sqft": m["price_per_sqft"]["a"],
                    "days_on_market": m["days_on_market"]["a"],
                    "walk_score": m["walk_score"]["a"],
                    "yoy_change": m["yoy_price_change_pct"]["a"],
                    "inventory": m["inventory"]["a"],
                },
                "city_b": {
                    "name": res["location_b"],
                    "median_price": m["median_price"]["b"],
                    "price_per_sqft": m["price_per_sqft"]["b"],
                    "days_on_market": m["days_on_market"]["b"],
                    "walk_score": m["walk_score"]["b"],
                    "yoy_change": m["yoy_price_change_pct"]["b"],
                    "inventory": m["inventory"]["b"],
                },
                "winners": {
                    "median_price": m["median_price"].get("more_affordable"),
                    "price_per_sqft": m["price_per_sqft"].get("more_affordable"),
                    "days_on_market": m["days_on_market"].get("less_competitive"),
                    "walk_score": m["walk_score"].get("more_walkable"),
                },
                "verdict": verdict,
            }
            break

    # Extract portfolio allocation chart data when portfolio_analysis ran
    chart_data = None
    for r in result.get("tool_results", []):
        if (
            r.get("tool_name") == "portfolio_analysis"
            and r.get("success")
            and isinstance(r.get("result"), dict)
        ):
            holdings = r["result"].get("holdings", [])
            if holdings:
                # Use top 6 holdings by allocation; group the rest as "Other"
                sorted_h = sorted(holdings, key=lambda h: h.get("allocation_pct", 0), reverse=True)
                top = sorted_h[:6]
                other_alloc = sum(h.get("allocation_pct", 0) for h in sorted_h[6:])
                labels = [h.get("symbol", "?") for h in top]
                values = [round(h.get("allocation_pct", 0), 1) for h in top]
                if other_alloc > 0.1:
                    labels.append("Other")
                    values.append(round(other_alloc, 1))
                chart_data = {
                    "type": "allocation_pie",
                    "labels": labels,
                    "values": values,
                }
            break

    return {
        "response": result.get("final_response", "No response generated."),
        "confidence_score": result.get("confidence_score", 0.0),
        "verification_outcome": result.get("verification_outcome", "unknown"),
        "awaiting_confirmation": result.get("awaiting_confirmation", False),
        # Clients must echo this back in the next request if awaiting_confirmation
        "pending_write": result.get("pending_write"),
        "tools_used": tools_used,
        "citations": result.get("citations", []),
        "latency_seconds": elapsed,
        "comparison_card": comparison_card,
        "chart_data": chart_data,
    }


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming variant of /chat — returns SSE (text/event-stream).
    Runs the full graph, then streams the final response word by word so
    the user sees output immediately rather than waiting for the full response.
    """
    history_messages = []
    for m in req.history:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "user":
            history_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            history_messages.append(AIMessage(content=content))

    initial_state: AgentState = {
        "user_query": req.query,
        "messages": history_messages,
        "query_type": "",
        "portfolio_snapshot": {},
        "tool_results": [],
        "pending_verifications": [],
        "confidence_score": 1.0,
        "verification_outcome": "pass",
        "awaiting_confirmation": False,
        "confirmation_payload": None,
        "pending_write": req.pending_write,
        "bearer_token": req.bearer_token,
        "confirmation_message": None,
        "missing_fields": [],
        "final_response": None,
        "citations": [],
        "error": None,
    }

    async def generate():
        result = await graph.ainvoke(initial_state)
        response_text = result.get("final_response", "No response generated.")
        tools_used = [r["tool_name"] for r in result.get("tool_results", [])]

        # Stream metadata first
        meta = {
            "type": "meta",
            "confidence_score": result.get("confidence_score", 0.0),
            "verification_outcome": result.get("verification_outcome", "unknown"),
            "awaiting_confirmation": result.get("awaiting_confirmation", False),
            "tools_used": tools_used,
            "citations": result.get("citations", []),
        }
        yield f"data: {json.dumps(meta)}\n\n"

        # Stream response word by word
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk = {"type": "token", "token": word + " ", "done": i == len(words) - 1}
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


class SeedRequest(BaseModel):
    bearer_token: str | None = None


@app.post("/seed")
async def seed_demo_portfolio(req: SeedRequest):
    """
    Populate the caller's Ghostfolio account with a realistic demo portfolio
    (18 transactions across AAPL, MSFT, NVDA, GOOGL, AMZN, VTI).

    Called automatically by the Angular chat when a logged-in user has an
    empty portfolio, so first-time Google OAuth users see real data
    immediately after signing in.
    """
    base_url = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")
    token = req.bearer_token or os.getenv("GHOSTFOLIO_BEARER_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    DEMO_ACTIVITIES = [
        {"type": "BUY",      "symbol": "AAPL",  "quantity": 10,  "unitPrice": 134.18, "date": "2021-03-15"},
        {"type": "BUY",      "symbol": "AAPL",  "quantity": 5,   "unitPrice": 148.56, "date": "2021-09-10"},
        {"type": "DIVIDEND", "symbol": "AAPL",  "quantity": 1,   "unitPrice": 3.44,   "date": "2022-02-04"},
        {"type": "SELL",     "symbol": "AAPL",  "quantity": 5,   "unitPrice": 183.12, "date": "2023-06-20"},
        {"type": "DIVIDEND", "symbol": "AAPL",  "quantity": 1,   "unitPrice": 3.66,   "date": "2023-08-04"},
        {"type": "BUY",      "symbol": "MSFT",  "quantity": 8,   "unitPrice": 242.15, "date": "2021-05-20"},
        {"type": "BUY",      "symbol": "MSFT",  "quantity": 4,   "unitPrice": 299.35, "date": "2022-01-18"},
        {"type": "DIVIDEND", "symbol": "MSFT",  "quantity": 1,   "unitPrice": 9.68,   "date": "2022-06-09"},
        {"type": "DIVIDEND", "symbol": "MSFT",  "quantity": 1,   "unitPrice": 10.40,  "date": "2023-06-08"},
        {"type": "BUY",      "symbol": "NVDA",  "quantity": 6,   "unitPrice": 143.25, "date": "2021-11-05"},
        {"type": "BUY",      "symbol": "NVDA",  "quantity": 4,   "unitPrice": 166.88, "date": "2022-07-12"},
        {"type": "BUY",      "symbol": "GOOGL", "quantity": 3,   "unitPrice": 2718.96,"date": "2021-08-03"},
        {"type": "BUY",      "symbol": "GOOGL", "quantity": 5,   "unitPrice": 102.30, "date": "2022-08-15"},
        {"type": "BUY",      "symbol": "AMZN",  "quantity": 4,   "unitPrice": 168.54, "date": "2023-02-08"},
        {"type": "BUY",      "symbol": "VTI",   "quantity": 15,  "unitPrice": 207.38, "date": "2021-04-06"},
        {"type": "BUY",      "symbol": "VTI",   "quantity": 10,  "unitPrice": 183.52, "date": "2022-10-14"},
        {"type": "DIVIDEND", "symbol": "VTI",   "quantity": 1,   "unitPrice": 10.28,  "date": "2022-12-27"},
        {"type": "DIVIDEND", "symbol": "VTI",   "quantity": 1,   "unitPrice": 11.42,  "date": "2023-12-27"},
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create a brokerage account for this user
        acct_resp = await client.post(
            f"{base_url}/api/v1/account",
            headers=headers,
            json={"balance": 0, "currency": "USD", "isExcluded": False, "name": "Demo Portfolio", "platformId": None},
        )
        if acct_resp.status_code not in (200, 201):
            return {"success": False, "error": f"Could not create account: {acct_resp.text}"}

        account_id = acct_resp.json().get("id")

        # Try YAHOO data source first (gives live prices in the UI).
        # Fall back to MANUAL per-activity if YAHOO validation fails.
        imported = 0
        for a in DEMO_ACTIVITIES:
            for data_source in ("YAHOO", "MANUAL"):
                activity_payload = {
                    "accountId": account_id,
                    "currency": "USD",
                    "dataSource": data_source,
                    "date": f"{a['date']}T00:00:00.000Z",
                    "fee": 0,
                    "quantity": a["quantity"],
                    "symbol": a["symbol"],
                    "type": a["type"],
                    "unitPrice": a["unitPrice"],
                }
                resp = await client.post(
                    f"{base_url}/api/v1/import",
                    headers=headers,
                    json={"activities": [activity_payload]},
                )
                if resp.status_code in (200, 201):
                    imported += 1
                    break  # success — no need to try MANUAL fallback

    return {
        "success": True,
        "message": f"Demo portfolio seeded with {imported} activities across AAPL, MSFT, NVDA, GOOGL, AMZN, VTI.",
        "account_id": account_id,
        "activities_imported": imported,
    }


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/login")
async def auth_login(req: LoginRequest):
    """
    Demo auth endpoint.
    Validates against DEMO_EMAIL / DEMO_PASSWORD env vars (defaults: test@example.com / password).
    On success, returns the configured GHOSTFOLIO_BEARER_TOKEN so the client can use it.
    """
    demo_email    = os.getenv("DEMO_EMAIL", "test@example.com")
    demo_password = os.getenv("DEMO_PASSWORD", "password")

    if req.email.strip().lower() != demo_email.lower() or req.password != demo_password:
        return JSONResponse(
            status_code=401,
            content={"success": False, "message": "Invalid email or password."},
        )

    token = os.getenv("GHOSTFOLIO_BEARER_TOKEN", "")

    # Fetch display name for this token
    base_url = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")
    display_name = "Investor"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get(
                f"{base_url}/api/v1/user",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 200:
                data = r.json()
                alias = data.get("settings", {}).get("alias") or ""
                display_name = alias or demo_email.split("@")[0] or "Investor"
    except Exception:
        display_name = demo_email.split("@")[0] or "Investor"

    return {
        "success": True,
        "token": token,
        "name": display_name,
        "email": demo_email,
    }


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page():
    with open(os.path.join(os.path.dirname(__file__), "login.html")) as f:
        return f.read()


@app.get("/me")
async def get_me():
    """Returns the Ghostfolio user profile for the configured bearer token."""
    base_url = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")
    token = os.getenv("GHOSTFOLIO_BEARER_TOKEN", "")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{base_url}/api/v1/user",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                alias = data.get("settings", {}).get("alias") or data.get("alias") or ""
                email = data.get("email", "")
                display = alias or (email.split("@")[0] if email else "")
                return {
                    "success": True,
                    "id": data.get("id", ""),
                    "name": display or "Investor",
                    "email": email,
                }
    except Exception:
        pass

    # Fallback: decode JWT locally (no network)
    try:
        import base64 as _b64
        padded = token.split(".")[1] + "=="
        payload = json.loads(_b64.b64decode(padded).decode())
        uid = payload.get("id", "")
        initials = uid[:2].upper() if uid else "IN"
        return {"success": True, "id": uid, "name": "Investor", "initials": initials, "email": ""}
    except Exception:
        pass

    return {"success": False, "name": "Investor", "id": "", "email": ""}


# Node labels shown in the live thinking display
_NODE_LABELS = {
    "classify":      "Analyzing your question",
    "tools":         "Fetching portfolio data",
    "write_prepare": "Preparing transaction",
    "write_execute": "Recording transaction",
    "verify":        "Verifying data accuracy",
    "format":        "Composing response",
}
_OUR_NODES = set(_NODE_LABELS.keys())


@app.post("/chat/steps")
async def chat_steps(req: ChatRequest):
    """
    SSE endpoint that streams LangGraph node events in real time.
    Clients receive step events as each graph node starts/ends,
    then a meta event with final metadata, then token events for the response.
    """
    start = time.time()

    history_messages = []
    for m in req.history:
        role = m.get("role", "")
        content = m.get("content", "")
        if role == "user":
            history_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            history_messages.append(AIMessage(content=content))

    initial_state: AgentState = {
        "user_query": req.query,
        "messages": history_messages,
        "query_type": "",
        "portfolio_snapshot": {},
        "tool_results": [],
        "pending_verifications": [],
        "confidence_score": 1.0,
        "verification_outcome": "pass",
        "awaiting_confirmation": False,
        "confirmation_payload": None,
        "pending_write": req.pending_write,
        "bearer_token": req.bearer_token,
        "confirmation_message": None,
        "missing_fields": [],
        "final_response": None,
        "citations": [],
        "error": None,
    }

    async def generate():
        seen_nodes = set()

        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                etype = event.get("event", "")
                ename = event.get("name", "")

                if ename in _OUR_NODES:
                    if etype == "on_chain_start" and ename not in seen_nodes:
                        seen_nodes.add(ename)
                        payload = {
                            "type": "step",
                            "node": ename,
                            "label": _NODE_LABELS[ename],
                            "status": "running",
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                    elif etype == "on_chain_end":
                        output = event.get("data", {}).get("output", {})
                        step_payload: dict = {
                            "type": "step",
                            "node": ename,
                            "label": _NODE_LABELS[ename],
                            "status": "done",
                        }
                        if ename == "tools":
                            results = output.get("tool_results", [])
                            step_payload["tools"] = [r["tool_name"] for r in results]
                        if ename == "verify":
                            step_payload["confidence"] = output.get("confidence_score", 1.0)
                            step_payload["outcome"] = output.get("verification_outcome", "pass")
                        yield f"data: {json.dumps(step_payload)}\n\n"

                elif ename == "LangGraph" and etype == "on_chain_end":
                    output = event.get("data", {}).get("output", {})
                    response_text = output.get("final_response", "No response generated.")
                    tool_results = output.get("tool_results", [])
                    elapsed = round(time.time() - start, 2)

                    cost_log.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "query": req.query[:80],
                        "estimated_cost_usd": round(COST_PER_REQUEST_USD, 5),
                        "latency_seconds": elapsed,
                    })

                    meta = {
                        "type": "meta",
                        "confidence_score": output.get("confidence_score", 0.0),
                        "verification_outcome": output.get("verification_outcome", "unknown"),
                        "awaiting_confirmation": output.get("awaiting_confirmation", False),
                        "pending_write": output.get("pending_write"),
                        "tools_used": [r["tool_name"] for r in tool_results],
                        "citations": output.get("citations", []),
                        "latency_seconds": elapsed,
                    }
                    yield f"data: {json.dumps(meta)}\n\n"

                    words = response_text.split(" ")
                    for i, word in enumerate(words):
                        chunk = {
                            "type": "token",
                            "token": word + (" " if i < len(words) - 1 else ""),
                            "done": i == len(words) - 1,
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            err_payload = {
                "type": "error",
                "message": f"Agent error: {str(exc)}",
            }
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def chat_ui():
    with open(os.path.join(os.path.dirname(__file__), "chat_ui.html")) as f:
        return f.read()


@app.get("/health")
async def health():
    ghostfolio_ok = False
    base_url = os.getenv("GHOSTFOLIO_BASE_URL", "http://localhost:3333")

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{base_url}/api/v1/health")
            ghostfolio_ok = resp.status_code == 200
    except Exception:
        ghostfolio_ok = False

    return {
        "status": "ok",
        "ghostfolio_reachable": ghostfolio_ok,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "query": req.query,
        "response": req.response[:200],
        "rating": req.rating,
        "comment": req.comment,
    }
    feedback_log.append(entry)
    return {"status": "recorded", "total_feedback": len(feedback_log)}


@app.get("/feedback/summary")
async def feedback_summary():
    if not feedback_log:
        return {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "approval_rate": "N/A",
            "message": "No feedback recorded yet.",
        }

    positive = sum(1 for f in feedback_log if f["rating"] > 0)
    negative = len(feedback_log) - positive
    approval_rate = f"{(positive / len(feedback_log) * 100):.0f}%"

    return {
        "total": len(feedback_log),
        "positive": positive,
        "negative": negative,
        "approval_rate": approval_rate,
    }


@app.get("/real-estate/log")
async def real_estate_log():
    """
    Returns the in-memory real estate tool invocation log.
    Only available when ENABLE_REAL_ESTATE=true.
    Each entry: timestamp, function, query (truncated), duration_ms, success.
    """
    from tools.real_estate import is_real_estate_enabled, get_invocation_log

    if not is_real_estate_enabled():
        return JSONResponse(
            status_code=404,
            content={"error": "Real estate feature is not enabled."},
        )

    log = get_invocation_log()
    total = len(log)
    successes = sum(1 for e in log if e["success"])
    return {
        "total_invocations": total,
        "success_count": successes,
        "failure_count": total - successes,
        "entries": log[-50:],  # last 50 only
    }


@app.get("/costs")
async def costs():
    total = sum(c["estimated_cost_usd"] for c in cost_log)
    avg = total / max(len(cost_log), 1)

    return {
        "total_requests": len(cost_log),
        "estimated_cost_usd": round(total, 4),
        "avg_per_request": round(avg, 5),
        "cost_assumptions": {
            "model": "claude-sonnet-4-20250514",
            "input_tokens_per_request": 2000,
            "output_tokens_per_request": 500,
            "input_price_per_million": 3.0,
            "output_price_per_million": 15.0,
        },
    }
