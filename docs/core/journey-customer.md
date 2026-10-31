# Customer mobile journey v1.0 (issue #72) — always visible, VI-first

## Journey map + states (loan example; every flow reuses the shell)

```
APPLIED (receipt + ref id, <1 min)
  -> SCORING (progress, "đang thẩm định", no PII in push text)
  -> DECISION (approve w/ limit + e-sign CTA | decline w/ reason + appeal CTA | review + ETA)
  -> E-SIGN (OTP, TP-C; F57 binding)
  -> DISBURSED (amount + schedule + support CTA)
```

State pushes fire on every transition (TP-C-app-status, <5 min, H71); the app
also polls on open (push is best-effort). Declines show the human-readable reason
from the explainer (I86), never a code. Full VI copy; EN toggle where offered.

## E-sign branch

From DECISION-approved: CTA opens the e-sign sheet (F57: OTP + CCCD binding) →
signed PDF/A receipt stored + linked to instance → DISBURSED. Expiry: link lives
72h; expired links regenerate on request (new OTP, old link dead). Decline path
offers appeal (re-enters triage as a new instance linked to the old one, never
an edit of history).
