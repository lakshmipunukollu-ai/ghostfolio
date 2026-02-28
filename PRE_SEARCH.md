---
> **Note:** This pre-search was completed before development began. The final implementation
> evolved from this plan — notably, 11 tools were built (vs 5 planned) with a real estate portfolio
> tracking focus added alongside the original portfolio analysis scope. The open source
> contribution was delivered as a public GitHub eval dataset rather than an npm package.
> See AGENT_README.md for final implementation details.
---

# Pre-Search: Ghostfolio AI Agent Bounty

## Objective

Design an AI agent layer for Ghostfolio that answers portfolio + life decision questions in a single conversation. Target: 32-year-old software engineer with $94k portfolio, job offer in Seattle, and interest in real estate.

## Planned Deliverables

### 1. Core Tools (5 planned)

| Tool | Purpose |
|------|---------|
| portfolio_analysis | Live Ghostfolio holdings, allocation, performance |
| compliance_check | Concentration risk, regulatory flags |
| tax_estimate | Capital gains estimation, wash-sale awareness |
| market_data | Live stock prices |
| transaction_query | Trade history retrieval |

### 2. Architecture

- **Framework:** LangGraph (state machine: classify → tool → verify → format)
- **LLM:** Claude Sonnet
- **Verification:** Confidence scoring, citation enforcement, domain constraint check
- **Human-in-the-loop:** awaiting_confirmation state for high-risk queries (e.g. "should I sell?")

### 3. Open Source Contribution (Planned)

- **Format:** npm package for Ghostfolio integration
- **Dataset:** Hugging Face eval dataset for finance AI agents
- **License:** MIT

### 4. Data Sources

- Ghostfolio REST API (portfolio, activities)
- Yahoo Finance (market data)
- Federal Reserve SCF 2022 (wealth benchmarks)
- SQLite for property tracking (added during development)

### 5. Verification Strategy (Planned)

- Fact-check node with tool_result_id tagging
- Citation rule: every number must name its source
- High-risk phrase scan before response return

### 6. Risks & Mitigations

| Risk | Mitigation |
|------|-------------|
| Hallucinated numbers | Citation enforcement in system prompt |
| Investment advice | Domain constraint check, disclaimer language |
| Wash-sale errors | tax_estimate tool with IRS rule awareness |

## Implementation Notes

The pre-search assumed a smaller scope (5 tools) and npm/Hugging Face release. Development expanded to 11+ tools with real estate CRUD, relocation runway, family planner, and wealth visualizer. The eval dataset was released on GitHub instead of Hugging Face to provide direct value to Ghostfolio fork developers.
