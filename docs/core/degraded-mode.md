# Degraded-mode journeys v1.0 (issue #80) — resilience is a journey, not just infra

## Degraded-mode table

| Failure | Customer journey | Branch journey | Money rule |
|---|---|---|---|
| power/net loss at branch | app works (unaffected) | paper capture → offline queue → sync (H73) | no cash ops without power |
| CIC bureau down | apply accepted, "pending verification" | same + manual checklist | no disbursal until check passes (H75) |
| SMS down | push/Zalo first (F56) | tablet + print | OTP via app TOTP fallback |
| eKYC provider down | "try later" + branch invite | manual KYC lane (B11) | no auto-pass, ever |
| core slow (lag) | status shows queued | queue + receipt | fail-closed to REVIEW |
| engine down | read-only status | paper + later entry | zero new postings |

## Manual-fallback forms

Paper twins of the 5 highest-volume captures (onboarding, loan app, transfer,
complaint, dispute): pre-printed with field codes matching event schemas so
later entry is transcription, not reinterpretation. Forms reconciled daily
(paper ref ↔ instance id); unreconciled forms page the branch manager. Drilled
quarterly per branch (J95 training covers the drill).
