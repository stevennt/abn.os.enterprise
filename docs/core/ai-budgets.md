# AI cost/latency budgets v1.0 (issue #69) — autonomy must stay profitable

## Budget table (per 1k instances; review quarterly with vendor pricing)

| Step (contract) | Max VND/1k | p99 latency/instance | Notes |
|---|---|---|---|
| s2-extract | 450,000 | 8s | two-pass OCR+LLM; cache by doc hash |
| s3-income-verify | 120,000 | 3s | scoring only, no generation |
| s5-memo-draft | 300,000 | 12s | longest output; citations add tokens |
| s1-triage | 80,000 | 3s | short in/out |
| copilot-qa | 150,000 | 5s | RAG retrieval dominates, not tokens |

Fill `cost_budget_per_1k` in each contract from this table (G61 template).
Assumes self-hosted inference at current GPU amortization; SaaS fallback priced
separately in J99 — whichever is live, the table's VND caps still bind.

## Alert thresholds + kill-switch

- Warn: 80% of budget for 3 consecutive days → owner investigates (cache hit rate?
  prompt bloat? retry storm?).
- Kill-switch: 150% of budget, or p99 2× cap for 1 day → step auto-falls to a
  cheaper lane (cached-only / smaller model / human REVIEW) until the owner signs
  back. Overrun spend without kill-switch action is a Sev2.
