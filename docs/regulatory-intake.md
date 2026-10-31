# Regulatory-change intake v1.0 (issue #50) — law changes absorbed in days

## Intake flow

```
SBV circular / law amendment published
  -> s1-log (compliance, 1d): register source, effective date, grace period
  -> s2-impact (risk + legal + affected units, 3d): map to rule packs/flows/touchpoints
  -> s3-diff (pack owner, 5d): rule PR with before/after + customer impact note
  -> s4-deploy (E46 pipeline): review, release, dual-run, audit link
  -> s5-attest (compliance, by effective date): attestation pack to regulator/board
```

SLA: standard changes live 10 business days after intake; urgent (safety/sanctions)
72h via the emergency path (E46). Missed effective dates are Sev1.

## RACI

| Step | R | A | C | I |
|---|---|---|---|---|
| s1-log | compliance analyst | MLRO | — | all units |
| s2-impact | risk + legal | CRO | affected unit heads | board-risk-committee |
| s3-diff | pack owner | risk manager | legal, affected units | — |
| s4-deploy | platform | pack owner | — | all units |
| s5-attest | compliance | MLRO | external counsel if needed | regulator, board |
