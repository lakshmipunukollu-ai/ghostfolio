---
# AgentForge Pre-Search
## Finance Domain · Ghostfolio · AI Portfolio Intelligence Agent
### G4 Cohort · Week 2 · February 2026

> **Note on plan vs delivery:** This pre-search was
> completed before development began. The final
> implementation evolved from this plan:
> - 16 tools were built (vs 5 planned) with real
>   estate portfolio tracking added to the original
>   portfolio analysis scope
> - Human-in-the-loop was implemented via an
>   awaiting_confirmation state in the graph
> - Wash-sale enforcement was implemented in
>   tax_estimate.py
> - Open source contribution was delivered as a
>   public GitHub eval dataset (183 tests) rather
>   than an npm package
> - See AGENT_README.md for final implementation

---

## Phase 1: Domain & Constraints

### Use Cases
- Portfolio health check: "How diversified am I?
  Where am I overexposed?"
- Performance Q&A: "What's my YTD return vs S&P 500?"
- Tax-loss harvesting: Surface unrealized losses to
  offset gains; flag wash-sale violations (30-day IRS rule)
- Natural language activity log: "Show me all my MSFT
  trades this year" → query Ghostfolio activities
- Compliance alerts: Concentration risk >20% single
  holding, missing cost basis warnings

### Ghostfolio — Actual API Integration Points
Stack: Angular frontend · NestJS backend ·
PostgreSQL + Prisma ORM · Redis cache · TypeScript

Data sources: Ghostfolio PostgreSQL DB (primary),
Yahoo Finance API (market data), IRS published tax
rules (compliance). All external data fetched at
runtime — no static snapshots.

### 4. Team & Skill Constraints
- Domain experience: Licensed real estate agent —
  strong knowledge of real estate use cases
- Framework familiarity: New to LangGraph,
  learned during build
- Biggest risk: Python context switch on Day 1
  Mitigation: minimal LangGraph hello world before
  touching domain logic

### 2. Scale & Performance
- Expected query volume: 5-20 queries/user/day
- Acceptable latency: Under 10 seconds for LLM synthesis
- Concurrent users: FastAPI async handles moderate load
- Cost constraint: Under $0.02 per query

### Reliability Requirements
- Cost of wrong answer: High — financial decisions
  have real consequences
- Non-negotiable: All claims cite sources, confidence
  score on every response, no specific advice without
  disclaimer
- Human-in-the-loop: Implemented for high-risk queries
- Audit: LangSmith traces every request

### Performance Targets
- Single-tool latency: <5s target (actual: 8-10s due
  to Claude Sonnet synthesis, documented)
- Tool success rate: >95%
- Eval pass rate: >80% (actual: 100%)
- Hallucination rate: <5% (citation enforcement)

---

## Phase 2: Architecture

### Framework & LLM Decisions
- Framework: LangGraph (Python)
- LLM: Claude Sonnet (claude-sonnet-4-20250514)
- Observability: LangSmith
- Backend: FastAPI
- Database: PostgreSQL (Ghostfolio) + SQLite (properties)
- Deployment: Railway

### Why LangGraph
Chosen over plain LangChain because financial workflows
require explicit state management: loop-back for
human confirmation, conditional branching by query type,
and mid-graph verification before any response returns.

### LangGraph State Schema
Core state persists across every node:
- query_type: routes to correct tool executor
- tool_result: structured output from tool call
- confidence_score: quantified certainty per response
- awaiting_confirmation: pauses graph for high-risk queries
- portfolio_snapshot: immutable per request for verification
- messages: full conversation history for LLM context

Key design: portfolio_snapshot is immutable once set —
verification node compares all numeric claims against it.
awaiting_confirmation pauses the graph at the
human-in-the-loop node; resumes only on explicit
user confirmation. confidence_score below 0.6 routes
to clarification node.

### Agent Tools (Final: 16 tools across 7 files)
Original plan was 5 core portfolio tools.
Implementation expanded to 16 tools adding real estate,
wealth planning, and life decision capabilities.

See AGENT_README.md for complete tool table.

Integration pattern: LangGraph agent authenticates
with Ghostfolio via anonymous token endpoint, then
calls portfolio/activity endpoints with Bearer token.
No NestJS modification required.

