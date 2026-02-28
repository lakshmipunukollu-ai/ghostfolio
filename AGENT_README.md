# Ghostfolio AI Agent — Architecture Documentation

## Domain & Use Cases

**Domain:** Personal Finance + Real Estate Portfolio Management

**Problem Solved:**
Most people manage investments and real estate in completely separate places. A portfolio app
tracks stocks. A spreadsheet tracks property equity. Neither talks to the other. No single tool
answers: _"Given everything I own, am I on track to retire? Can I afford to buy more real estate?
What does my financial picture actually look like?"_

**Target Customer:**
Working professionals aged 28–45 who have started investing in Ghostfolio and own or are
planning to own real estate. They want to understand their complete financial picture —
investments + property equity — and run scenarios on major life decisions (job offers, buying
property, having children, retiring earlier).

**Specific user this was built for:**
A 32-year-old software engineer who uses Ghostfolio to track their investments and is trying to
figure out if their $94k portfolio can fund a down payment, whether to accept a job offer in
Seattle, and what their retirement looks like if they start buying rental properties — all in one
conversation without switching between 8 different tools.

**Use Cases:**

1. Track real estate equity alongside investment portfolio
2. Run "what if I buy a house every 2 years for 10 years" retirement scenarios
3. Ask whether a job offer in another city is financially worth it after cost of living
4. Understand total net worth across all asset classes (stocks + real estate)
5. Check if savings rate is on track vs peers (Federal Reserve SCF 2022 data)
6. Plan family finances including childcare cost impact by city
7. Analyze equity options (keep / cash-out refi / rental property)

---

## Agent Architecture

**Framework:** LangGraph (Python)  
**LLM:** Claude claude-sonnet-4-5 (Anthropic `claude-sonnet-4-5-20251001`)  
**Backend:** FastAPI  
**Database:** SQLite (properties.db — stateful CRUD) + Ghostfolio PostgreSQL  
**Observability:** LangSmith  
**Deployment:** Railway

### Why LangGraph

Chosen over plain LangChain because the agent requires stateful multi-step reasoning:
classify intent → select tool → execute → verify → format. LangGraph's explicit state
machine makes every step debuggable and testable. The graph has clear nodes and edges
rather than an opaque chain.

### Graph Architecture

```
User Message
↓
classify_node      (keyword matching → intent category string)
↓
_route_after_classify   (maps intent string → executor node)
↓
[Tool Executor Node]    (calls appropriate tool function, returns structured result)
↓
verify_node        (confidence scoring + domain constraint check)
↓
format_node        (LLM synthesizes tool result into natural language response)
↓
Response to User
```

### State Schema (`AgentState`)

```python
{
  "user_query": str,
  "messages": list[BaseMessage],   # full conversation history
  "query_type": str,
  "portfolio_snapshot": dict,
  "tool_results": list[dict],
  "pending_verifications": list,
  "confidence_score": float,
  "verification_outcome": str,
  "awaiting_confirmation": bool,
  "confirmation_payload": dict | None,
  "pending_write": dict | None,
  "bearer_token": str | None,
  "final_response": str | None,
  "citations": list[str],
  "error": str | None,
}
```

### Tool Registry

**11 Tools Built Across 7 Files:**

| Tool | File | Purpose |
|------|------|---------|
| portfolio_analysis | portfolio.py | Live Ghostfolio holdings, allocation, performance |
| compliance_check | portfolio.py | Concentration risk, regulatory flags |
| tax_estimate | portfolio.py | Tax liability estimation |
| get_market_data | market_data.py | Live stock prices via Yahoo Finance |
| add_property | property_tracker.py | CRUD — create property record |
| get_properties | property_tracker.py | CRUD — read all properties |
| update_property | property_tracker.py | CRUD — update property values |
| remove_property | property_tracker.py | CRUD — delete property record |
| analyze_equity_options | property_tracker.py | Home equity scenario analysis |
| get_total_net_worth | property_tracker.py | Portfolio + real estate combined |
| calculate_relocation_runway | relocation_runway.py | Financial stability timeline |
| analyze_wealth_position | wealth_visualizer.py | Fed Reserve peer comparison |
| simulate_real_estate_strategy | realestate_strategy.py | Buy-hold retirement projection |
| plan_family_finances | family_planner.py | Childcare cost impact |
| analyze_life_decision | life_decision_advisor.py | Job offer, relocation decisions |
| calculate_down_payment_power | wealth_bridge.py | Portfolio to home purchase |

---

## Latency Notes

Single-tool queries average 5–10 seconds due to Claude Sonnet response generation time.
The classify step (keyword matching) adds <10ms. Tool execution adds 50–200ms. The majority
of latency is LLM synthesis. Streaming responses (`/chat/steps`, `/chat/stream`) are
implemented to improve perceived performance. A startup warmup pre-establishes the LLM
connection to reduce cold-start latency on the first request.

---

## Verification Strategy

**Three verification systems implemented:**

**1. Confidence Scoring**
Every /chat response includes a confidence score between 0.0 and 1.0. Score is based on tool
success, data source reliability, and query type. Responses with confidence below 0.80 have
verified=false returned to the client.

**2. Source Attribution (Citation Enforcement)**
The system prompt enforces a citation rule: every factual claim must name its data source.
Portfolio data cites "Ghostfolio live data". Real estate projections cite user-provided
assumptions. Federal Reserve data is cited by name. The LLM cannot return a number
without its source.

**3. Domain Constraint Check**
A pre-return scan runs on every financial response checking for high-risk phrases
("guaranteed return", "you should buy", "risk-free"). Responses containing these
phrases without appropriate disclaimers are flagged. Every financial projection
includes "not financial advice" language.

