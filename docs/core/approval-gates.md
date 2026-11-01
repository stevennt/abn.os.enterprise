# Approval gates — the authority grid at the decision (contract `approval-gates@1`)

**Status:** interface specified (issue #312); implementation is PC1-08-02…10
(#313–#321). **Shape:** `schemas/approval-gate.json`. **Checker:**
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

## Where it will live

| Piece | Path (planned) |
|---|---|
| the gate | `gateway/approvals.py` (#313) |
| the surface | `infra/approvals.py` — `decide`, `show`, `pending` (#315) |
| the gate check | `--sync` validates the grid and the recorded decisions (#314) |
| the measure | `gateway/approval_metrics.py` — escalations, refusals, gates open too long (#317) |

## Not in this contract

* Amounts in several currencies in one request — the grid is single-currency by
  design, and a second currency is a second grid.
* Delegation and out-of-office — a delegate is a person with a role, not a rule.
* Multi-signature sequences — a later contract; today a gate has one signer.
