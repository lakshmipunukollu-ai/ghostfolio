# AgentForge Bounty — $500 Submission

## The Customer

**A 32-year-old software engineer** who uses Ghostfolio to track their $94k investment
portfolio and is trying to figure out:

1. Whether their portfolio can fund a down payment on a home
2. Whether to accept a $180k job offer in Seattle (is it actually a raise after cost of living?)
3. What their retirement looks like if they start buying rental properties now

...all in one conversation, without switching between a portfolio app, a real estate site,
a COL calculator, a spreadsheet, and a financial advisor.

**The specific pain:** _"I have $94k in my Ghostfolio portfolio, I got a job offer in
Seattle, I'm thinking about buying a house, and I want to know if any of this makes sense
together — but every tool I use only knows about one piece."_

This person needs a financial co-pilot that knows about their whole picture — investments,
real estate equity, and major life decisions — and can reason about all three in one place.

---

## The Features

### 1. Portfolio → Down Payment Bridge

Reads the user's live Ghostfolio portfolio and calculates exactly which housing markets they
can afford at 20% down. Compares conservative (60%), full (100%), and safe (80%) scenarios.
Includes monthly payment estimates and rent vs. buy verdict.

### 2. Job Offer Affordability Calculator

Takes any salary offer and destination city, adjusts for cost of living difference, and
tells the user whether it is a real raise in purchasing power. Compares state income tax.
Works for 200+ cities worldwide. Example: `$180k Seattle vs $120k Austin = NOT a real raise
(-$5,593 purchasing power loss after COL adjustment)`.

### 3. Property Tracker — Full CRUD

Users log owned properties, track equity, monitor appreciation over time. The agent supports
all four CRUD operations via natural language:

- **CREATE:** `add_property(address, purchase_price, current_value, mortgage_balance)` → stores in SQLite, returns equity
- **READ:** `get_properties()` → lists all active properties with equity, appreciation, mortgage balance
- **UPDATE:** `update_property(id, current_value=490000)` → recalculates equity after market changes
- **DELETE:** `remove_property(id)` → soft-delete preserving audit trail, property no longer in active list

Persists across sessions in `agent/data/properties.db` (SQLite).

### 4. Unified Net Worth View

Combines live investment portfolio from Ghostfolio API + real estate equity from SQLite into
one complete financial picture. Single conversation turn: "What is my total net worth?"
returns portfolio + all property equity + total.

### 5. Relocation Runway Calculator

Calculates month-by-month timeline until the user rebuilds emergency fund, reaches down
payment, and feels financially stable after any relocation. Works for any two cities globally.

### 6. Wealth Gap Visualizer

Compares actual net worth against Federal Reserve median wealth by age group. Projects
retirement income at current savings rate. Source: Federal Reserve SCF 2022.

### 7. Life Decision Advisor

Orchestrates all tools into one complete recommendation for job offers, relocations, home
purchases, and rent vs. buy decisions. Returns verdict, tradeoffs, confidence level, and
next steps.

### 8. Equity Unlock Advisor

For homeowners: models three 10-year scenarios for home equity — keep untouched, cash-out
refi and invest, or use as rental property down payment.

### 9. Real Estate Strategy Simulator

Simulates buying a home every N years for M years and renting previous ones. Uses the user's
own appreciation/rent assumptions, not guesses. Returns year-by-year net worth projection.

### 10. Family Financial Planner

Models the financial impact of having children for any city. Covers 25+ US cities and
international cities. Shows income needed, childcare cost breakdown, and international
comparisons (Berlin $333/month vs Austin $1,500/month).

---

## Data Sources

### Primary: SQLite Property Database (`agent/data/properties.db`)

**This is the stateful CRUD data the agent uses.** Users add their own properties via
natural language. The data persists in SQLite across sessions. The agent reads, writes,
updates, and soft-deletes property records through 5 tool functions:

```
add_property      → INSERT into properties table
get_properties    → SELECT all active properties
update_property   → UPDATE specific fields (value, mortgage, etc.)
remove_property   → UPDATE is_active=0 (soft delete)
get_total_net_worth → aggregate equity across all active properties
```

The agent accesses this data by calling `property_tracker.py` tool functions through the
LangGraph routing layer. The LangGraph graph classifies the user's intent → routes to the
property tracker node → executes the appropriate CRUD function → returns structured JSON
result → LLM formats into natural language response.

