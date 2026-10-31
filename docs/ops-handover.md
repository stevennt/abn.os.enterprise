# Ops handover v1.0 (issue #98) — autonomy still needs owners

## Runbook index (one page per Sev, linked from the on-call console)

| Runbook | Trigger | First 3 actions |
|---|---|---|
| RB-Sev1-money | double-post / ledger break | freeze auto-posting → micro-recon → incident channel |
| RB-Sev1-data | PII in logs/twin | revoke grants → seal + rotate → MLRO notify |
| RB-degrade | lag/breaker storm | confirm fail-closed → shed non-money load → page platform |
| RB-dlq-spike | NO_ROUTE surge | pause producer → add routing row (E46 fast path) |
| RB-restore | any DR event | pick layer runbook (I89) → money drill before traffic |
| RB-rollback | pilot/wave breach | one-PR default flip → shadow mode → incident |

## On-call rotation draft

- Follow-the-sun across 3 squads (platform, risk-tech, ops-duty); primary + secondary,
  1-week rotations, max 2 primaries/quarter per person.
- Page policy: Sev1 pages primary+secondary immediately; Sev2 pages primary, secondary
  in 15 min if unacked. Alert fatigue review monthly (tune, don't mute).
- Handover notes mandatory (open incidents, degrades, deploys in flight); missed
  handover = Sev3 process incident. Compensation: on-call stipend + day-off after
  night Sev1.
