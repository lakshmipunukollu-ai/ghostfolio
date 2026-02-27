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

## Data Sources

**User's own property data** — stored in SQLite,
persists across sessions, full CRUD via natural language

**Ghostfolio portfolio API** — live investment holdings,
total value, performance data

**Federal Reserve Survey of Consumer Finances 2022** —
wealth percentile benchmarks by age group (public data)

**US Dept of Labor + Care.com 2024** — childcare cost
estimates for family planning feature (background data)

**ACTRIS/Unlock MLS January 2026** — Austin TX market
data available as background context when asked
(provided by developer, licensed Austin real estate agent)

---

## The Impact

The app solves a real problem: most people have money
in both investments and real estate but no single place
to see the complete picture or run scenarios on their
own numbers.

A user adds their home (bought $400k, worth $480k,
mortgage $310k) and immediately sees $170k equity
tracked alongside their $94k investment portfolio —
total net worth $264k in one view.

They then ask: "What if I buy a home every 2 years
for the next 10 years and rent the previous one?"

The agent asks what appreciation and rent assumptions
they want to use — because we do not guess at numbers
for markets we cannot verify. The user says "moderate
— 4% appreciation." The agent runs the projection using
their actual portfolio balance, their income, and their
assumptions — and returns a year-by-year picture of
what their net worth could look like at retirement.

This is a conversation people pay financial advisors
hundreds of dollars per hour to have. This app does it
in 30 seconds — honestly, with the user's own numbers,
and with clear disclaimers about what is a projection
vs a prediction.

No market data promises. No city comparisons we cannot
stand behind. Just the user's numbers, their assumptions,
and honest math.

---

## Suggestion Chips (UI)

Four rows of suggestion chips, visible before first message:

**Row 1 — Portfolio (always shown):**

- 📈 My portfolio performance
- ⚠️ Any concentration risk?
- 💰 Estimate my taxes

**Row 2 — Property Tracking (when `enableRealEstate=true`):**

- 🏠 Add my home to track equity
- 📊 Show my total net worth
- 💰 What are my equity options?

**Row 3 — Life Decisions (when `enableRealEstate=true`):**

- 💰 Can my portfolio buy a house?
- ✈️ I have a job offer — is it worth it?
- 🌍 How long until I'm stable if I move?

**Row 4 — Strategy (when `enableRealEstate=true`):**

- 📊 Am I ahead or behind financially?
- 👶 Can I afford to have kids?
- 🏘️ What if I buy a house every 2 years?

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

- **100 fast-passing tests (deterministic, no network)**
- Tests by feature:
  - 60 portfolio tests (holdings, performance, tax, compliance)
  - 13 property tracker tests (full CRUD cycle, equity, net worth)
  - 7 real estate strategy simulator tests (user assumptions, presets, disclaimer)
  - 4 property onboarding tests (add, list, net worth, graceful empty)
  - 6 wealth gap visualizer tests (Fed Reserve benchmarks)
  - 4 equity unlock advisor tests (3-option analysis)
  - 6 family financial planner tests (global childcare data)
  - Additional async integration tests (wealth bridge, relocation runway,
    life decision advisor) that require network access
- LangSmith tracing active at smith.langchain.com
- `/real-estate/log` observability endpoint
- Structured error codes on all tool failures (`REAL_ESTATE_PROVIDER_UNAVAILABLE`,
  `PROPERTY_TRACKER_NOT_FOUND`, `PROPERTY_TRACKER_INVALID_INPUT`, etc.)
- All tools registered in LangGraph with conversation history maintained
- Feature flag: `ENABLE_REAL_ESTATE=true` activates all real estate + wealth bridge features

---

## New Files Added in This Submission

| File                                        | Purpose                                                           |
| ------------------------------------------- | ----------------------------------------------------------------- |
| `agent/tools/teleport_api.py`               | Global city COL + housing data (200+ cities)                      |
| `agent/tools/wealth_bridge.py`              | Down payment power + job offer COL calculator                     |
| `agent/tools/relocation_runway.py`          | Month-by-month stability timeline for any relocation              |
| `agent/tools/wealth_visualizer.py`          | Fed Reserve wealth benchmarks + retirement projection             |
| `agent/tools/life_decision_advisor.py`      | Orchestrates tools into complete life decision verdict            |
| `agent/tools/family_planner.py`             | Financial impact of children for 25+ cities worldwide             |
| `agent/tools/realestate_strategy.py`        | Multi-property buy-and-rent strategy simulator (user assumptions) |
| `agent/evals/test_wealth_bridge.py`         | Integration tests for wealth bridge features                      |
| `agent/evals/test_relocation_runway.py`     | Integration tests for relocation runway calculator                |
| `agent/evals/test_wealth_visualizer.py`     | 6 tests for wealth gap visualizer                                 |
| `agent/evals/test_life_decision_advisor.py` | Integration tests for life decision advisor                       |
| `agent/evals/test_equity_advisor.py`        | 4 tests for equity unlock advisor                                 |
| `agent/evals/test_family_planner.py`        | 6 tests for family financial planner                              |
| `agent/evals/test_realestate_strategy.py`   | 7 tests for strategy simulator (user assumptions, presets)        |
| `agent/evals/test_property_onboarding.py`   | 4 tests for property onboarding flow                              |
| `agent/data/`                               | SQLite database directory for property persistence                |
| `BOUNTY.md`                                 | This file                                                         |

## Modified Files

| File                                     | Change                                                          |
| ---------------------------------------- | --------------------------------------------------------------- |
| `agent/tools/real_estate.py`             | Expose real ACTRIS data_source in responses + TX footer         |
| `agent/tools/property_tracker.py`        | Full SQLite CRUD + analyze_equity_options function              |
| `agent/graph.py`                         | Strategy simulator routing + assumption extraction + onboarding |
| `apps/client/.../ai-chat.component.html` | Personal tracking chips replacing market data chips             |
| `apps/client/.../ai-chat.component.scss` | Amber gold (Row 3) + purple/violet (Row 4) chip styling         |
