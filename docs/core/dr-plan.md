# DR plan v1.0 (issue #89) — the OS is critical infra now

## RPO/RTO table

| Layer | RPO | RTO | How |
|---|---|---|---|
| event bus (topics) | 0 (3 replicas, minISR 2) | <15 min (rebalance) | D36 design; replay fills gaps |
| engine journal | 0 (write-ahead per step, F52) | <30 min (resume from journal) | kill-tested in CI |
| OS Postgres | <5 min (WAL streaming) | <1h (promote standby, replay) | F55 schema; standby in 2nd AZ |
| audit vault | 0 (sealed append-only, dual-write) | <1h | A05 chain verifies post-restore |
| sealed payload store | <5 min | <2h | HSM keys backed up offline (F59) |
| gateway/inbox | stateless — 0 | <15 min (redeploy) | F54/F53; config in git |

Money rule: after any restore, the A07 money drill re-runs BEFORE traffic resumes —
a restored system that double-posts is worse than a slow one.

## Restore drill plan

- Quarterly game-day: pick one layer, restore to an isolated env, verify (audit
  chain OK, ledger reconciles, RPO/RTO met), file report in 5 days.
- Annual full-failover rehearsal with business observers (branch + CS present).
- Drill failures are Sev1 with action issues; two consecutive failures freeze
  promotions (same bar as chaos drills, I85).