Error handling: every tool returns structured error
dict on failure — never throws to the agent.

### Verification Stack (3 Layers Implemented)
1. Confidence Scoring: Every response scored 0.0-1.0.
   Below 0.80 returns verified=false to client.
2. Citation Enforcement: System prompt requires every
   factual claim to name its data source. LLM cannot
   return a number without citation.
3. Domain Constraint Check: Pre-return scan for
   high-risk phrases. Flags responses making specific
   investment recommendations without disclaimers.

Note: Pre-search planned fact-check node with
tool_result_id tagging. Citation enforcement via
system prompt proved more reliable in practice
because it cannot be bypassed by routing logic.

### Observability Plan
Tool: LangSmith — native to LangGraph.
Metrics per request:
- Full reasoning trace
- LLM + tool latency breakdown
- Input/output tokens + rolling cost
- Tool success/failure rate by tool name
- Verification outcome (pass/flag/escalate)
- User thumbs up/down linked to trace_id
- /metrics endpoint for aggregate stats
- eval_history.json for regression detection

---

## Phase 3: Evaluation Framework

### Test Suite (183 tests, 100% pass rate)
Categories:
- Happy path: 20 tests
- Edge cases: 14 tests
- Adversarial: 14 tests
- Multi-step: 13 tests
- Additional tool unit tests: 122 tests

All integration and eval tests run against
deterministic data — fully reproducible,
eliminates flakiness from live market data.

### Testing Strategy
- Unit tests for every tool
- Integration tests for multi-step chains
- Adversarial tests: SQL injection, prompt injection,
  extreme values, malformed inputs
- Regression: save_eval_results.py stores pass rate
  history in eval_history.json, flags drops

---

## Failure Modes & Security

### Failure Modes
- Tool fails: returns error dict, LLM synthesizes
  graceful response
- Ambiguous query: keyword classifier falls back to
  portfolio_analysis as safe default
- Rate limiting: not implemented at MVP
- Graceful degradation: every tool has try/except,
  log_error() captures context and stack trace

### Security
- API keys: environment variables only, never logged
- Data leakage: portfolio data scoped per authenticated
  user, agent context cleared between sessions
- Prompt injection: user input sanitized before prompt
  construction; system prompt resists override instructions
- Audit logging: every tool call + result stored with
  timestamp; LangSmith retains traces

---

## AI Cost Analysis

### Development Spend Estimate
- Estimated queries during development: ~2,000
- Average tokens per query: 1,600 input + 400 output
- Cost per query: ~$0.01 (Claude Sonnet pricing)
- Total development cost estimate: ~$20-40
- LangSmith: Free tier
- Railway: Free tier

### Production Cost Projections
Assumptions: 10 queries/user/day, 2,000 input tokens,
500 output tokens, 1.5 avg tool calls

| Scale | Monthly Cost |
|-------|-------------|
| 100 users | ~$18/mo |
| 1,000 users | ~$180/mo |
| 10,000 users | ~$1,800/mo |
| 100,000 users | ~$18,000/mo* |

*At 100k users: semantic caching + Haiku for simple
queries cuts LLM cost ~40%. Real target ~$11k/mo.

---

## Open Source Contribution

Delivered: 183-test public eval dataset for finance
AI agents — first eval suite for Ghostfolio agents.
MIT licensed, accepts contributions.

Location: agent/evals/ on submission/final branch
Documentation: agent/evals/EVAL_DATASET_README.md

Note: Pre-search planned npm package + Hugging Face.
GitHub eval dataset was chosen instead — more directly
useful to developers forking Ghostfolio since they
can run the test suite immediately.

---

## Deployment & Operations

- Hosting: Railway (FastAPI agent + Ghostfolio)
- CI/CD: Manual deploy via Railway GitHub integration
- Monitoring: LangSmith dashboard + /metrics endpoint
- Rollback: git revert + Railway auto-deploys from main

---

## Iteration Planning

- User feedback: thumbs up/down in chat UI, each vote
  stored with LangSmith trace_id
- Improvement cycle: eval failures → tool fixes →
  re-run suite → confirm improvement
- Regression gate: new feature must not drop eval pass rate
- Model updates: full eval suite runs against new model
  before switching in production
---
