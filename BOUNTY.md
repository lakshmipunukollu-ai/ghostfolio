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

A user asks one question:

> "I have a job offer in Tokyo for $200k. I currently make $120k in Austin.
> Is it worth it, and could I ever afford to buy there?"

The agent:

1. Reads their live $94k portfolio from Ghostfolio
2. Fetches Tokyo cost of living + housing from Teleport API
3. Calculates real purchasing power of Tokyo offer vs Austin salary
4. Shows down payment power across Austin vs Tokyo markets
5. Returns clear recommendation in plain English

This is not possible in any other portfolio app. It requires live portfolio data

- real MLS data + global city data in the same agent with shared context across
  turns.

---

## Suggestion Chips (UI)

Three rows of suggestion chips, visible before first message:

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
```

---

## Evals & Verification

- **89 passing tests total** (81 existing + 8 new wealth bridge tests)
- 8 wealth bridge specific tests:
  - Down payment power at $94k portfolio
  - Small portfolio cannot afford safe down payment
  - Seattle $180k offer is NOT a real raise vs Austin $120k
  - SF $250k offer IS a real raise vs Austin $80k
  - Global city (London) comparison returns all required fields
  - Full property CRUD cycle (CREATE → READ → UPDATE → DELETE)
  - Net worth combines portfolio + real estate equity correctly
  - Teleport fallback works when API unavailable
- LangSmith tracing active at smith.langchain.com
- `/real-estate/log` observability endpoint
- Structured error codes on all tool failures (`REAL_ESTATE_PROVIDER_UNAVAILABLE`,
  `PROPERTY_TRACKER_NOT_FOUND`, `PROPERTY_TRACKER_INVALID_INPUT`, etc.)
- All tools registered in LangGraph with conversation history maintained
- Feature flag: `ENABLE_REAL_ESTATE=true` activates all real estate + wealth bridge features

---

## New Files Added in This Submission

| File                                | Purpose                                            |
| ----------------------------------- | -------------------------------------------------- |
| `agent/tools/teleport_api.py`       | Global city COL + housing data (200+ cities)       |
| `agent/tools/wealth_bridge.py`      | Down payment power + job offer COL calculator      |
| `agent/evals/test_wealth_bridge.py` | 8 new tests for wealth bridge features             |
| `agent/data/`                       | SQLite database directory for property persistence |
| `BOUNTY.md`                         | This file                                          |

## Modified Files

| File                                     | Change                                                   |
| ---------------------------------------- | -------------------------------------------------------- |
| `agent/tools/real_estate.py`             | Expose real ACTRIS data_source in responses + TX footer  |
| `agent/tools/property_tracker.py`        | Full SQLite CRUD + update_property + get_total_net_worth |
| `agent/graph.py`                         | Wealth bridge routes + property update/remove routes     |
| `apps/client/.../ai-chat.component.html` | Row 3 wealth bridge suggestion chips                     |
| `apps/client/.../ai-chat.component.scss` | Amber gold chip styling for Row 3                        |
