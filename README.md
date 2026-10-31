# abn.os.enterprise — Autonomous Enterprise OS

> **Problem:** model 100% of a business's operations (e.g. a bank: departments, org-charts, staff, processes, regulations) so that every situation — with defined inputs/data — routes through the right process flow and runs automatically. Workflow where possible, AI where judgement is needed, humans only at explicit touchpoints.
>
> **Goal:** near-100% autonomous operation with full auditability.

## 6 primitives (everything in this repo hangs off these)

| # | Primitive | File | Question it answers |
|---|-----------|------|---------------------|
| 1 | `OrgUnit` + `Role` | `metamodel/org.schema.yaml` | Who exists? Who may do/approve what? |
| 2 | `Process` | `metamodel/process.schema.yaml` | What is the flow? Inputs → steps → outputs? |
| 3 | `Rule` | `metamodel/rule.schema.yaml` | What policy/regulation constrains the flow? |
| 4 | `Event` + `Data` | `metamodel/event.schema.yaml` | What triggers/inputs arrive? What leaves? |
| 5 | `Touchpoint` | `metamodel/touchpoint.schema.yaml` | Where does a Customer / Employee / System / External party meet the flow? |
| 6 | `AutomationLevel` L0–L5 | `engine/automation-levels.md` | Can this step run as workflow, AI, or needs human? |

```
Event(Data) → Router → Process(Step[workflow|ai|human] + Rule + Role) → Touchpoint → Output + Audit
```

## Repo map

```
README.md                  — this file
ARCHITECTURE.md            — runtime options + recommended hybrid stack
ROADMAP.md                 — 6 phases + build-vs-buy decisions
metamodel/                 — YAML schemas (the "language" of the OS)
examples/bank/             — reference bank: org-chart, 40-process catalog, 1 fully-worked flow
engine/                    — automation levels, workflow-vs-AI decision matrix
docs/                      — vision, glossary, touchpoint taxonomy, simulation plan
scripts/seed-issues.py     — the 100 GitHub issues (source of truth, re-runnable)
```

## How to model any department (repeatable recipe)

1. **Org:** list units → roles → headcount → RACI per process (`examples/bank/org-chart.yaml`).
2. **Inputs:** for each situation, write the input JSON schema + trigger event (`metamodel/event.schema.yaml`).
3. **Flow:** draw steps as `workflow` (deterministic) / `ai` (judgement) / `human` (approval/touch). Mark the level L0–L5.
4. **Rules:** attach policy IDs (SBV/fraud/AML/KYC…) as DMN-style tables (`metamodel/rule.schema.yaml`).
5. **Touchpoints:** mark every C/E/S/X contact with channel + SLA (`metamodel/touchpoint.schema.yaml`).
6. **Close the loop:** outputs → KPI → audit event → simulation replay.

Worked example: `examples/bank/loan-approval.flow.yaml` (retail unsecured loan, L3→L4 path).

## Status

- Phase 0 scaffolding + 100 issues (this commit).
- Next: Phase 1 metamodel freeze → Phase 2 bank pilot (eKYC + loan + payments).
- Issues: ~100, labelled `track:A..J`, `type:metamodel|engine|ai|touchpoint|data|grc|pilot`.

## Language

Docs + schemas in English (machine-readable). Discussion in issues may be Vietnamese/English.
