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

### Tool Registry (11 tools across 7 files)

| Tool                                 | File                     | Purpose                               |
| ------------------------------------ | ------------------------ | ------------------------------------- |
| `portfolio_analysis`                 | portfolio.py             | Live Ghostfolio holdings via API      |
| `add_property`                       | property_tracker.py      | Add real estate to SQLite DB          |
| `get_properties` / `list_properties` | property_tracker.py      | List all active properties            |
| `update_property`                    | property_tracker.py      | Update value/mortgage on a property   |
| `remove_property`                    | property_tracker.py      | Soft-delete property                  |
| `analyze_equity_options`             | property_tracker.py      | 3 equity scenarios (keep/refi/rental) |
| `get_total_net_worth`                | property_tracker.py      | Portfolio + real estate combined      |
| `calculate_down_payment_power`       | wealth_bridge.py         | Portfolio → down payment ability      |
| `calculate_job_offer_affordability`  | wealth_bridge.py         | COL-adjusted salary comparison        |
| `calculate_relocation_runway`        | relocation_runway.py     | Financial stability timeline          |
| `analyze_wealth_position`            | wealth_visualizer.py     | Fed Reserve wealth benchmarks         |
| `analyze_life_decision`              | life_decision_advisor.py | Multi-tool orchestrator               |
| `plan_family_finances`               | family_planner.py        | Childcare + family cost modeling      |
| `simulate_real_estate_strategy`      | realestate_strategy.py   | Buy-hold-rent projection              |

---

## Verification Strategy

### 3 Verification Systems Implemented

**Verification 1 — Confidence Scoring** (`main.py::calculate_confidence`)

Every `/chat` response includes a `confidence` score (0.0–1.0). The score is computed
dynamically based on:

- Base: 0.85
- Deduction: −0.20 if tool result contains an error
- Addition: +0.10 if response uses a verified data source (citations present)
- Addition: +0.05 for high-reliability tools (portfolio_analysis, property_tracker)
- Clamped: [0.40, 0.99]

Example: `{"confidence": 0.95, "verified": true}`

**Verification 2 — Source Attribution (Citation Enforcement)** (`graph.py` system prompt)

The LLM system prompt enforces a citation rule for every factual claim:

- Portfolio data → cites `"Ghostfolio live data"`
- Real estate data → cites `"ACTRIS/Unlock MLS January 2026"`
- Federal Reserve benchmarks → cites `"Federal Reserve SCF 2022"`
- User assumptions → cites `"based on your assumption of X%"`
- Projections → flagged as `"not financial advice / estimate only"`

The LLM cannot return a number without naming its source.

**Verification 3 — Domain Constraint Check** (`main.py::check_financial_response`)

Before every response is returned, it is scanned for high-risk financial advice phrases:

```python
HIGH_RISK_PHRASES = [
    "you should buy", "you should sell", "i recommend buying",
    "guaranteed return", "will definitely", "certain to",
    "risk-free", "always profitable",
]
```

If a high-risk phrase is found AND there is no disclaimer present, `verified: false` is
returned in the response. Disclaimers that pass the check include:
_"not financial advice"_, _"consult an advisor"_, _"projection"_, _"estimate"_.

Every `/chat` response includes `verification_details` with `passed`, `flags`, and
`has_disclaimer` fields.

---

## Eval Results

**Test Suite:** 182 test cases across 10 test files  
**Pass Rate:** 100% (182/182)

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

**Contribution Type:** New agent layer + eval dataset as brownfield addition  
**Repository:** [github.com/lakshmipunukollu-ai/ghostfolio-agent-priya](https://github.com/lakshmipunukollu-ai/ghostfolio-agent-priya)  
**Branch:** `feature/complete-showcase`

**What was contributed:**

The complete real estate agent layer (14 tools, 182 tests, full observability setup) is
designed as a reusable brownfield addition to any Ghostfolio fork. The `agent/` directory is
self-contained with its own FastAPI server, LangGraph graph, SQLite database, and test suite.

**Zero changes to Ghostfolio core.** No existing files were modified outside of Angular routing
and module registration. All additions are in:

- `agent/` — the entire AI agent (new directory)
- `apps/client/src/app/pages/` — new Real Estate page (additive)
- `apps/client/src/app/components/` — new AI chat component (additive)

**To contribute back upstream:**

The `agent/` directory could be submitted as a PR to the main Ghostfolio repo as an optional
AI agent add-on. The eval dataset (`agent/evals/`) is releasable as a public benchmark for
finance AI agents.

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
