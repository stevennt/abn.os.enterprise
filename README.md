# abn.os.enterprise — Autonomous Enterprise OS

> **Problem:** model 100% of an enterprise's operations — departments, org-charts,
> staff, processes, regulations — so that every situation, with defined inputs and
> data, routes through the right process flow and runs automatically. Workflow where
> possible, AI where judgement is needed, humans only at explicit touchpoints.
>
> **Goal:** near-100% autonomous operation with full auditability — for **any**
> industry, with one shared contract and one auditable model per industry.

## Multi-industry by construction

This repo is a **contract plus a set of industries**, not one company's project:

```
metamodel/            the contract (6 primitives + industry manifest + pack schema)
industries/<id>/      one industry each: org, rules, flows, events, ai, evals, pack, docs
companies/<id>/       one legal entity's operating model, pinned to a contract release
docs/core/            knowledge that applies to every industry
```

Every industry is a folder that must pass the same checks. Nothing in `docs/core/`
or `scripts/` knows a specific industry's name — new industries are discovered by
globbing, and `bin/new-industry <id>` produces a passing scaffold in one command
(`docs/core/onboarding-industry.md`).

| Industry | Tier | Content |
|---|---|---|
| `banking` | commercial | 13 org units, 15 flows, 4 rule packs, 5 AI contracts, active agent pack |
| `legal` | commercial | 3 org units, 1 flow, 2 structural rule packs, draft pack (structure only, no asserted law) |

`public`/`commercial` live here. `restricted`/`classified` industries live in their
own repository with a vendored metamodel — `docs/core/confidentiality.md` explains why
a folder label is not access control.

## 6 primitives (everything in this repo hangs off these)

| # | Primitive | File | Question it answers |
|---|-----------|------|---------------------|
| 1 | `OrgUnit` + `Role` | `metamodel/org.schema.yaml` | Who exists? Who may do/approve what? |
| 2 | `Process` | `metamodel/process.schema.yaml` | What is the flow? Inputs → steps → outputs? |
| 3 | `Rule` | `metamodel/rule.schema.yaml` | What policy/regulation constrains the flow? |
| 4 | `Event` + `Data` | `metamodel/event.schema.yaml` | What triggers/inputs arrive? What leaves? |
| 5 | `Touchpoint` | `metamodel/touchpoint.schema.yaml` | Where does a Customer / Employee / System / External party meet the flow? |
| 6 | `AutomationLevel` L0–L5 | `engine/automation-levels.md` | Can this step run as workflow, AI, or needs human? |

Two further contracts make it multi-industry: `metamodel/industry.schema.yaml` (what
an industry must declare) and `metamodel/pack.schema.yaml` (the agent-pack shape
consumed by the execution platform).

```
Event(Data) → Router → Process(Step[workflow|ai|human] + Rule + Role) → Touchpoint → Output + Audit
```

## Repo map

```
README.md                  — this file
ARCHITECTURE.md            — runtime options + recommended hybrid stack
ROADMAP.md                 — phases, gates, and what is deliberately deferred
metamodel/                 — the contract: 8 JSON Schemas (6 primitives + industry + pack)
companies/                 — per-company operating models (tenant + entity, pinned to a contract tag)
industries/                — one folder per industry: org, rules, flows, events, ai, evals, pack, docs
docs/core/                 — shared knowledge: gates, security, PII, release, bundles, onboarding
engine/                    — automation levels, workflow-vs-AI matrix, capacity model, stage env
scripts/                   — validators and drills (every one runs in CI)
bin/                       — operator tools: tag-industry, build-pack, new-industry
```

To bring a customer on: `docs/core/onboarding-tenant.md` (the contract view,
with owners and evidence), then the operator's commands in the platform repo
(abn.platform.opengate, its docs/onboarding-tenant.md page). The gate before
go-live is `docs/core/readiness-scorecard.md` — ten gates, each with evidence,
and a recorded decision. To model a legal entity inside that tenant:
`docs/core/onboarding-company.md`; to add an industry:
`docs/core/onboarding-industry.md`.

## How to model any department (repeatable recipe)

1. **Org:** list units → roles → headcount → RACI per flow (`industries/<id>/org/`).
2. **Inputs:** for each situation, write the input JSON schema + trigger event.
3. **Flow:** mark steps `workflow` (deterministic) / `ai` (judgement) / `human` (approval or touch), with the L0–L5 level.
4. **Rules:** policy rows as DMN-style tables, cited by flow steps, never embedded in code.
5. **Touchpoints:** every C/E/S/X contact with channel and SLA.
6. **Close the loop:** outputs → KPI → audit event → simulation replay.

Worked example: `industries/banking/flows/loan-approval.flow.yaml` (retail unsecured
loan, L3 → L4 path) with a verified trace beside it.

## What "validated" means here

Every push runs ~30 checks. The ones that bite:

- schemas + manifests valid, org index reconciles with full unit files, catalogs non-empty
- every flow has owner + rule + SLA + fail-path, and a trace whose audit chain verifies
- rule packs: no duplicate `when`, wildcard coverage row present
- packs: schema, cross-file refs, cites resolve to same-repo rules/flows, no asserted
  claim without a cite or an explicit `placeholder:`
- ids globally unique across industries; no cross-industry references; tier hosted here
- no script hardcodes an industry path; the onboarding playbook covers every CI script
- bundles are deterministic and a tampered bundle is refused

## Status

- Contract frozen (8 schemas); banking is the reference industry; legal is a
  deliberate structure-only scaffold.
- Execution proven on a real engine stage (Camunda 8, trace + timer + crash recovery);
  agent packs are consumed as verified bundles, not git checkouts.
- Not yet done: live pilot against a real branch/core system, substantive legal content
  (blocked on a named reviewer), and a second commercial industry with real depth.

## Language

Docs + schemas in English (machine-readable). Issue discussion may be Vietnamese or
English.
