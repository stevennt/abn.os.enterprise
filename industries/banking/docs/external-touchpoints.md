# External touchpoints v1.0 (issue #76) — the regulatory surface, made explicit

## Filing calendar (recurring; ad-hoc STR/complaint filings ride C25/C28)

| Filing | To | Cadence | Owner | Due |
|---|---|---|---|---|
| prudential ratios report | SBV | monthly | finance | WD10 |
| credit data (CIC) | CIC | daily | risk | T+1 08:00 |
| STR | SBV-AMLD | event-driven | MLRO | statutory (C25 SLA) |
| complaint aggregate | SBV | quarterly | cs_manager | quarter+15d |
| audit confirmations | external auditor | annual + ad-hoc | finance | per engagement letter |
| bancassurance bordereaux | insurer partners | monthly | corporate | 5th |

Missed statutory filings are Sev1 (E50); the calendar lives in the ops runbook (J98)
with a named backup owner per row.

## Payload signing spec

- Every outbound filing is canonical-JSON + detached Ed25519 signature
  (`kid` = key id, `sig` over sha256 of canonical bytes); SBV portal uploads attach
  the `.sig` sidecar, API filings carry `X-Filing-Signature`.
- Keys in HSM/vault (F59 prod path), rotation 12 months with 30-day overlap;
  receivers verify against the published key directory before processing.
- Inbound (CIC responses, auditor requests): verify signature, check replay window
  (5 min) + idempotency key (A07) before touching any flow.
