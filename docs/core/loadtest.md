# Load test plan v1.0 (issue #60) — 1000 loan apps/hour holds payday spikes

## k6 plan (`engine/load/loan-spike.js`, track F implements)

Stages against stage env (F59): ramp 0→20 rps over 5m, hold 1000 apps/hour (17 rps)
for 30m, spike to 2× for 5m, ramp down. Mix: 80% clean approve-path, 15% REVIEW,
5% duplicates (idempotency check under load, A07). Synthetic data only (D40 seed).

## SLO table

| Metric | Target | Page at |
|---|---|---|
| TTA p50 (submit→decision) | ≤ 2 min | > 5 min for 10 min |
| TTA p95 | ≤ 15 min | > 30 min for 10 min |
| error rate (5xx/poison) | < 0.1% | ≥ 0.5% for 5 min |
| double-post rate | 0 | any occurrence (Sev1) |
| consumer lag p99 | < 5s | > 30s for 5 min |
| engine worker CPU | < 70% sustained | > 85% for 10 min |

## Bottleneck list (expected, verify in run)

1. AI extract step (s2) latency under burst → batch + cache by doc hash.
2. Core posting throughput at spike → throttle + queue, never fail open.
3. Audit write amplification → async batch writer, verify job stays <60s behind.
4. Notification fan-out bursts → per-channel rate limits (F56).

Pass = all SLOs green + zero double-posts + bottleneck actions filed as issues.
Runs monthly and before every L4 promotion touching the loan flow (A10).
