# Error taxonomy + retry/escalation v1.0 (issue #58) — no retry-storms on core

## Taxonomy table

| Class | Meaning | Retry? | Escalation | Example |
|---|---|---|---|---|
| TRANSIENT | downstream timeout/5xx, lock wait | yes — exp backoff, max 5, jitter | page on 5th failure | core timeout, SMS gateway 503 |
| BUSINESS | rule says no (limit, DSTI, deadline) | no — decide REVIEW/DECLINE | none (normal path) | DSTI 0.68, expired scheme deadline |
| FRAUD | crime signal | no — hold + case | page compliance immediately | sanction hit, mule pattern |
| FATAL | bug/contract break/schema invalid | no — DLQ + incident | page platform + owning team | missing required field, engine bug |

Retry budget is per instance (not per step): 5 transient retries total, then the
instance diverts to its step's `on_fail` lane. Circuit-breakers per adapter (H75):
3 consecutive transient failures halve the rate; 10 open the breaker for 5 min.

## Per-step on_fail audit

Every flow step MUST carry `on_fail` (validator enforces across all flows):
allowed forms are `REVIEW`, `retry+page`, `hold:<queue>`, `escalate:<role>`,
`return-cached-response`, `page:<who>`, `DECLINE-with-reasons`. Free-text on_fail
is rejected in review — the lane must exist (queue, role, or DLQ reason).
