# System adapters v1.0 (issue #75) — external latency must not kill instances

## Adapter contract (every S touchpoint driver implements this)

- `call(op, payload, idempotency_key) -> (ok, result | error_class)` with
  error_class in {TRANSIENT, BUSINESS, FRAUD, FATAL} (F58) — no raw exceptions
  cross the boundary, ever.
- Timeouts per op (connect + read), retries inside the adapter only for TRANSIENT
  (max 3, backoff + jitter), then return TRANSIENT to the engine for step-level policy.
- Cut-off awareness: adapter knows rail windows (B15); after cut-off it returns
  BUSINESS/`AFTER_CUTOFF` (value-date next day) instead of timing out.
- Health endpoint + lag/latency metrics per adapter for the I82 panel.

## Breaker thresholds (per adapter, tuned quarterly)

| Adapter | Trip: consecutive TRANSIENT | Half-open probe | Open duration | Fail mode |
|---|---|---|---|---|
| core | 5 | 1 probe/30s | 5 min | fail-closed to REVIEW (money) |
| CIC bureau | 5 | 1 probe/60s | 10 min | REVIEW (never skip the check) |
| NAPAS | 3 | 1 probe/15s | 3 min | queue + retry (payments) |
| SWIFT | 3 | 1 probe/30s | 5 min | queue + retry, value-date guard |
| eKYC provider | 5 | 1 probe/30s | 5 min | branch manual lane |
| SMS/push | 10 | continuous | n/a (degraded) | next channel (F56) |

Breaker state changes are audit-logged; money paths always fail closed to REVIEW,
never open (a guess that moves money is a Sev1 by definition).
