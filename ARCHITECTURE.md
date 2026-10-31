# ARCHITECTURE — runtime options + recommendation

## The routing core (one sentence)

Every business situation is an **Event with a typed Data payload**; a **Router** classifies it and starts the matching **Process version**; each step executes as **workflow / AI / human** under **Rules** and **Roles**; every step emits an **Audit event**.

```mermaid
flowchart LR
  IN[Event + Data] --> R[Router: classify + version]
  R --> P[Process engine: durable execution]
  P -->|deterministic| W[Workflow step]
  P -->|judgement| A[AI agent step]
  P -->|approval/touch| H[Human task]
  W & A & H --> RL[(Rules + Roles)]
  W & A & H --> T[Touchpoint C/E/S/X]
  T --> OUT[Output + KPI]
  OUT --> AUD[Audit log + replay]
```

## Option comparison (read before building)

| Option | Core | Strength | Weakness | Best for |
|--------|------|----------|----------|----------|
| **A. Temporal + Kafka** | code-first durable execution | strongest failure handling, versioning, testability | business users can't read code | bank core: payments, loans, ledger |
| **B. Camunda 8 / Zeebe** | BPMN 2.0 + DMN native | analysts draw, engine runs, DMN for rules | ops cost, less dev-ergonomic than Temporal | compliance-heavy, analyst-owned flows |
| **C. Frappe Workflow + n8n/ActivePieces** | low-code, you already own it | fastest pilot (days), human-task UI free | not durable at bank scale, versioning weak | pilot touchpoints + internal ops |
| **D. Pure AI-agent swarm** | LLM orchestrates everything | flexible for unstructured cases | non-deterministic, unauditable, expensive | REJECT as core; use only at AI steps |

## Recommended hybrid (what the 100 issues implement)

- **Durable core:** Temporal (or Camunda 8 if analysts must own BPMN). One binary per domain, Postgres + Redpanda/Kafka, idempotency keys everywhere.
- **Rules:** DMN tables / OPA + OpenFGA for roles. No rule inside code — rule IDs referenced from process YAML.
- **AI sidecar:** LLM agents ONLY at marked `ai` steps (classify, extract, score, draft) with JSON-schema outputs, evals, and human fallback. Never the router.
- **Human layer:** Frappe / custom inbox for approvals + customer/employee portals. Every task has SLA + escalation.
- **Gateway:** Axum (you own it) fronts everything; Supabase Postgres is system-of-record; PostgREST/Kong patterns you already run stay.
- **Observability + twin:** OpenTelemetry traces per process-instance; event log replayable into a simulator for "what-if" (staffing, SLA, fraud).

## Workflow vs AI vs Human — decision matrix

| Signal | → Workflow | → AI | → Human |
|--------|-----------|------|---------|
| Inputs structured, rule exists | ✅ | | |
| Needs reading/extracting/scoring unstructured | | ✅ (+ schema + eval) | |
| Legal/financial sign-off, complaint, exception over threshold | | | ✅ (with AI draft) |
| Cost of error high + precedent low | | AI proposes | ✅ decides |
| Everything else, first version | | | ✅ then promote L3→L4 with data |

Rule of thumb: **start L3 (auto + human approve), promote to L4 (auto + override) only with 30+ days of clean audit + evals green.**
See `engine/automation-levels.md`.
