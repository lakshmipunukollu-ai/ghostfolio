import json
import time
import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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


@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


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
