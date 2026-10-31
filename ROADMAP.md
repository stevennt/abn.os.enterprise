# ROADMAP — 6 phases + best implementation bets

## Phases (maps to issue tracks A–J)

- **P0 Foundation (A):** freeze the 6-primitive metamodel, YAML schemas, validators, 1 worked bank flow. (Issues 1–10)
- **P1 Org & Roles (B):** full bank org-chart, RACI, staffing model, OpenFGA mapping. (11–20)
- **P2 Process discovery (C):** 40-process catalog, BPMN for top 10, input/output schemas per situation. (21–30)
- **P3 Data & Events (D):** event catalog, master-data model, router classifier, idempotency + replay. (31–40)
- **P4 Rules & GRC (E):** DMN rule tables (KYC/AML/SBV), policy-as-code, audit trail. (41–50)
- **P5 Runtime (F):** Temporal/Camunda spike, Frappe human-inbox, Axum gateway, pilot env. (51–60)
- **P6 Intelligence (G):** AI steps with evals (extract/score/draft), fallback discipline. (61–70)
- **P7 Touchpoints (H):** customer/employee/system/external surfaces + SLAs. (71–80)
- **P8 Twin & Assurance (I):** simulator, KPI dashboards, chaos/fraud drills, promotion L3→L4 gates. (81–90)
- **P9 Pilots & Scale (J):** eKYC, retail loan, payments, then roll to all departments. (91–100)

## Bets (opinionated, to save months)

1. **Don't build a workflow engine.** Adopt Temporal or Camunda 8. Building durable execution (retries, versioning, exactly-once) is a 2-year trap.
2. **Don't let LLM be the router.** Router = deterministic classifier (rules + small model) with version pinning. LLM only inside `ai` steps.
3. **Reuse what Anh owns:** Frappe (human tasks), Axum gateway, Supabase Postgres, n8n/ActivePieces for glue — not core.
4. **One worked flow beats 40 diagrams.** Freeze `loan-approval.flow.yaml` end-to-end first; the metamodel earns trust only when it runs.
5. **Evals before autonomy.** No step promotes L3→L4 without eval set + 30-day audit window.
6. **Audit is a feature, not a log.** Every step emits who/what/rule-version/AI-model-version; replay must reproduce the decision.
