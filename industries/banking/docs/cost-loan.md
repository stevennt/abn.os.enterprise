# Cost sheet: loan.retail.unsecured v1.0 (issue #119) — first numbers, I90 template

Per 1k instances. (M) = measured in stage/pilots, (E) = estimated, remeasured Q2.

| Line | L3 (per 1k) | L4 (per 1k) | Source |
|---|---|---|---|
| infra (engine+bus+DB) | 2.0M (E) | 2.0M (E) | F55/D36 sizing at pilot scale |
| AI inference (s2-extract) | 0.45M (E) | 0.45M (E) | G69 budget 450k/1k |
| human minutes × 500k VND/h | 125.0M (E): 15 min × 1k | 6.25M (E): 5% override × 15 min × 1k | B18 capacity (manager 30m/task blended to 15m avg review) |
| notifications/docs | 0.5M (E) | 0.5M (E) | F56/F57 meters |
| incidents/audit share | 1.0M (E) | 1.0M (E) | I87 pack sizing |
| **total** | **128.95M** | **10.2M** |  |
| human-min saved vs L0 (120 min/inst) | 105,000 min | 119,250 min | L0 baseline time-study |

## L3 vs L4

L4 costs **12.6× less** per 1k (10.2M vs 129M) because s5 manager review drops from
100% to ~5% overrides. AI cost is identical (s2 runs in both); infra flat at this
scale. Break-even of the whole OS build vs L0 manual: ~40k instances at L4 pricing.

## Recompute recipe

1. Pull volumes/TTA/override% from I82 for the quarter.
2. Refresh G69 AI bills + B18 blended rate + infra invoices.
3. Re-run `sim/sim.py` cost line; diff vs sheet; >15% drift opens a cost-review issue.
4. Stamp version + sign (finance manager); archive with the risk pack (I87).