### Supporting: Ghostfolio Portfolio API

Live investment portfolio data (holdings, total value, allocation, performance) fetched
from `http://localhost:3333/api/v1/portfolio` using the user's bearer token. This is the
existing Ghostfolio data the agent is built on top of.

**How accessed:** The agent receives the user's Ghostfolio bearer token from the Angular
frontend, uses it to call the Ghostfolio REST API, and incorporates the live portfolio
data into property-aware calculations (e.g., net worth = portfolio value + real estate equity).

### Supporting: Yahoo Finance

Live stock prices for portfolio performance and YTD calculations. The agent fetches current
prices from Yahoo Finance when computing gains, allocations, and real-time portfolio value.
Used by `portfolio_analysis` to work around Ghostfolio's local Yahoo feed limitations.

### Supporting: Teleport API

Cost of living and housing data for 200+ cities worldwide. Powers the Job Offer
Affordability Calculator and Relocation Runway features. Fetched from
`api.teleport.org` for cities outside Austin; Austin areas use ACTRIS instead.

### Supporting: ACTRIS/Unlock MLS January 2026

Licensed Austin TX real estate market data for listing search and neighborhood comparisons.
Provided by the developer, who is a licensed Austin real estate agent. Embedded in
`agent/tools/real_estate.py` as structured data.

**Usage:** Powers the Portfolio → Down Payment Bridge feature for Austin markets, and the
real estate search/compare features. Cited in agent responses as _"ACTRIS/Unlock MLS
January 2026"_.

### Supporting: Federal Reserve Survey of Consumer Finances 2022

Public data. Age-group wealth percentiles (25th, median, 75th, 90th) from the Fed's most
recent SCF. Hard-coded in `agent/tools/wealth_visualizer.py`.

**Usage:** Powers the Wealth Gap Visualizer. Cited in agent responses as
_"Federal Reserve SCF 2022"_.

---

## The CRUD Operations (Explicit)

| Operation  | Function                                                                 | What It Does                                                                                   |
| ---------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| **CREATE** | `add_property(address, purchase_price, current_value, mortgage_balance)` | Inserts new property into SQLite, calculates equity, returns property dict with ID             |
| **READ**   | `get_properties()` / `list_properties()`                                 | Selects all active properties, returns with equity, appreciation, and summary totals           |
| **UPDATE** | `update_property(id, current_value=..., mortgage_balance=...)`           | Updates specified fields, recalculates equity and appreciation_pct                             |
| **DELETE** | `remove_property(id)`                                                    | Sets `is_active=0` (soft delete), property no longer appears in active list but data preserved |

**Bonus:** `get_total_net_worth(portfolio_value)` aggregates equity across all active
properties + adds investment portfolio → returns complete financial picture.

---

## The Impact

The app solves a real problem. Most people with both investments and real estate have no
single place to see the complete picture or run scenarios on their own numbers.

A user adds their home (bought $400k, worth $480k, mortgage $310k) and immediately sees
$170k equity tracked alongside their $94k investment portfolio — **total net worth $264k
in one view.**

They then ask: _"What if I buy a home every 2 years for the next 10 years and rent the
previous one?"_

The agent asks what appreciation and rent assumptions they want to use — because we do not
guess at numbers for markets we cannot verify. The user says "moderate — 4% appreciation."
The agent runs the projection using their actual portfolio balance, their income, and their
assumptions, and returns a year-by-year picture of what their net worth could look like at
retirement.

This is a conversation people pay financial advisors **hundreds of dollars per hour** to
have. This app does it in 30 seconds — honestly, with the user's own numbers, and with
clear disclaimers about what is a projection vs. a prediction.

---

## Eval & Verification

- **182 tests** (100% pass rate) covering portfolio logic, CRUD flows, strategy simulation,
  edge cases, adversarial inputs, and multi-step chains
- **3 verification systems:** confidence scoring, source attribution (citation enforcement),
  and domain constraint check (no guaranteed-return language)
- **LangSmith tracing** active — every request traced at `smith.langchain.com`
- All tool failures return structured error codes (e.g., `PROPERTY_TRACKER_NOT_FOUND`)
- Conversation history maintained across all turns via `AgentState.messages`
