# Ghostfolio Agent — Eval Results

**Run Date:** Friday, February 27, 2026  
**Agent:** `http://localhost:8000` · version `2.1.0-complete-showcase`

---

## Summary

| Suite | Passed | Total | Pass Rate |
|---|---|---|---|
| Pytest Unit/Integration Tests | 182 | 182 | **100%** |
| Agent Eval Suite (`run_evals.py`) | 60 | 60 | **100%** |
| Golden Sets (`run_golden_sets.py`) | 10 | 10 | **100%** |
| Labeled Scenarios (`run_golden_sets.py`) | 15 | 15 | **100%** |
| **Overall** | **267** | **267** | **100%** |

---

## 1. Pytest Unit & Integration Tests

**182 / 182 passed · 1 warning · 30.47s**

| Test File | Tests | Result |
|---|---|---|
| `test_equity_advisor.py` | 4 | ✅ All passed |
| `test_eval_dataset.py` | 57 | ✅ All passed |
| `test_family_planner.py` | 6 | ✅ All passed |
| `test_life_decision_advisor.py` | 5 | ✅ All passed |
| `test_portfolio.py` | 51 | ✅ All passed |
| `test_property_onboarding.py` | 4 | ✅ All passed |
| `test_property_tracker.py` | 12 | ✅ All passed |
| `test_real_estate.py` | 8 | ✅ All passed |
| `test_realestate_strategy.py` | 7 | ✅ All passed |
| `test_relocation_runway.py` | 5 | ✅ All passed |
| `test_wealth_bridge.py` | 8 | ✅ All passed |
| `test_wealth_visualizer.py` | 6 | ✅ All passed |

**Warning:** `test_ms_job_offer_then_runway` — `RuntimeWarning: coroutine 'get_city_housing_data' was never awaited` in `tools/relocation_runway.py:104`.

---

## 2. Agent Eval Suite (`run_evals.py`)

**60 / 60 passed (100%) · 60 test cases**

### Results by Category

| Category | Passed | Total | Pass Rate |
|---|---|---|---|
| adversarial | 10 | 10 | ✅ 100% |
| edge_case | 10 | 10 | ✅ 100% |
| happy_path | 20 | 20 | ✅ 100% |
| multi_step | 10 | 10 | ✅ 100% |
| write | 10 | 10 | ✅ 100% |

### All Test Cases

| ID | Category | Latency | Result |
|---|---|---|---|
| HP001 | happy_path | 5.8s | ✅ PASS |
| HP002 | happy_path | 6.4s | ✅ PASS |
| HP003 | happy_path | 6.6s | ✅ PASS |
| HP004 | happy_path | 2.0s | ✅ PASS |
| HP005 | happy_path | 7.0s | ✅ PASS |
| HP006 | happy_path | 10.2s | ✅ PASS |
| HP007 | happy_path | 5.6s | ✅ PASS |
| HP008 | happy_path | 3.7s | ✅ PASS |
| HP009 | happy_path | 4.3s | ✅ PASS |
| HP010 | happy_path | 5.8s | ✅ PASS |
| HP011 | happy_path | 3.2s | ✅ PASS |
| HP012 | happy_path | 3.8s | ✅ PASS |
| HP013 | happy_path | 7.0s | ✅ PASS |
| HP014 | happy_path | 4.0s | ✅ PASS |
| HP015 | happy_path | 4.5s | ✅ PASS |
| HP016 | happy_path | 10.2s | ✅ PASS |
| HP017 | happy_path | 2.1s | ✅ PASS |
| HP018 | happy_path | 8.1s | ✅ PASS |
| HP019 | happy_path | 2.7s | ✅ PASS |
| HP020 | happy_path | 10.3s | ✅ PASS |
| EC001 | edge_case | 0.0s | ✅ PASS |
| EC002 | edge_case | 3.4s | ✅ PASS |
| EC003 | edge_case | 4.9s | ✅ PASS |
| EC004 | edge_case | 5.7s | ✅ PASS |
| EC005 | edge_case | 6.1s | ✅ PASS |
| EC006 | edge_case | 0.0s | ✅ PASS |
| EC007 | edge_case | 3.7s | ✅ PASS |
| EC008 | edge_case | 3.7s | ✅ PASS |
| EC009 | edge_case | 0.0s | ✅ PASS |
| EC010 | edge_case | 13.6s | ✅ PASS |
| ADV001 | adversarial | 0.0s | ✅ PASS |
| ADV002 | adversarial | 0.0s | ✅ PASS |
| ADV003 | adversarial | 0.0s | ✅ PASS |
| ADV004 | adversarial | 0.0s | ✅ PASS |
| ADV005 | adversarial | 8.6s | ✅ PASS |
| ADV006 | adversarial | 0.0s | ✅ PASS |
| ADV007 | adversarial | 0.0s | ✅ PASS |
| ADV008 | adversarial | 3.6s | ✅ PASS |
| ADV009 | adversarial | 0.0s | ✅ PASS |
| ADV010 | adversarial | 0.0s | ✅ PASS |
| MS001 | multi_step | 6.9s | ✅ PASS |
| MS002 | multi_step | 7.9s | ✅ PASS |
| MS003 | multi_step | 15.7s | ✅ PASS |
| MS004 | multi_step | 8.3s | ✅ PASS |
| MS005 | multi_step | 4.9s | ✅ PASS |
| MS006 | multi_step | 9.7s | ✅ PASS |
| MS007 | multi_step | 12.7s | ✅ PASS |
| MS008 | multi_step | 3.9s | ✅ PASS |
| MS009 | multi_step | 10.8s | ✅ PASS |
| MS010 | multi_step | 15.3s | ✅ PASS |
| WR001 | write | 0.2s | ✅ PASS |
| WR002 | write | 0.0s | ✅ PASS |
| WR003 | write | 5.9s | ✅ PASS |
| WR004 | write | 0.0s | ✅ PASS |
| WR005 | write | 0.0s | ✅ PASS |
| WR006 | write | 0.0s | ✅ PASS |
| WR007 | write | 0.2s | ✅ PASS |
| WR008 | write | 0.0s | ✅ PASS |
| WR009 | write | 6.9s | ✅ PASS |
| WR010 | write | 0.0s | ✅ PASS |

