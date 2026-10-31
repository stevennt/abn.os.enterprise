# ROADMAP — where this stands, and what is deliberately deferred

## Done

| Loop | Scope | Result |
|---|---|---|
| 1 (issues 1–100) | the model | 8 schemas and the first industry as a reference implementation (13 units, 15 flows, 4 rule packs, 40 events), a 700-row golden set, ~30 validators, a real Camunda stage |
| 2 (101–120) | specs → running systems | stage live (trace, timer, crash recovery), deterministic data generators, drills that execute, evidence packs, cost numbers |
| 3 (121–122) | boundary with the agent platform | business truth and agent content in one repo; platform consumes bundles |
| 4 (123–140) | multi-industry | `industries/<id>/` layout, industry manifest + pack contract, per-industry release streams, verified bundles, tier/split rule, onboarding in one command |

## Now

- **Banking** is the reference industry (active pack, both tag streams, bundle consumed
  by the platform as `banking-pack-2026.10.1`).
- **Legal** is a structure-only scaffold: no article numbers, penalties or deadlines
  asserted; rule rows carry `authority: pending-review` and CI enforces the boundary.
- **Validation** is the product: ~30 checks run per push, including "no asserted claim
  without a cite", "ids unique across industries", "no hardcoded industry path", and
  "the onboarding playbook covers every CI script".

## Deferred, on purpose

| Item | Why not yet | Trigger to start |
|---|---|---|
| Live pilot against a real core/branch system | needs an owner, access, and a go-decision — not a coding task | `industries/banking/docs/pilot-0-ekyc.md` signed off |
| Substantive legal rules | requires a named qualified reviewer per row | reviewer named in `industries/legal/docs/status.md` |
| A third industry with real depth | two prove the contract; a third should be a business decision | an industry sponsor exists |
| Classified industries (`defense-ops`, `civil-protection`) | they do not belong in this repo at any label | split repo created per `docs/core/confidentiality.md` |
| AI steps actually calling models | contracts + goldens exist; runtime lives in the agent platform | platform bundle path in production |
| Camunda → production topology | stage proves semantics, not operations | load-test SLO review (`docs/core/loadtest.md`) |

## Bets (unchanged, and now tested rather than assumed)

1. **Don't build a workflow engine.** Camunda 8 was chosen on evidence and validated
   on a live stage; building durable execution is a two-year trap.
2. **Don't let an LLM be the router.** Deterministic classification, version pinned;
   models only inside `ai` steps with a schema and an eval gate.
3. **Co-locate prose and policy.** The citation checker could not see semantic drift;
   one repository per industry can.
4. **Consume artifacts, not checkouts.** Bundles with per-file hashes and an archive
   hash; a tampered bundle is refused instead of half-applied.
5. **Evals before autonomy.** No step reaches L4 without a green suite and a 30-day
   audit window.
6. **Audit is a feature.** Every step emits who/what/rule-version/model-version, and
   the chain is verifiable — replay must reproduce the decision.

## Next decisions for the owner (not engineering)

1. Which industry gets real depth second — and who sponsors it.
2. Whether the legal pack proceeds (that means naming a reviewer and budgeting time).
3. When banking goes live, with which caps and which branch.
