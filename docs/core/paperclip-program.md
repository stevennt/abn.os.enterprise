# Paperclip program — start here

The program that puts a **company of AI agents** (Paperclip) to work inside the
existing two authorities: the **Enterprise OS** (the operating model) and
**OpenGate** (the tenant runtime and its evidence). 600 tasks, three tiers, one
queue.

This page is the front door. Everything below is reachable from here; nothing
below is required reading in order except the first three.

## Read first (in this order)

| # | Document | Why |
|---|---|---|
| 0 | `docs/core/paperclip-explainer.md` | the same thing in plain language, no architecture — start here if you are new |
| 1 | `docs/core/paperclip-integration.md` | the boundary: three planes, ten decisions, ownership matrix, seam contracts, security model |
| 2 | `docs/core/adr-002-paperclip-three-planes.md` | the ratification (ADR-002): what was accepted, the consequences, what would reverse it |
| 3 | `docs/core/paperclip-reviews/PC1-01-02-plane-contract.md` | the review that hardened the contract: nine findings, four fixed, five owned |

## The board

- **Issues:** <https://github.com/stevennt/abn.os.enterprise/issues?q=label%3Apaperclip>
  — labels `paperclip`, `loop:6`, `tier:1|2|3`, `target:enterprise|opengate|both`.
- **Catalog (the 600 tasks, dependency order):**
  `docs/core/prompts/paperclip-catalog.json`
- **Task → issue map:** `docs/core/prompts/paperclip-issue-map.json`
- **Prompts (same order as the queue):** `docs/core/prompts/paperclip-queue.json`
- **Generator:** `scripts/paperclip-program.py` — `catalog`, `create`, `queue`,
  `status`.

The catalog order *is* the run order: dependencies are linear inside a
workstream and chain across workstreams. Each workstream is decomposed by a
ten-step ladder that fits its kind (design, build, ops, compliance), so a task
title says what phase it is and what it touches.

The contract has a version — `paperclip-boundary@1.0` — and its upgrade path is
in the contract itself; a company template records the version it was compiled
against, so drift shows up in the record.

## The plan

| Tier | Tasks | Builds |
|---|---|---|
| 1 | 100 | the integration spine: boundary, compiler, adapter, identity, policy, evidence, money, governance, portability, harness |
| 2 | 200 | the platform surface: connector API, records, onboarding with a crew, admin, readiness, metering, quotas, secrets, residency, PII, observability, reliability, security, groups, sync, migration, docs, testing, release, support |
| 3 | 300 | industries, pilots and operations: five industry crews, evals, quality, training, three pilot waves, onboarding playbook, capacity, cost, performance, DR, multi-region, GDPR, SOC 2, sector rules, audit, partners, marketplace, analytics, data platform, SRE, on-call, roadmap, close-out |

## The rules of the board

1. **One issue, one dispatch.** Read the issue, meet every acceptance criterion,
   stage only its files (never `git add -A`), branch `DEV`, `git pull` first.
2. **Verify before claiming.** Each issue carries the exact chain for its target
   repo(s); stop on red.
3. **Commit, push, close with evidence.** `Issue #<n>: ...`, then a `Done:` comment
   with files, proof and repo.
4. **Blocked is an outcome.** Comment why on the issue and stop — do not guess.
5. **Other sessions' work is not yours to stage.** If a shared file is dirty, take
   only your hunk.

## Where the code lives

| Plane | Repo | Entry points |
|---|---|---|
| design (model) | this repo | `metamodel/`, `industries/`, `companies/`, `bin/` |
| execution (agents) | Paperclip (pinned, self-hosted) | its API + UI; our adapter lands in OpenGate |
| tenant + evidence | `abn.platform.opengate` | `gateway/` (contracts), `infra/` (CLIs), `apps/api` + `apps/web` (surface), `docs/` (operator docs). The platform half of this contract is [its docs/paperclip-integration.md](https://github.com/stevennt/abn.platform.opengate/blob/DEV/docs/paperclip-integration.md) |

## Status

As of 2026-11-01 the boundary workstream is in progress: contract (#242), review
(#243) and ratification (#244) are closed; publishing (#245) is this page. The
compiler workstream follows, and it needs the template schema (#252) before the
adapter (#262) can run against a live Paperclip.
