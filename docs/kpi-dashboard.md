# KPI dashboard spec v1.0 (issue #82) — what management watches daily

Slices on every view: per-process, per-version, per-branch, trailing 7d/30d.

## Metric definitions (single formulas, used everywhere incl. A10/I83)

| Metric | Definition |
|---|---|
| TTA p50/p95 | submit/trigger → terminal decision, by process version |
| approval_rate | APPROVE / decided (excl. in-flight) |
| default_30d | facilities 30+ days past due / disbursed in window |
| override_rate | human-overturned auto steps / auto steps |
| review_rate | REVIEW outcomes / started |
| breach_rate | SLA breaches / steps due |
| abstain_rate | AI abstains / AI steps (by G68 code) |
| cost_per_1k | infra + AI + human-minutes per 1000 instances (G69/I90) |
| touchless_rate | instances with zero human touches / started (the J100 headline) |

## Wireframe (ops overview → process drill-down → instance)

1. Overview row: touchless %, TTA p95 sparkline, breach count, Sev/open incidents.
2. Process table: one row per (process, version) with the 9 metrics + trend arrows;
   L3/L4 badge per step; click sorts/filters.
3. Instance drawer: step timeline, actor/rule/model versions, audit verify badge (E49),
   touchpoint pushes sent, linked DLQ/replay items if any.
4. AI panel (G68): REVIEW rate by reason code, latency, cost, eval status per step.
5. Journey panel (H79): funnels, drop-off, CSAT scatter.
