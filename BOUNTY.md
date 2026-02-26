# AgentForge Bounty — $500 Submission

## The Customer

Tech professionals anywhere in the world evaluating a job offer, relocation,
or first home purchase. Specifically: someone with investments in Ghostfolio
who wants to know:

- "Is this job offer in Seattle/London/Tokyo actually a real raise after cost of living?"
- "Can my portfolio fund a down payment? Where can I afford?"
- "What is my total net worth including my home equity?"

**The pain:** "I have money in the market. I got a $180k offer in Seattle.
I don't know if I can afford to move, whether I can buy a house, or if the
raise is even real."

---

## The Features

### 1. Portfolio → Down Payment Bridge

Reads the user's live Ghostfolio portfolio and calculates exactly which housing
markets they can afford at 20% down with monthly payment estimates and rent vs
buy comparison. Works for Austin (real MLS data) and any city worldwide
(Teleport API).

### 2. Job Offer Affordability Calculator

Takes any salary offer and destination city anywhere in the world, adjusts for
cost of living, and tells the user whether it is a real raise in purchasing
power terms. Covers 200+ cities via Teleport API + real Austin MLS data.
Handles state income tax comparison automatically.

### 3. Property Tracker — Full CRUD

Users log owned properties, track equity, monitor appreciation. Agent supports
create, read, update, and delete via natural language. Stored in SQLite —
persists across sessions. Soft-delete preserves audit trail.

### 4. Unified Net Worth View

Agent combines live investment portfolio + real estate equity into one complete
financial picture in a single conversation turn.

### 5. Relocation Runway Calculator

Calculates month-by-month how long until the user
rebuilds emergency fund, reaches a down payment,
and feels financially stable after any relocation.
Works for any two cities globally via Teleport API

- ACTRIS Austin data.

### 6. Wealth Gap Visualizer

Compares actual net worth against Federal Reserve
median wealth by age group. Projects retirement income
at current savings rate. Shows what-if scenarios.
Source: Federal Reserve Survey of Consumer Finances 2022.

### 7. Life Decision Advisor

Orchestrates all tools into one complete recommendation
for any major life decision — job offer, relocation,
home purchase, rent vs buy. Returns structured verdict
with tradeoffs, confidence level, and next steps.

### 8. Equity Unlock Advisor

For homeowners: models three 10-year options for home
equity — leave untouched, cash-out refi and invest,
or use as rental property down payment. Uses real Austin
appreciation data and current mortgage rates.

### 9. Family Financial Planner

Models financial impact of having children for any city
worldwide. Covers 25+ US cities and international cities
including European subsidized childcare. Shows income
needed, cost breakdown, alternatives, and international
comparisons (Berlin $333/mo vs Austin $1,500/mo).

---

## The Data Sources

### ACTRIS / Unlock MLS — January 2026 (Austin TX)

- 7 counties: City of Austin, Travis County, Williamson County, Hays County,
  Bastrop County, Caldwell County, Austin-Round Rock-San Marcos MSA
- Provided by the developer — a licensed Austin real estate agent (ACTRIS member)
- Fields: ListPrice, DaysOnMarket, MonthsOfInventory, MedianRentMonthly,
  CloseToListRatio, PendingSalesYoY, ClosedSalesYoY, AffordabilityScore
- Schema follows RESO Web API naming — live API swap requires zero refactoring
- Footer appended to every Texas response:
  `📊 Source: ACTRIS/Unlock MLS · January 2026 · Verified by licensed Austin real estate agent`

**Key January 2026 figures:**

| Market            | Median Price | DOM | Months Inventory | Rent/mo |
| ----------------- | ------------ | --- | ---------------- | ------- |
| City of Austin    | $522,500     | 82  | 3.9              | $2,100  |
| Travis County     | $445,000     | 87  | 3.9              | $2,100  |
| Austin MSA        | $400,495     | 89  | 4.0              | $2,000  |
| Williamson County | $403,500     | 92  | 3.5              | $1,995  |
| Hays County       | $344,500     | 86  | 4.4              | $1,937  |
| Bastrop County    | $335,970     | 109 | 5.8              | $1,860  |
| Caldwell County   | $237,491     | 73  | 8.4              | $1,750  |

### Teleport API (global — 200+ cities, free, no auth)

- Endpoint: `api.teleport.org`
- Covers: cost of living, housing costs, quality of life scores for cities
  worldwide including US, Europe, Asia, Australia, Canada, Latin America
- Functions: `search_city_slug()` + `get_city_housing_data()`
- Returns normalized schema compatible with Austin ACTRIS data structure
- Fallback: hardcoded data for 23 major cities if API unavailable
- Used by wealth_bridge for COL-adjusted salary calculations

### Ghostfolio Portfolio API

- Live portfolio holdings, total value, performance metrics
- Connected via bearer token auth (per-user, passed from Angular frontend)
- Used to calculate real purchasing power for down payment analysis

---

## The Impact

A user asks: "I have a $150k offer in Berlin, I make
$120k in Austin, I have $94k invested, I want kids in
2 years — should I go?" The agent reads their live
portfolio, calculates real purchasing power of the Berlin
offer, shows the relocation runway, compares German
childcare ($333/mo) vs Austin ($1,500/mo), checks their
wealth position vs Fed Reserve peers, and returns a
complete recommendation with tradeoffs — in one
conversation using live data from three sources.

---

## Suggestion Chips (UI)

Four rows of suggestion chips, visible before first message:

**Row 1 — Portfolio (always shown):**

- 📈 My portfolio performance
- ⚠️ Any concentration risk?
- 💰 Estimate my taxes

**Row 2 — Real Estate (when `enableRealEstate=true`):**

- 🏠 Austin under $500k
- 📊 Austin vs Denver
- 🏘️ SF snapshot

