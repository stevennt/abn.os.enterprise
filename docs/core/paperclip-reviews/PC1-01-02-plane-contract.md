# Review — plane boundary contract (PC1-01-02, issue #243)

- **Reviewer:** operator (single reviewer; the program has no second seat yet)
- **Subject:** `docs/core/paperclip-integration.md` at `c1163d9` (draft from #242)
- **Verdict:** **accepted for the compiler work** (tier 1, PC1-02). Five findings
  are deferred to named issues; the three that block the adapter (F1, F3, F4) must
  be closed before PC1-03 runs against a live Paperclip.
- **Method:** read each decision and seam against the code it names, not against
  the prose. Evidence is a file/line or a command, quoted per finding.

## Findings

| # | Sev | Finding | Evidence | Disposition |
|---|---|---|---|---|
| F1 | major | Seam 2 ("run context") names a `gateway/resolve.py` capability that does not exist — there is no run-context mode, no schema, and the adapter would have to invent one. | `grep -n "run-context\|run_context" gateway/resolve.py` → no match | **resolved**: the contract now marks it "not built yet", names the owner, and requires the adapter to fail closed until it exists (PC1-05-02, #283) |
| F2 | major | Seam 3 says OpenGate "appends it to `audit.jsonl`", but the audit writer has a fixed signed line and the event has fields it does not carry (agent, run, cost). Without a mapping, the evidence would be a second, unsigned format. | `apps/api/src/companies.core.ts:476` (`auditAppend` writes `{at, tenant, actor, actorRole, action, target?, detail?, prev, sig, alg}`) | **resolved**: the contract now maps event → line (`actor` = agent account, `actorRole` = `agent`, `action` = kind, `detail` = responsible user/artifact/approval) and sends cost to metering only |
| F3 | major | "Agents are OpenGate service accounts" is not modelled: `accounts.json` has no service-account shape, the store has no schema, and the admin path requires a password, which an agent must not have. | `gateway/seats.py:112` (`_accounts` reads `{id, role, unit}`, credentials never loaded); `apps/api/src/admin.controller.ts` (`password` required); `schemas/` has no accounts schema | **deferred** → PC1-04-02 (#273), owner: identity workstream. Decision needed: token-only agent accounts (no credential) and the store shape. Blocks the adapter's real run. |
| F4 | major | Budget policy is per agent/company in Paperclip but OpenGate's plan limits are per tenant (`seats`, `storageMb`, `jobsPerMonth`). The contract does not say how a group tenant splits one ceiling across companies or agents. | `gateway/plans.py` `effective()` returns `limits` per tenant only; `onboarding/plans.json` has no per-company split | **deferred** → PC1-07-01 (#302), owner: money workstream. Rule to implement: the plan is the ceiling; per-company budgets are an explicit split (weights or declared policy), never an inferred one. |
| F5 | minor | "Paperclip connectors for tenant data are disabled" is a configuration claim with no enforcement point — nothing checks it, and an operator can add a connector tomorrow. | no check exists in either repo (grep for a connector/credential scan returns nothing) | **resolved**: the security model now states a checkable rule — no tenant credential outside the vault, the OpenGate tool surface is the only path — and the scan is owned by PC1-05 |
| F6 | minor | The company template has no schema, so the compiler cannot be validated and Paperclip's import cannot be tested against a contract. | `schemas/` has no `paperclip-company.json`; the catalog's PC1-02-01 is the first compiler task | **deferred** → PC1-02-01 (#252), owner: compiler workstream. Deliverable: the schema + a golden template fixture. |
| F7 | minor | "Import refuses an unresolvable pin" duplicates a rule that already exists for company models; two implementations would drift. | `scripts/validate_company.py` + `docs/core/onboarding-company.md` (tag/sha resolution) | **resolved**: the compiler must call the same resolver, not reimplement it (noted in the review; enforced by PC1-02-09) |
| F8 | minor | Nothing says what a heartbeat does when OpenGate is unavailable: run anyway (unsafe), queue, or fail? | no failure semantics in the contract; the adapter task (PC1-03) has none either | **deferred** → PC2-12-01 (#352), owner: reliability workstream. Rule: fail closed — no run without a signed context; the ticket stays queued with a reason. |
| F9 | minor | The "one work item" strip ends at "statement line", implying every run is billable; internal or rework runs would inflate a statement. | `docs/core/paperclip-integration.md` work-item strip; `gateway/metering.py` distinguishes billable events | **resolved**: the contract now says audit always, metering only for billable kinds |

## What changed in the contract because of this review

- seam 2 carries a **not-built-yet** marker and the owning issue;
- seam 3 gained the **activity → audit-line mapping** and the billable rule;
- the security model gained the **checkable no-tenant-credentials rule**;
- a **Reviews** section links this record;
- F7 is recorded as a rule for the compiler (reuse the existing pin resolver).

## What is still open (with an owner and an issue)

| Finding | Owner workstream | Issue | Blocks |
|---|---|---|---|
| F3 agent accounts | identity | #273 | the adapter's first real run |
| F4 budget split | money | #302 | group-tenant pilots |
| F1 run context | policy | #283 | the adapter's context |
| F6 template schema | compiler | #252 | Paperclip import test |
| F8 OpenGate-down semantics | reliability | #352 | production hardening |

**Reviewer's note:** F1, F3 and F4 are the ones that would have turned into
"works in the demo, fails for the second tenant". They are now owned, and the
adapter task (#262) inherits them as entry conditions.
