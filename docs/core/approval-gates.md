# Approval gates — the authority grid at the decision (contract `approval-gates@1`)

**Status:** interface specified (#312), implemented in `gateway/approvals.py`
(#313); the wire, record, surface, harden, measure and demo steps follow
(#314–#321). **Shape:** `schemas/approval-gate.json`. **Checker:**
`scripts/check_approval_spec.py` (CI, `--self-test`). **Boundary:** ADR-002 D6 —
*approvals are clicked in Paperclip, decided by the authority grid.*

The authority grid already exists in the tenant: `authority.json` per company
(optionally a group grid with an explicit `appliesTo`), `authority_limits()` and
`can_approve()` in `gateway/tenant_registry.py`, and RACI in `assignments.json`.
What does not exist is the **gate**: the object that takes a request, finds who may
decide it, refuses a maker who tries to check their own work, escalates when the
clicked approver is too small for the amount, and records the decision with the
signer.

```
request ──▶ gate.decide(request, approver)
                 │ grid (authority.json) ─ can_approve ─┐
                 │ assignments (RACI, units, roles) ────┤──▶ decision + audit line
                 └──────────────────────────────────────┘
```

## What this contract is not

* **Not an approval inbox.** Paperclip renders the button (D6); this is the rule
  behind it and the record after it.
* **Not a second authority grid.** The limits stay in `authority.json`; a gate
  never widens them and never invents a default. No grid means no approval —
  fail closed, exactly as `can_approve` already behaves.
* **Not a workflow engine.** One request, one decision. Sequences of gates (a
  memo needing two signatures) are a later contract.

## Inputs

### 1. The request

| Field | Rule |
|---|---|
| `kind` | one of `payment`, `memo`, `release`, `exception` — what is being approved |
| `amount` | a number ≥ 0, in the grid's currency |
| `currency` | required; must equal the grid's currency (`E-GOV-02` otherwise) |
| `requester` | the account asking — a person or an agent |
| `unit` | the unit the request belongs to; the approver's role must be held **here** |
| `company` | the company whose grid applies |

### 2. The approver (the human who clicked)

`{account, role, unit}` as held in `accounts.json` / the org chart. Two
refusals apply before any limit is consulted:

* **an agent cannot approve** — D6 says the signer is a human; an agent account is
  `E-GOV-04`;
* **the requester cannot approve their own request** — maker/checker, also
  `E-GOV-04`. Same account, not "same team": a control that depends on team
  membership is not a separation of duties.

### 3. The grid

`authority_limits(root, tenant, company)` — `{role: maxAmount}` and the currency.
The company grid wins per role over a group grid; a group grid applies only to the
companies in `appliesTo`.

### 4. The RACI

`assignments.json` names the accountable unit for a function. The gate uses it to
answer "who *should* sign this" when the clicked approver is too small, and to
report an escalation target rather than a bare refusal.

## Outputs

One decision record — `schemas/approval-gate.json`:

```json
{
  "version": 1, "contract": "approval-gates@1",
  "id": "ap-6b1f0c2a9d4e77b3",
  "tenant": "acme", "company": "acme",
  "request": {"kind": "payment", "amount": 120000000, "currency": "VND",
              "requester": "agent-co", "unit": "finance"},
  "gate": {"approver": "admin-1", "role": "admin", "limit": 5000000000,
           "currency": "VND"},
  "decision": "approved",
  "reason": "admin-1 (admin) may approve 120000000 (limit 5000000000)",
  "escalateTo": null,
  "at": "2026-11-01T09:00:00.000Z"
}
```

| Field | Meaning |
|---|---|
| `id` | `ap-` + `sha256(tenant|company|request.id)` — one id per request, so a retry cannot open a second gate |
| `decision` | `approved` · `refused` · `escalated` |
| `gate` | the approver, their role, the limit that applied and the currency — the numbers the decision was made against, frozen |
| `escalateTo` | the `{role, limit}` that can approve, when `decision` is `escalated` |
| `reason` | one sentence naming the limit or the rule that decided |

Every decision writes **one** audit line: `approval.granted`, `approval.refused`
or `approval.escalated`, with `target` = the request id and `detail` = the code
(when refused) and the limit. A refused approval is evidence too — the record of
*who tried* is the point of maker/checker.

## The decision procedure (ordered)

1. **shape** — a malformed request is `E-GOV-01` (a number that is a bool, a
   negative amount, a kind not in the vocabulary, a missing currency).
2. **already decided** — the same decision returns the record (`duplicate: true`);
   a *different* decision on the same request is `E-GOV-06`. A gate is not a
   vote, and reopening one hides the first signature.
3. **an agent cannot approve** — `E-GOV-04`.
4. **the requester cannot approve their own request** — `E-GOV-04`.
5. **the approver's role is held at the request's unit** — otherwise `E-GOV-05`;
   a role the org chart posts elsewhere has no authority here.
6. **a grid exists and the currency matches** — otherwise `E-GOV-02`.
7. **within the limit** → `approved`; **over it** → `escalated` to the smallest
   role held at the unit that can approve the amount; **nobody can** → `E-GOV-07`.

The order is the graph: shape → decided → who → where → how much → can any. Each
step refuses for its own reason, and the reason is a sentence an operator can act
on (`#299`'s rule).

| Code | When | What the operator does |
|---|---|---|
| `E-GOV-01` | the request is malformed | fix the caller; the gate does not guess a default |
| `E-GOV-02` | no grid for the company, or the currency does not match | write `authority.json`; a currency mismatch is a control failure, not a conversion |
| `E-GOV-03` | the amount exceeds the approver's limit **and** someone else can approve it — reported as `escalated`, never silently approved | route it to the named role |
| `E-GOV-04` | an agent tried to approve, or the requester tried to approve their own request | have a human who is not the requester click it |
| `E-GOV-05` | the approver's role is not held at the request's unit | post the role at that unit, or route to one that holds it |
| `E-GOV-06` | a different decision was already recorded for this request | read the record; a gate is decided once |
| `E-GOV-07` | no role at the unit can approve the amount (escalation exhausted) | raise a limit, or route to the group with an explicit grid |
| `E-GOV-08` | a standing decision was edited, added or deleted after the store was sealed, or the seal itself was altered | re-seal after an intended change; an approval that can be rewritten is not an approval |

## The arithmetic

```
limit(approver) = grid[role(approver)]              # per role, company grid wins
within          = amount <= limit(approver)
escalateTo      = min({role: limit ≥ amount} held at request.unit, key=limit)
```

`limit ≥ 0` is required by `authority.json`'s own validation; a role with no limit
is absent from the grid, and absent is not unlimited.

## Worked example

`tests/fixtures/approval/case.valid.json` — one company, a grid
(`credit-officer` 500 000 000 VND, `admin` 5 000 000 000 VND), roles posted at
`finance`, and four requests:

| Request | Clicked by | Decision |
|---|---|---|
| 120 000 000 payment, requested by an agent | `admin-1` (admin) | `approved` |
| the same, clicked by the requesting agent | `agent-co` | `refused` — `E-GOV-04` |
| 800 000 000 payment | `credit-officer-1` (credit-officer, limit 500 M) | `escalated` to `admin` |
| 9 000 000 000 payment | `admin-1` | `refused` — `E-GOV-07`, nobody can approve |

`scripts/check_approval_spec.py` recomputes every decision from the grid and the
requests and fails on a byte of drift; `--self-test` mutates the case to prove
each code fires for its own reason.

## The runbook

`abn.platform.opengate/docs/approvals-walkthrough.md` is the generated, end-to-end
transcript (#318): an approval, both maker/checker refusals, an escalation, a
request nobody can approve, a replay, a second different decision, the inspection
commands, the seal and its silent repeat, the non-admin refusal, and a decision
tampered after sealing. `--check` regenerates and diffs it, so a stale transcript
fails the suite.

## The operator surface

`infra/approvals.py` in the tenant repo: `decide` (the actor is the approver; exit
0 for approved/escalated, 1 for refused), `show` and `list` (admin-only — a
decision names who approved what and for how much), `seal` (admin-only) and
`check` (no actor: it reads what `--sync` reads).

## The conformance matrix

The implementation's matrix is `abn.platform.opengate/tests/test_approval_matrix.py`
(#315): 26 cases, each asserting which code fires **and why**. It covers a clean
payment and an amount exactly at the limit; escalation to the smallest role that
fits; `E-GOV-07` when nobody can; the requester and an agent refusing themselves;
a role absent from the unit, from the grid, and a unit that does not exist
(`E-GOV-05`); no grid and a currency mismatch (`E-GOV-02`); eight malformed
requests and an unknown approver (`E-GOV-01`); a second different click
(`E-GOV-06`); a replay that writes nothing; and a tampered decision in the store.
A final case asserts the matrix covers every code — `E-GOV-03` counted as the
escalation, which is a decision rather than a message.

## Where it will live

| Piece | Path (planned) |
|---|---|
| the gate | `gateway/approvals.py` (#313) — `decide`, `record_of`, `decisions`, `validate_records` |
| the surface | `infra/approvals.py` — `decide`, `show`, `list`, `seal`, `check` (#317) |
| the gate check | `--sync` validates the grid and the recorded decisions (#314) |
| the measure | `gateway/approval_metrics.py` — escalations, refusals, gates open too long (#317) |

## Where it fires today (#314)

The first real path is tenant deletion (`infra/offboard_tenant.py --yes
--confirm`): a tenant **with** an authority grid needs `--approver <account>` — a
second person whose role is in the grid — and the decision is written into the
signed deletion certificate under `approval`, because the deletion removes the
tenant tree and with it the audit lines. A tenant **without** a grid keeps the
`--yes`/`--confirm` guard and nothing else: failing closed there would strand
every legacy tenant. The gate is the same `approvals.decide`; there is no second
implementation on the delete path.

## The measurement (#320)

`gateway/approval_metrics.py` in the tenant repo: `G1` refusal-spike and `G2`
probing-approver read the **chain** (a refusal is an attempt, never a standing
decision), `G3` open-escalation reads the **store** (an escalation is a route
somebody must walk), and `G4` is trust. Alerts are one line per rule per day;
`--sync` validates the store and the drill proves each fires while a clean tenant
stays quiet.

Writing `G3` found a bug: the implementation stored an escalated request as the
standing decision, so the role it named could never approve it (`E-GOV-06`). An
escalation is a route, not a verdict — `decide` now lets the named role (or any
role whose limit covers the amount) **supersede** it, and the audit line records
`supersedes: "escalated"`.

## Hardening

The implementation's edges (#319), each with its code: the tenant is a path
(`E-GOV-01`, checked before identity and before any profile read); a decision file
is a symbolic link (`E-GOV-08`, the target named and never written); a second
writer holds the tenant's lock (`E-GOV-01 … the store is busy`, 300 s TTL for a
crashed holder); and a decision whose `at` or `gate.limit` is not what the shape
says (`E-GOV-01` from `validate_records`).

**The lock is a governance fix.** Without it, two approvers clicking one request
in the same second both read "no standing decision" and both write, leaving two
grants for one request that no validator would catch — each file is individually
valid. The lock is `O_EXCL`, released in a `finally` (including on a failed
decision), and taken over after its TTL.

## The seal (#316)

`approvals.seal()` pins every standing decision by digest and puts one chain over
the set, in `customers/<t>/approvals/sealed.json`. `--sync` compares the store to
it, so an edited decision, one recorded after the seal, one deleted, or a tampered
seal are each `E-GOV-08`. Sealing an unchanged store is silent, and an unsealed
store is valid — sealing is a deliberate act, and re-sealing after an intended
change is the workflow.

## Recorded, not guessed

The implementation stores a decision under
`customers/<t>/approvals/ap-<sha256(tenant|company|request.id)[:16]>.json`, so a
retry cannot open a second gate and `--sync` can prove the file name matches its
own content. A **refused** click is different: it writes one `approval.refused`
line and no file, because a refusal is evidence of an attempt and the right
approver must still be able to decide. Only `approved` and `escalated` become the
request's decision.

## Not in this contract

* Amounts in several currencies in one request — the grid is single-currency by
  design, and a second currency is a second grid.
* Delegation and out-of-office — a delegate is a person with a role, not a rule.
* Multi-signature sequences — a later contract; today a gate has one signer.
