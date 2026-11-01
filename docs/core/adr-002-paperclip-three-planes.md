# ADR-002: Paperclip × OpenGate × Enterprise OS — three planes (issue #244) — ACCEPTED

**Status:** accepted (program) — ratified 2026-11-01 after the #243 review.
**Ratifies:** `paperclip-boundary@1.0`.
**Decided by:** the program operator. There is no second review seat yet; that
is recorded here as a risk, not hidden.
**Supersedes:** nothing. **Amends:** the loop-5 boundary assumption that OpenGate
was the only runtime for agent work.
**Inputs:** `docs/core/paperclip-integration.md` (#242 draft),
`docs/core/paperclip-reviews/PC1-01-02-plane-contract.md` (#243 review).

## Context

Paperclip is an open-source control plane for a company of AI agents (org chart,
tickets, heartbeats, approvals, budgets, skills, connectors, run history). The
program already has two authorities: the Enterprise OS owns the operating model
(org, roles, processes, rules, touchpoints, automation levels, packs, contract
pins), and OpenGate owns the tenant runtime and its evidence (identity, folders
and ACL, records, metering, audit, plans, go/no-go). Adding a third system
without a boundary would create two org charts, two task systems, two ledgers and
two audit trails — each pair disagreeing within a quarter.

The question this ADR settles: **which plane is authoritative for what**, and
what crosses the seams.

## Decision

Adopt the **three-plane split** and its ten decisions (D1–D10) as written in
`docs/core/paperclip-integration.md`:

- **Enterprise OS — design plane.** Owns the model: org units, roles, reporting
  lines, processes and steps with their automation level, rules, touchpoints,
  packs, companies and the contract pin. It **compiles** a company template; it
  does not run work.
- **Paperclip — execution plane.** Owns work state: tickets, checkout locks,
  heartbeats, runs, agent org, skills, approvals inbox, budgets as a throttle,
  connectors. Its tickets are **ephemeral**; the durable record lives elsewhere.
- **OpenGate — tenant and evidence plane.** Owns the tenant boundary: identity
  (ONEID), companies, org charts, folders and ACL, `dataMode`, the resolved run
  context, records (cases/documents), metering, the signed audit chain, plans and
  the go/no-go scorecard.

The seams are four contracts (company template, run context, activity event,
budget policy), and the crossings are one-way by decision:

| Crossing | Direction | Frequency | Mechanism |
|---|---|---|---|
| company template (pinned) | Enterprise → Paperclip | on change, re-compiled | `bin/paperclip-company` + import |
| run context | OpenGate → Paperclip | every heartbeat | signed context file + env |
| activity event | Paperclip → OpenGate | every run transition | audit line + metering event |
| budget policy | OpenGate → Paperclip | on plan/overage change | seeded policy |

## Consequences

- **Positive:** one org model, one record system, one ledger, one identity tree;
  agents inherit the tenant's ACL and classification instead of being trusted;
  the scorecard can gate a crew; cost is attributable per company and per agent
  without a second invoice.
- **Negative (accepted):** the compiler is a real component to maintain, and a
  model change requires re-compile + diff; Paperclip upgrades must be re-tested
  against the adapter; a Paperclip outage stops agent work but not the tenant's
  portal (OpenGate is independent).
- **Cost:** one more service to run (Postgres + runner), pinned and telemetry-off.
- **Migration:** existing tenants are unaffected until a crew is compiled for
  them; nothing in the loop-5 contracts changes shape.

## What would reverse this

1. **Paperclip grows a tenant/ACL model** that OpenGate can delegate to without
   losing folder-level and `dataMode` enforcement — then D3 (all access through
   OpenGate) is revisited, not the whole split.
2. **Compile drift becomes unmanageable** — more than a handful of routines
   diverging per release, or the diff review taking longer than the change — then
   the template becomes generated-on-read instead of imported.
3. **A second review seat appears** and disagrees with D1/D2/D5 — those three are
   the load-bearing ones; reopening any of them reopens this ADR.

## Rejected alternatives

Recorded in the contract's *Alternatives considered* table and the #243 review:
bidirectional sync, Paperclip as system of record, its secret store, two ledgers,
task mirroring, prompt-level guardrails, library embedding, per-tenant Paperclip
instances, and a ONEID session minter instead of OIDC.

## Open items inherited by the tiers

| Item | Owner | Issue |
|---|---|---|
| run-context mode in `resolve.py` | policy | #283 |
| agent service accounts (no password) | identity | #273 |
| per-agent budget vs tenant ceiling, group split | money | #302 |
| company-template schema | compiler | #252 |
| OpenGate-down semantics (fail closed) | reliability | #352 |
