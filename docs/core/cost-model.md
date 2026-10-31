# Cost-of-operation model v1.0 (issue #90) — per 1k instances, L3 vs L4

## Where numbers live

This file is the **template and the method**. Filled sheets are per industry, next to
the content they describe:

- `industries/banking/docs/cost-loan.md` — first real numbers for the retail loan flow
- a new industry copies that file's shape; nothing shared needs to change

Industries differ in ways one sheet cannot capture: a bank's cost is dominated by
human approval minutes, a legal practice's by reviewer time and licensed sources.

## Cost sheet template (fill per flow per industry, quarterly, vendor pricing refreshed)

| Industry | Line | L3 (per 1k) | L4 (per 1k) | Source |
|---|---|---|---|
| `<id>` | infra (engine+bus+DB amortized) | _ | _ | F55/D36 sizing |
| `<id>` | AI inference (sum of step budgets) | _ | _ | G69 table |
| `<id>` | human minutes × blended rate | _ (high) | _ (override only) | B18 capacity |
| `<id>` | notifications/docs | _ | _ | F56/F57 meters |
| `<id>` | incidents/audit overhead share | _ | _ | I87 pack |
| `<id>` | **total** | _ | _ |  |
| human-minutes saved vs L0 | _ | _ | baseline time-study |

## Reading rules

- L4 must beat L3 on total AND on human-minutes; cheaper-but-equal-touch is not a win.
- AI cost growth faster than volume growth triggers G69 kill-switch review.
- Numbers feed the promotion pack (I83) and the J100 scorecard;estimates allowed in
  v1, measured-only from the second quarter (pilots produce real meters, J95).