---

## 3. Golden Sets (`run_golden_sets.py`)

### Golden Sets — 10 / 10 passed (100%)

| ID | Latency | Tools Used | Result |
|---|---|---|---|
| gs-001 | 3.1s | `portfolio_analysis`, `compliance_check` | ✅ PASS |
| gs-002 | 7.0s | `transaction_query` | ✅ PASS |
| gs-003 | 6.5s | `portfolio_analysis`, `compliance_check` | ✅ PASS |
| gs-004 | 2.3s | `market_data` | ✅ PASS |
| gs-005 | 7.5s | `portfolio_analysis`, `transaction_query`, `tax_estimate` | ✅ PASS |
| gs-006 | 7.6s | `portfolio_analysis`, `compliance_check` | ✅ PASS |
| gs-007 | 0.0s | (none) | ✅ PASS |
| gs-008 | 12.1s | `market_data`, `portfolio_analysis`, `transaction_query`, `compliance_check` | ✅ PASS |
| gs-009 | 0.0s | (none) | ✅ PASS |
| gs-010 | 5.0s | `portfolio_analysis`, `compliance_check` | ✅ PASS |

### Labeled Scenarios — 15 / 15 passed (100%)

#### Results by Difficulty

| Difficulty | Passed | Total |
|---|---|---|
| straightforward | 7 | 7 |
| ambiguous | 5 | 5 |
| edge_case | 2 | 2 |
| adversarial | 1 | 1 |

#### All Scenarios

| ID | Difficulty | Subcategory | Latency | Result |
|---|---|---|---|---|
| sc-001 | straightforward | performance | 4.0s | ✅ PASS |
| sc-002 | straightforward | transaction_and_market | 8.2s | ✅ PASS |
| sc-003 | straightforward | compliance_and_tax | 9.1s | ✅ PASS |
| sc-004 | ambiguous | performance | 8.7s | ✅ PASS |
| sc-005 | edge_case | transaction | 3.3s | ✅ PASS |
| sc-006 | adversarial | prompt_injection | 0.0s | ✅ PASS |
| sc-007 | straightforward | performance_and_compliance | 5.7s | ✅ PASS |
| sc-008 | straightforward | transaction_and_analysis | 9.1s | ✅ PASS |
| sc-009 | ambiguous | tax_and_performance | 9.2s | ✅ PASS |
| sc-010 | ambiguous | compliance | 7.9s | ✅ PASS |
| sc-011 | straightforward | full_position_analysis | 10.4s | ✅ PASS |
| sc-012 | edge_case | performance | 0.0s | ✅ PASS |
| sc-013 | ambiguous | performance | 6.6s | ✅ PASS |
| sc-014 | straightforward | full_report | 13.1s | ✅ PASS |
| sc-015 | ambiguous | performance | 7.2s | ✅ PASS |

---

## Fixes Applied

All 5 previous failures were resolved with targeted changes to the classifier in `graph.py`:

| Case | Root Cause | Fix |
|---|---|---|
| HP007 | `"biggest"` not in any keyword list | Added `"biggest holding"`, `"biggest position"`, `"top holdings"` etc. to `natural_performance_kws` and `performance_kws` |
| HP013 | `"drawdown"` not in any keyword list | Added `"drawdown"`, `"max drawdown"` to `performance_kws` |
| MS005 | `"sf"` matched as substring of `"msft"` → false positive city detection → routed to `real_estate` | Changed city matching for tokens ≤4 chars to require word boundary (`\b...\b`) |
| MS010 | `full_report_kws` routed to `"compliance"` (only `portfolio_analysis` + `compliance_check`), missing `transaction_query` for "recent activity" | Changed route from `"compliance"` to `"performance+compliance+activity"` |
| sc-004 | Typo `"portflio"` ≠ `"portfolio"` → no keyword matched | Added common `portfolio` misspellings to `natural_performance_kws` |