**Row 3 — Wealth Bridge (when `enableRealEstate=true`):**

- 💰 Can my portfolio buy a house?
- ✈️ Is my job offer a real raise?
- 🌍 Cost of living in Tokyo

**Row 4 — Life Decisions (when `enableRealEstate=true`):**

- ⏱️ How long to feel stable if I move?
- 📊 Am I ahead or behind financially?
- 👶 Can I afford to have kids?

---

## Tool Architecture

```
wealth_bridge.py
├── calculate_down_payment_power(portfolio_value, cities)
│     → 7 Austin markets (ACTRIS) or any cities (Teleport)
│     → can_afford_full / conservative / safe + monthly payment
│     → rent vs buy comparison + break-even years
├── calculate_job_offer_affordability(salaries, cities)
│     → COL-adjusted purchasing power for any two cities worldwide
│     → state income tax comparison
│     → verdict + breakeven salary needed
└── get_portfolio_real_estate_summary()
      → reads live Ghostfolio portfolio + runs down payment calc

property_tracker.py
├── add_property(address, prices, mortgage)
├── get_properties() / list_properties()
├── update_property(id, new_values)
├── remove_property(id)          ← soft delete
└── get_total_net_worth(portfolio_value)

real_estate.py (Austin — real ACTRIS MLS data)
├── search_listings(query, filters)
├── get_neighborhood_snapshot(location)
├── compare_neighborhoods(city_a, city_b)
└── get_listing_details(listing_id)

teleport_api.py (global — 200+ cities)
├── search_city_slug(city_name)   ← resolves to Teleport slug
└── get_city_housing_data(city_name)
      → live Teleport API → normalized schema → fallback if down

relocation_runway.py
└── calculate_relocation_runway(salaries, cities, portfolio_value)
      → months to 3mo/6mo emergency fund + down payment
      → compare stay vs move milestones

wealth_visualizer.py
└── analyze_wealth_position(portfolio, age, income, ...)
      → Fed Reserve percentile + retirement projection
      → what-if: save more / retire earlier

life_decision_advisor.py
└── analyze_life_decision(decision_type, user_context)
      → orchestrates wealth_bridge + runway + visualizer
      → returns verdict + tradeoffs + next steps

family_planner.py
└── plan_family_finances(city, income, ...)
      → childcare costs for 25+ cities (US + global)
      → income impact + alternatives + international comparison
```

---

## Evals & Verification

- **115 passing tests total**
- Tests by feature:
  - Down payment power at $94k portfolio
  - Small portfolio cannot afford safe down payment
  - Seattle $180k offer is NOT a real raise vs Austin $120k
  - SF $250k offer IS a real raise vs Austin $80k
  - Global city (London) comparison returns all required fields
  - Full property CRUD cycle (CREATE → READ → UPDATE → DELETE)
  - Net worth combines portfolio + real estate equity correctly
  - Teleport fallback works when API unavailable
  - 5 relocation runway tests (runway calculator)
  - 6 wealth gap visualizer tests (Fed Reserve benchmarks)
  - 5 life decision advisor tests (tool orchestration)
  - 4 equity unlock advisor tests (3-option analysis)
  - 6 family financial planner tests (global childcare data)
- LangSmith tracing active at smith.langchain.com
- `/real-estate/log` observability endpoint
- Structured error codes on all tool failures (`REAL_ESTATE_PROVIDER_UNAVAILABLE`,
  `PROPERTY_TRACKER_NOT_FOUND`, `PROPERTY_TRACKER_INVALID_INPUT`, etc.)
- All tools registered in LangGraph with conversation history maintained
- Feature flag: `ENABLE_REAL_ESTATE=true` activates all real estate + wealth bridge features

---

## New Files Added in This Submission

| File                                        | Purpose                                                |
| ------------------------------------------- | ------------------------------------------------------ |
| `agent/tools/teleport_api.py`               | Global city COL + housing data (200+ cities)           |
| `agent/tools/wealth_bridge.py`              | Down payment power + job offer COL calculator          |
| `agent/tools/relocation_runway.py`          | Month-by-month stability timeline for any relocation   |
| `agent/tools/wealth_visualizer.py`          | Fed Reserve wealth benchmarks + retirement projection  |
| `agent/tools/life_decision_advisor.py`      | Orchestrates tools into complete life decision verdict |
| `agent/tools/family_planner.py`             | Financial impact of children for 25+ cities worldwide  |
| `agent/evals/test_wealth_bridge.py`         | 8 tests for wealth bridge features                     |
| `agent/evals/test_relocation_runway.py`     | 5 tests for relocation runway calculator               |
| `agent/evals/test_wealth_visualizer.py`     | 6 tests for wealth gap visualizer                      |
| `agent/evals/test_life_decision_advisor.py` | 5 tests for life decision advisor                      |
| `agent/evals/test_equity_advisor.py`        | 4 tests for equity unlock advisor                      |
| `agent/evals/test_family_planner.py`        | 6 tests for family financial planner                   |
| `agent/data/`                               | SQLite database directory for property persistence     |
| `BOUNTY.md`                                 | This file                                              |

## Modified Files

| File                                     | Change                                                   |
| ---------------------------------------- | -------------------------------------------------------- |
| `agent/tools/real_estate.py`             | Expose real ACTRIS data_source in responses + TX footer  |
| `agent/tools/property_tracker.py`        | Full SQLite CRUD + analyze_equity_options function       |
| `agent/graph.py`                         | Routes for all 5 new features + wealth bridge + property |
| `apps/client/.../ai-chat.component.html` | Row 3 wealth bridge chips + Row 4 life decision chips    |
| `apps/client/.../ai-chat.component.scss` | Amber gold (Row 3) + purple/violet (Row 4) chip styling  |
