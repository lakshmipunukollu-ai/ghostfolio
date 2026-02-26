# Ghostfolio AI Agent — AgentForge Integration

## What I Built

A LangGraph-powered portfolio assistant embedded directly inside Ghostfolio — a production open-source wealth management app. The agent runs as a FastAPI sidecar and adds a floating AI chat panel, nine specialized tools, and an optional real estate market feature, all as a brownfield addition that leaves the existing codebase untouched.

---

## Architecture

```
Angular UI (port 4200)
  └── GfAiChatComponent
        ├── AiChatService (event bus for Real Estate nav → chat)
        └── HTTP calls
              │
              ▼
        FastAPI Agent (port 8000)   ← agent/main.py
              │
              ▼
        LangGraph Graph             ← agent/graph.py
              │
        ┌─────┴──────────────────────────────────────────┐
        │  9 Tools (agent/tools/)                        │
        ├── portfolio_analysis      portfolio data        │
        ├── transaction_query       filter transactions   │
        ├── compliance_check        concentration risk    │
        ├── market_data             live price context    │
        ├── tax_estimate            capital gains math    │
        ├── write_transaction       record buys/sells     │
        ├── categorize              label transactions    │
        ├── real_estate             city/listing search   │ ← brownfield add
        └── compare_neighborhoods  side-by-side cities   │ ← brownfield add
              │
              ▼
        Ghostfolio REST API (port 3333)
```

---

## How to Run Locally

### Prerequisites

- Node.js 18+, npm
- Python 3.11+
- Ghostfolio account with a bearer token

### Step 1 — Start Ghostfolio

```bash
cd ghostfolio

# Terminal 1 — API server
npm run start:server
# Wait for: "Nest application successfully started"

# Terminal 2 — Angular client
npm run start:client
# Wait for: "Compiled successfully"
```

### Step 2 — Configure the Agent

```bash
cd ghostfolio/agent
cp .env.example .env   # if not already present
```

Edit `.env`:

```
GHOSTFOLIO_BASE_URL=http://localhost:3333
GHOSTFOLIO_BEARER_TOKEN=<your token from Ghostfolio Settings>
ANTHROPIC_API_KEY=<your Anthropic key>
ENABLE_REAL_ESTATE=true
```

### Step 3 — Start the Agent

```bash
cd ghostfolio/agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Wait for: "Application startup complete."
```

### Step 4 — Open the App

Go to `http://localhost:4200` → sign in → click the **Ask AI** button (bottom right).

Portfolio data seeds automatically when the agent detects an empty portfolio — no manual step needed.

---

## Real Estate Feature Flag

The real estate tools are gated behind `ENABLE_REAL_ESTATE` so they can be toggled without any code change.

**Enable:**

```
ENABLE_REAL_ESTATE=true
```

**Disable (default):**

```
ENABLE_REAL_ESTATE=false
```

When enabled:

- A **Real Estate** nav item appears in Ghostfolio's sidebar
- Real estate suggestion chips appear in the chat panel
- The `real_estate` and `compare_neighborhoods` tools are active
- Tool calls are logged to `GET /real-estate/log`

When disabled, all real estate endpoints return a clear `REAL_ESTATE_FEATURE_DISABLED` error — no silent failures.

---

## Test Suite

```bash
cd ghostfolio/agent
source venv/bin/activate

# Run all tests with verbose output
python -m pytest evals/ -v

# Run just the real estate tests
python -m pytest evals/ -v -k "real_estate"

# Run with coverage summary
python -m pytest evals/ -v 2>&1 | tail -10
```

**Coverage:** 68+ test cases across:

- Portfolio analysis accuracy
- Transaction query filtering
- Compliance / concentration risk detection
- Tax estimation logic
- Write operation confirmation flow
- Real estate listing search & filtering
- Neighborhood snapshot data
- City comparison (affordability, yield, DOM)
- Feature flag enforcement

---

## 2-Minute Demo Script

1. **Open** `localhost:4200`, sign in
2. **Click** the floating **Ask AI** button (bottom right) — note the green status dot = agent online
3. **Click** "📈 My portfolio performance" chip → agent calls `portfolio_analysis` + `market_data`; see tool chips on the response
4. **Click** "⚠️ Any concentration risk?" → agent calls `compliance_check`
5. **Click** "💰 Estimate my taxes" → agent calls `tax_estimate`
6. **Type** "buy 5 shares of AAPL at $185" → agent asks for confirmation → click Confirm
7. **Click** "Real Estate" in the sidebar → chat opens with Austin/Denver query pre-filled
8. **Click** "📊 Austin vs Denver" chip → side-by-side comparison with tool chips visible
9. **Click** Clear → suggestion chips reappear

---

## What Makes This a Brownfield Integration

- **Zero changes to Ghostfolio core** — no existing files were modified outside of Angular routing/module registration. The agent is a fully separate FastAPI process.
- **Feature-flagged addition** — `ENABLE_REAL_ESTATE=false` returns the app to its original state with no trace of the real estate feature.
- **Token passthrough** — the agent receives the user's existing Ghostfolio bearer token from the Angular client and uses it for all API calls, so authentication is reused rather than reimplemented.

---

## Observability Endpoints

| Endpoint                | Purpose                                   |
| ----------------------- | ----------------------------------------- |
| `GET /health`           | Agent + Ghostfolio reachability check     |
| `GET /real-estate/log`  | Real estate tool invocation log (last 50) |
| `GET /feedback/summary` | 👍/👎 approval rate across all sessions   |
| `GET /costs`            | Estimated Anthropic API cost tracker      |
