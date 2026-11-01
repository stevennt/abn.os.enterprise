# Tenant onboarding with a crew — `tenant-crew@1` (issue #362)

**Status:** specified (#362), implemented (#363), wired (#364), tested (#365),
recorded (#366), surfaced (#367), documented (#368), hardened (#369); measure
(#370) and demo (#371) follow. **The runbook:**
[tenant-crew-walkthrough.md](https://github.com/stevennt/abn.platform.opengate/blob/DEV/docs/tenant-crew-walkthrough.md)
— the roster, the eight steps with their refusals, the gate, the handover. **Boundary:** ADR-002 D3 and D4 — every data access goes through
the OpenGate API, and **agents are service accounts with a responsible person**.
**Shape:** `schemas/tenant-crew.json`. **The executable oracle:**
`scripts/check_tenant_crew_spec.py` (`--self-test` mutates the record eight ways).

A tenant can be provisioned by one operator with a guide, as
[onboarding-tenant](../../../abn.platform.opengate/blob/DEV/docs/onboarding-tenant.md)
describes. A **crew** is the same onboarding performed by agents, and it changes
one thing and only one: *who runs each step, and what that person is allowed to
run*. The steps stay the steps a person already runs — a crew is a staffing
decision, not a second process.

```
commercial pack (ready) ─┐
company model            ├─▶ the crew ─▶ tenant files · accounts · agents · grants
industry pack            ┘      │            │
                                │            └─▶ every step is a command that
                                │                already exists and is validated
                                └─▶ one record: who ran what, in what order,
                                    and which person signed the handover
```

## What a crew is not

- **Not a second onboarding process.** The eight steps are the existing commands;
  the crew is the roster and the record, not a new pipeline.
- **Not a way to skip the person.** A crew prepares the handover; a **person
  signs it** (`goNoGo.signedBy` must be one of the tenant's people, never a
  member). D4 in one line: an agent acts, a person answers.
- **Not a permission of its own.** A member's mandate is *which steps it may
  run*; the tenant's own gates (ACL, `dataMode`, plans) still decide what the
  step may touch.
- **Not a budget holder.** The crew runs inside the tenant's plan; a member that
  would exceed it is refused by the quota gate, not by the crew.

## The eight steps

| # | Step | What it produces | Who may run it |
|---|---|---|---|
| 1 | `commercial` | the pack is parsed and its gaps named | the crew (never the person who signs) |
| 2 | `company` | the tenant and its company/companies exist | the crew |
| 3 | `org` | the chart: units, parents, roles posted | the crew |
| 4 | `accounts` | people, with credentials they hold themselves | the crew **may not** set or read a credential |
| 5 | `crew` | the agent accounts: `kind: agent`, owner, purpose | the crew |
| 6 | `folders` | the ACL: which unit may read/write which folder | the crew |
| 7 | `plans` | the plan, its ceilings, the trial window | the crew |
| 8 | `verify` | `resolve.py --sync` green — which now reads this record too (#364) — and the record written | the crew |

Then the handover: `goNoGo` — a person's signature, with a decision and a time.

**Order is the contract.** Step *n* may not run before step *n−1*: an account
cannot be created before the unit it sits in, a grant cannot be set before the
folder exists, and `verify` is only meaningful after everything else.

## Inputs

| Input | From | Notes |
|---|---|---|
| the commercial pack | `customers/<tenant>/commercial-pack.json` | must be `ready`; a draft onboarding provisions the wrong departments |
| the company model | `companies/<id>/company.yaml` (design plane) | the departments, the industry, the boundary pin |
| the industry pack | `industries/<industry>/` | the roles the chart posts and the skills the crew's agents reference |
| the plan | `onboarding/plans.json` | seats, agents named in the crew count against it |
| the people | the operator's list | a crew member's `owner` must be one of them |

## Outputs

One record per onboarding, `customers/<tenant>/crew.json` (shape:
`schemas/tenant-crew.json`):

```json
{"version": 1, "contract": "tenant-crew@1", "tenant": "demo", "company": "demo",
 "pack": {"id": "banking", "status": "ready"},
 "boundary": "paperclip-boundary@1.0",
 "people": [{"id": "admin-1", "role": "admin", "unit": "finance"}],
 "units": ["finance", "credit"],
 "members": [{"id": "agent-intake", "role": "intake-officer", "unit": "credit",
              "kind": "agent", "owner": "admin-1",
              "purpose": "Read the commercial pack and open the company.",
              "steps": ["commercial", "company"]}],
 "steps": [{"id": "commercial", "by": "agent-intake",
            "at": "2026-11-02T09:00:00Z", "result": "ok"}],
 "goNoGo": {"signedBy": "admin-1", "at": "2026-11-02T09:08:00Z",
            "decision": "go"}}
```

The record is the **join** between three things a tenant otherwise keeps apart:
who the tenant's people are (`people`), which agents exist and why (`members`),
and what actually happened (`steps`). A tenant that was onboarded by a crew can
answer *who gave this agent the right to provision accounts* from this file
alone.

## Refusals

| Code | When |
|---|---|
| `E-CRW-01` | the record does not match the schema, or its contract pin is another version |
| `E-CRW-02` | the commercial pack was not `ready` when the crew started |
| `E-CRW-03` | the steps ran out of order, a step is doubled, or one is missing |
| `E-CRW-04` | a step was run by a member whose mandate does not name it |
| `E-CRW-05` | a member is not an agent, or its owner is not one of the tenant's people |
| `E-CRW-06` | a member's unit is not on the tenant's chart |
| `E-CRW-07` | an id is used twice, or a member runs no step |
| `E-CRW-08` | an agent performed a person's act — signing the go/no-go, setting a credential, disabling an account — or the handover is not last |

Every code names its fix (`FIX` in the oracle), because the audience is an
operator who has to finish the onboarding, not a developer who has to read a
traceback.

**Hardened (#369).** A linked record or a linked chain is refused rather than
followed; the writers take a per-tenant lock, so two runners cannot record one
step twice and skip another; and `init` refuses to *create* the agents it names —
an account is the identity store's to make, with an owner and no credential. The
crew may name an agent; it may never invent one.

## Who may read it, and who may sign it (#367)

Two permissions, and the split is the contract's own:

| Action | Who | The rule |
|---|---|---|
| read the record | **tenant admin** | it names who onboarded the tenant and what each agent may do |
| sign the handover | **a person of this tenant** | `E-CRW-08` — never a member, and the signing principal is the one the credential belongs to |

So a token minted by an agent cannot sign a handover, not because a surface adds
a rule but because the record already refuses a member's signature. That is D4
expressed as an authorisation decision rather than a sentence.

## The tenant half

The crew's *record* is written here, on the design plane, because the roster is a
design decision. The **evidence** lives in the tenant: the agent accounts
(`accounts.json`), the units (`org.json`), the grants (`folders.json`) and the
`--sync` that proves them. The tenant-side contract is
[tenant-crew.md](https://github.com/stevennt/abn.platform.opengate/blob/DEV/docs/tenant-crew.md),
and the seam is the same one the adapter uses: the design plane never writes a
tenant file, and the tenant never reads a company model.

## Wired (#364)

The crew is not a side artefact: **the record is checked by the gate the tenant
already runs**. The OpenGate `resolve.py --sync` calls the tenant-side
`crew.validate_tenant`, which applies the same rules this page states — the order,
each step inside its member's mandate, an owner who is a person, units on the
chart, and a handover that is a person's and comes last. So a tenant that was
onboarded by a crew cannot be `--sync`-green with a record that contradicts what
it did, and a tenant onboarded by one operator (no crew, no record) stays valid:
**the gate requires no crew, only that a crew's record, if present, is true.**

**And the record is backed by the chain (#366).** Every step also appends one
`crew.step` line to the tenant's signed audit chain (attributed to the member),
and a handover appends `crew.signed` with `actorRole: person`. The tenant's check
requires, for every step, a line with that actor and that target — so a record
cannot claim work the chain does not have, and a rewritten `by` is a contradiction
in two places at once.

The two checkers are deliberately two: the tenant's writer *prevents* an invalid
record from being written, and this plane's oracle *detects* one that was edited
after the fact. One contract page, one order table, one set of codes.

## The oracle

`python scripts/check_tenant_crew_spec.py [path]` checks one record; `--self-test`
mutates the committed fixture eight ways — one per code — and proves each refusal
fires **for its own reason**:

```
$ python scripts/check_tenant_crew_spec.py
tenant crew: OK — the record describes a crew that was allowed to do the work
$ python scripts/check_tenant_crew_spec.py --self-test
self-test: E-CRW-01 … E-CRW-08
self-test: 8 mutations refused, the fixture clean — OK
```
