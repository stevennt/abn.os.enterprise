# Build-vs-buy final review v1.0 (issue #99) — no surprise invoices at scale

Priced with pilot-measured numbers where available (J91–J95 meters), estimates
marked (est) elsewhere. Horizon: 3 years, prod scale (~50M events/day).

## Costed options (3y TCO bands)

| Option | Engine | Infra/yr | Licenses/yr | People | 3y band |
|---|---|---|---|---|---|
| A. Camunda self-managed | Zeebe on K8s | mid (3 brokers + workers) | 0 + support (opt) | 2 platform eng | lowest cash, highest ops load |
| B. Camunda SaaS | hosted | low | per-task pricing (volume-sensitive!) | 1 platform eng | predictable until volume 3×, then steep |
| C. Temporal Cloud/self | Temporal | mid | 0 self / actions-based cloud | 2 platform eng | close to A, weaker BPMN story |
| D. Build own engine | custom | low-mid | 0 | 4+ eng × 2y sunk | rejected (2-year trap, ARCHITECTURE.md) |

AI inference: self-hosted GPU amortization vs SaaS per-1k (G69 meters decide per
step, not per program — no single answer). Event bus: Redpanda self-managed
(band: commodity) vs Confluent Cloud (band: ~3× at our volume).

## Recommendation

- Engine: **A, with B as overflow** (SaaS for DR region only) — revisit when task
  volume crosses the contracted SaaS breakpoint (alert owned by finance, not eng).
- Bus + inference: self-managed first, SaaS only where meters prove cheaper (J99
  re-runs yearly). Procurement sign-off: CFO + CRO on this file + J100 scorecard.
