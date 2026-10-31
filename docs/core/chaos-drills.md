# Chaos drills v1.0 (issue #85) — degrade, never corrupt

Stage only (F59), business-hours with comms, abort switch owned by drill lead.

## Drill calendar (quarterly rotation + monthly mini)

| Drill | Kills | Expected behavior |
|---|---|---|
| engine-worker-loss | 50% workers mid-flow | journal resume, zero double-effects (F52) |
| kafka-lag | inject 60s lag | TTA degrades, money fail-closed to REVIEW |
| cic-down | bureau adapter 503 | no auto-pass, REVIEW queue (H75) |
| core-slow | 10× latency | breakers trip, backpressure, no retry-storm (F58) |
| az-loss | full AZ | traffic shifts, RPO≈0 via journal+outbox |
| clock-skew | +5 min partitions | idempotency keys hold, no double-post (A07) |

## Pass criteria

- Zero data corruption (ledger balances reconcile to the cent post-drill).
- Zero silent auto-approvals during degradation (every degraded decision cites REVIEW).
- Recovery ≤ RTO in the DR table (I89); drill report filed within 5 business days
  with action items as issues. Two consecutive drill failures freeze promotions (A10).
