# Fallback & abstain discipline v1.0 (issue #68) — silent auto-approve is forbidden

## Reason-code list (every REVIEW-from-AI carries exactly one)

| Code | Trigger | Lane |
|---|---|---|
| `LOW_CONF` | confidence below contract `abstain_below` | human review, same queue |
| `SCHEMA_FAIL` | output fails output_schema | human review + eval-team ticket |
| `MODEL_UNPINNED` | version drift or eval not green | freeze step, page platform |
| `PII_RISK` | input above contract PII tier | human review, masked view |
| `TIMEOUT` | p99 budget exceeded (G69) | retry once, then REVIEW |
| `CONTRADICT` | sources disagree (memo/complaint) | human review with both sources shown |
| `OOC` | out-of-corpus (copilot) | human review + owning-unit pointer |

Reason codes are audit-logged (A05) and aggregated — a step whose REVIEW rate
crosses its contract budget auto-demotes per A10, no meeting needed.

## Dashboard requirement (I82 panel)

Per AI step, trailing 7d/30d: volume, REVIEW rate by reason code, abstain rate,
p50/p99 latency, cost per 1k (G69), eval-suite status at pinned version.
Alert: REVIEW rate >2× baseline for 3 days, or any single `MODEL_UNPINNED`.
