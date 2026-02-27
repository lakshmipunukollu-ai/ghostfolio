# AI Cost Analysis

## Model Used

**Claude claude-sonnet-4-5** (`claude-sonnet-4-5-20251001`)

---

## Per-Request Cost Breakdown

### Token Assumptions

| Component                          | Tokens     | Notes                                         |
| ---------------------------------- | ---------- | --------------------------------------------- |
| System prompt                      | ~800       | Tool registry + citation rules + instructions |
| Conversation history (avg 3 turns) | ~200       | Rolled-up prior messages                      |
| User message                       | ~100       | Average query length                          |
| Tool call result                   | ~300       | Structured JSON from tool                     |
| **Total input**                    | **~1,200** |                                               |
| Response generation                | **~400**   | Typical financial explanation                 |

### Claude Sonnet Pricing

| Token Type          | Rate               | Cost per Request                |
| ------------------- | ------------------ | ------------------------------- |
| Input               | $3.00 / 1M tokens  | 1,200 × $0.000003 = **$0.0036** |
| Output              | $15.00 / 1M tokens | 400 × $0.000015 = **$0.006**    |
| **Total per query** |                    | **$0.0096 ≈ $0.01**             |

---

## Development & Testing Costs

### Development Estimate

| Activity                                    | Queries    | Cost     |
| ------------------------------------------- | ---------- | -------- |
| Agent prototyping (classify, route, format) | ~500       | ~$5.00   |
| Tool development + debugging                | ~600       | ~$6.00   |
| Eval suite creation + validation            | ~400       | ~$4.00   |
| UI integration + end-to-end testing         | ~300       | ~$3.00   |
| Deployment + final polish                   | ~200       | ~$2.00   |
| **Total estimated development**             | **~2,000** | **~$20** |

### Infrastructure Costs (Development)

| Service                  | Cost                            |
| ------------------------ | ------------------------------- |
| LangSmith                | Free tier (10,000 traces/month) |
| Railway deployment       | Free tier (sufficient for MVP)  |
| **Total infrastructure** | **$0**                          |

### Total Development Cost

**~$20** (API calls only)

---

## Production Cost Projections

### Assumptions

- 5 queries per user per day (realistic for a personal finance assistant)
- 1,600 tokens average per query (input + output with tool call overhead)
- 1.2× multiplier for tool call metadata overhead
- Effective cost per query: **$0.012** (after overhead)

### Scale Projections

| Scale      | Monthly Users | Daily Queries | Monthly Queries | Monthly API Cost |
| ---------- | ------------- | ------------- | --------------- | ---------------- |
| Starter    | 100           | 500           | 15,000          | **~$18**         |
| Growth     | 1,000         | 5,000         | 150,000         | **~$180**        |
| Scale      | 10,000        | 50,000        | 1,500,000       | **~$1,800**      |
| Enterprise | 100,000       | 500,000       | 15,000,000      | **~$18,000**     |

### Cost Per Feature

| Feature                      | Avg Input Tokens | Avg Output Tokens | Cost/Query  |
| ---------------------------- | ---------------- | ----------------- | ----------- |
| Portfolio analysis           | 1,000            | 400               | ~$0.009     |
| Property tracking (CRUD)     | 600              | 200               | ~$0.005     |
| Strategy simulation          | 1,400            | 600               | ~$0.013     |
| Life decision advisor        | 1,600            | 800               | ~$0.016     |
| Wealth gap visualizer        | 900              | 300               | ~$0.008     |
| Relocation runway            | 1,200            | 500               | ~$0.011     |
| Family planner               | 1,100            | 450               | ~$0.010     |
| **Average across all tools** | **1,114**        | **464**           | **~$0.010** |

---

## Cost Optimization Strategies

### 1. Query-Level Caching (saves ~30%)

Common queries like "Austin market data", "Federal Reserve benchmarks", and "What is my portfolio?"
can be cached with a 24-hour TTL. This reduces repeat Claude API calls for identical inputs.

- Estimated savings at 1,000 users: ~$54/month
- Implementation: Redis or simple in-memory LRU cache

### 2. Model Tiering (saves ~70% on classification)

Use Claude Haiku for the classify_node (~10x cheaper than Sonnet) and reserve Sonnet only for
the format_node where response quality matters.

- Classification cost with Haiku: ~$0.0003/request (vs $0.003 with Sonnet)
- Saves: $0.0027 per request × 15,000/month = ~$40/month at Starter tier

### 3. Conversation Compaction (saves ~20%)

Summarize conversation history older than 3 turns instead of sending raw messages.
This reduces input tokens for multi-turn conversations from ~800 to ~200.

- Savings: 600 tokens × $0.000003 × 15,000/month ≈ $27/month at Starter

### 4. Tool Result Truncation (saves ~10%)

Real estate listings and portfolio data can be pre-summarized before LLM formatting.
Reduces average output from 400 to 300 tokens for data-heavy responses.

### Combined Optimization Impact

At 1,000 users/month, implementing all 4 strategies reduces cost from ~$180 to ~$85/month —
a **53% reduction**.

---

## Break-Even Analysis

### SaaS Pricing Model

| Subscription Price | Monthly Cost at 1,000 users | Gross Margin                     |
| ------------------ | --------------------------- | -------------------------------- |
| $9.99/month        | $180 API + $0 infra         | **55%** (with optimization: 91%) |
| $14.99/month       | $180 API + $0 infra         | **70%** (with optimization: 94%) |
| $19.99/month       | $180 API + $0 infra         | **78%** (with optimization: 96%) |

At **$15/month** subscription and 150 queries/month per user:

- Revenue per user: $15.00
- API cost per user: $0.18 (150 × $0.012)
- Gross margin: **98.8%** before infrastructure and support

### When to Pay for Infrastructure

| Milestone       | Infrastructure Needed                | Estimated Monthly Cost |
| --------------- | ------------------------------------ | ---------------------- |
| 0–500 users     | Railway free tier + LangSmith free   | $0                     |
| 500–5,000 users | Railway $5 + LangSmith Developer $39 | $44/month              |
| 5,000+ users    | Railway Pro $20 + LangSmith Plus $99 | $119/month             |

---

## Observability Cost

| Tool                   | Plan                       | Cost         |
| ---------------------- | -------------------------- | ------------ |
| LangSmith              | Free (10,000 traces/month) | $0           |
| Railway                | Free tier                  | $0           |
| **Total at MVP scale** |                            | **$0/month** |

LangSmith free tier covers ~333 traced requests/day — sufficient for beta testing and
submission demo. Production would require the Developer plan at $39/month.

---

## Summary

| Phase                            | Monthly Cost  |
| -------------------------------- | ------------- |
| Development (one-time)           | ~$20 total    |
| MVP (100 users)                  | ~$2 API       |
| Early stage (1,000 users)        | ~$18–$180 API |
| Growth (10,000 users, optimized) | ~$900 API     |
| Infrastructure at scale          | ~$120/month   |

The model is **profitable from day one** at any subscription price above $1/month per user.
