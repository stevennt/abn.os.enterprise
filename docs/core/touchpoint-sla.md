# Touchpoint SLA table v1.0 (issue #71) — SLAs are the ops contract

| TP id | Party | Channel | SLA | Fallback | Owner |
|---|---|---|---|---|---|
| TP-C-onboarding | C | mobile app | status <5 min | SMS | retail |
| TP-C-app-status | C | push → Zalo → SMS | <5 min/step | next channel (F56) | owning unit |
| TP-E-inbox | E | Frappe inbox | per-step SLA (flow) | escalate per on_fail (F58) | owning unit |
| TP-S-ekyc-provider | S | API | p99 <8s | manual branch lane | retail |
| TP-S-core | S | API/CDC | p99 <5s (D37) | queue + REVIEW (never guess) | itops |
| TP-S-napas | S | rail | cut-off 16:00 (B15) | next-day value-date | payments |
| TP-S-iam | S | API | p99 <2s | ticket + manual grant | itops |
| TP-S-erp | S | API | p99 <5s | ticket + manual post | finance |
| TP-S-scheme | S | Visa/MC | T-10d guardrail (C27) | manual filing | cards |
| TP-X-appraiser | X | signed docs | 48h | second appraiser | retail.credit |
| TP-X-notary | X | in person | 24h | alternate notary office | retail.credit |
| TP-X-land-office | X | registry | statutory (3–5d) | follow-up docket | retail.credit |
| TP-X-regulator | X | SBV portal | statutory deadline | MLRO attested manual file | compliance |

## Breach escalation refs

- C breach (status late): auto-push via next channel + incident note; 3 breaches/week → unit review.
- E breach (task SLA): escalate per step on_fail (F53 demo); inbox shows breached-first ordering.
- S breach (adapter timeout): breaker per H75; money paths fail-closed to REVIEW.
- X breach (external SLA): docket + owner chase daily; statutory risk escalates to
  MLRO/CRO the same day. Missed statutory deadlines are Sev1 (E50).
