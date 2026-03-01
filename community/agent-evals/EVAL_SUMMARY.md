# Ghostfolio AI Agent — Eval Test Dataset

A community-contributed evaluation dataset for
testing AI agents built on top of the Ghostfolio API.

## Overview

183 test cases covering the full Ghostfolio API
surface, contributed by the Gauntlet AI bounty
submission (March 2026).

## Categories

| Category | Count | Description |
|----------|-------|-------------|
| Happy Path | 20 | Standard queries that should always work |
| Edge Cases | 14 | Boundary conditions, empty data, typos |
| Adversarial | 14 | Prompt injection, nonsense, abuse attempts |
| Multi-Step | 13 | Conversations spanning multiple tool calls |
| Domain Specific | 122 | Portfolio, market, property, tax, relocation |

## Query Types Covered

- Portfolio analysis (holdings, allocation, performance)
- Market data (live stock prices, YTD returns)
- Tax estimation (capital gains, tax-loss harvesting)
- Risk & compliance (concentration, diversification)
- Transaction history (trade history, recent activity)
- Real estate (property CRUD, equity analysis)
- Life decisions (job offers, relocation, retirement)
- Wealth gap analysis (Fed SCF benchmarking)

## How to Use

These test cases can be used to evaluate any
AI agent built on top of the Ghostfolio API.
Each test case includes:
- Input query (natural language)
- Expected tool called
- Expected response characteristics
- Verification criteria

## Full Dataset

The full test dataset with code is available at:
https://github.com/lakshmipunukollu-ai/ghostfolio-agent-priya
in the `agent/evals/` directory.

## Routing Test Cases

| Query | Expected Tool |
|-------|--------------|
| how is my portfolio | portfolio_analysis |
| check apple for me | market_data |
| how many shares of APPL do I have | portfolio_analysis |
| can I afford to retire | wealth_gap |
| tell me about my house | property_tracker |
| what can this do | capabilities |
| give me a full portfolio summary | portfolio_analysis |
| is 180k in seattle a raise from 120k in austin | relocation_runway |
| estimate my capital gains | tax_estimate |
| am I over concentrated | compliance_check |
| what is the price of NVDA | market_data |
| show me my transactions | transaction_query |
| how much is AAPL | market_data |
| can I afford a house | wealth_down_payment |

## Contributing

If you build an AI agent on Ghostfolio and want
to contribute additional test cases, please open
a PR adding them to this directory.