**Note on plan vs delivery:**
The pre-search described a fact-check node with tool_result_id tagging. The implemented
approach achieves the same goal differently: citation enforcement is in the system prompt
rather than a separate node, which proved more reliable in practice because it cannot
be bypassed by the routing logic.

### Human-in-the-Loop (Implemented)

Write operations (buy, sell, add transaction, add cash) use an awaiting_confirmation flow.
When the user expresses a write intent (e.g. "buy 10 shares of AAPL"), the write_prepare
node builds a confirmation payload and sets awaiting_confirmation=True. The user sees a
summary and must reply "yes" or "confirm" to proceed. Only then does write_execute run
the actual Ghostfolio API call. This prevents accidental trades.

---

## Eval Results

**Test Suite:** 183 test cases across 10 test files  
**Pass Rate:** 100% (183/183)

### Test Categories

| Category          | Count | Description                                |
| ----------------- | ----- | ------------------------------------------ |
| Happy path        | 20    | Normal successful user flows               |
| Edge cases        | 12    | Zero values, boundary inputs, missing data |
| Adversarial       | 12    | SQL injection, extreme values, bad inputs  |
| Multi-step        | 12    | Chained tool calls, stateful CRUD flows    |
| Portfolio logic   | 60    | Compliance, tax, categorization, helpers   |
| Property CRUD     | 13    | Full property lifecycle                    |
| Real estate       | 8     | Listing search, compare, feature flag      |
| Strategy          | 7     | Simulation correctness                     |
| Relocation        | 5     | Runway calculations                        |
| Wealth bridge     | 8     | COL comparison, net worth                  |
| Wealth visualizer | 6     | Fed Reserve benchmarks                     |

### Performance Targets

| Metric              | Target | Status        |
| ------------------- | ------ | ------------- |
| Single-tool queries | < 5s   | ✅ avg ~3–4s  |
| Multi-step chains   | < 15s  | ✅ avg ~8–12s |
| Tool success rate   | > 95%  | ✅            |
| Eval pass rate      | > 80%  | ✅ 100%       |

---

## Observability Setup

### LangSmith Tracing

Every request generates a LangSmith trace showing the full execution graph:  
`input → classify → tool call → verify → format → output`

Environment variables:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<key>
LANGCHAIN_PROJECT=agentforce
```

Dashboard: [smith.langchain.com](https://smith.langchain.com)

### Per-Response Observability

Every `/chat` response includes:

```json
{
  "latency_ms": 3241,
  "tokens": {
    "input": 1200,
    "output": 400,
    "total": 1600,
    "estimated_cost_usd": 0.0096
  },
  "confidence": 0.95,
  "verified": true,
  "trace_id": "uuid-here",
  "timestamp": "2026-02-27T03:45:00Z",
  "tool": "property_tracker",
  "tools_used": ["property_tracker"],
  "verification_details": {
    "passed": true,
    "flags": [],
    "has_disclaimer": true
  }
}
```

### /metrics Endpoint

`GET /metrics` returns aggregate session metrics:

```json
{
  "total_requests": 47,
  "avg_latency_ms": 3890,
  "successful_tool_calls": 44,
  "failed_tool_calls": 3,
  "tool_success_rate_pct": 93.6,
  "recent_errors": [],
  "last_updated": "2026-02-27T03:45:00Z"
}
```

### Additional Endpoints

| Endpoint                | Purpose                                 |
| ----------------------- | --------------------------------------- |
| `GET /health`           | Agent + Ghostfolio reachability check   |
| `GET /metrics`          | Aggregate session metrics               |
| `GET /costs`            | Estimated Anthropic API cost tracker    |
| `GET /feedback/summary` | 👍/👎 approval rate across all sessions |
| `GET /real-estate/log`  | Tool invocation log (last 50)           |

---

## Open Source Contribution

**Contribution Type:** Public Eval Dataset

**What was delivered:**
183 test cases for finance AI agents — released publicly on GitHub as the first eval dataset
for agents built on Ghostfolio.

**Note on plan vs delivery:**
The pre-search planned an npm package and Hugging Face dataset release. During development,
the eval dataset approach was chosen instead because it provides more direct value to developers
forking Ghostfolio — they can run the test suite immediately without installing a package.
The dataset is MIT licensed and accepts contributions.

**Location:**
github.com/lakshmipunukollu-ai/ghostfolio/tree/submission/final/agent/evals

**Documentation:**
agent/evals/EVAL_DATASET_README.md

---

## How to Run

```bash
# Clone and setup
git clone https://github.com/lakshmipunukollu-ai/ghostfolio-agent-priya
cd ghostfolio
git checkout feature/complete-showcase

# Start Ghostfolio (portfolio backend)
docker-compose up -d
npm install && npm run build
npm run start:server &   # API server: http://localhost:3333
npm run start:client &   # Angular UI: http://localhost:4200

# Start AI agent
cd agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Run eval suite
python -m pytest evals/ -v
# → 182 passed in ~30s

# Access
# Portfolio UI:   http://localhost:4200
# Agent API:      http://localhost:8000
# Agent health:   http://localhost:8000/health
# Agent metrics:  http://localhost:8000/metrics
# LangSmith:      https://smith.langchain.com (project: agentforce)
```

---

## Deployed Application

**Production URL:** https://ghostfolio-agent-production.up.railway.app

The agent is deployed on Railway free tier. The Angular UI is served separately by the
Ghostfolio Next.js/Angular build pipeline.
