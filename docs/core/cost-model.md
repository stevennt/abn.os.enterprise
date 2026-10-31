# Cost-of-operation model v1.0 (issue #90) — per 1k instances, L3 vs L4

## Cost sheet template (fill per flow, quarterly refresh with vendor pricing)

| Line | L3 (per 1k) | L4 (per 1k) | Source |
|---|---|---|---|
| infra (engine+bus+DB amortized) | _ | _ | F55/D36 sizing |
| AI inference (sum of step budgets) | _ | _ | G69 table |
| human minutes × blended rate | _ (high) | _ (override only) | B18 capacity |
| notifications/docs | _ | _ | F56/F57 meters |
| incidents/audit overhead share | _ | _ | I87 pack |
| **total** | _ | _ |  |
| human-minutes saved vs L0 | _ | _ | baseline time-study |

## Reading rules

- L4 must beat L3 on total AND on human-minutes; cheaper-but-equal-touch is not a win.
- AI cost growth faster than volume growth triggers G69 kill-switch review.
- Numbers feed the promotion pack (I83) and the J100 scorecard;estimates allowed in
  v1, measured-only from the second quarter (pilots produce real meters, J95).
