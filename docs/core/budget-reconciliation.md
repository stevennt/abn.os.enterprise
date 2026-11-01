# Budget reconciliation — plan quota vs agent budgets (contract `budget-reconciliation@1`)

**Status:** interface specified (issue #302); implementation is PC1-07-02…10
(#303–#311). **Shapes:** `schemas/budget-store.json` (the input the tenant
writes) and `schemas/budget-reconciliation.json` (the report this contract
produces). **Checker:** `scripts/check_budget_spec.py` (CI, with `--self-test`).
**Boundary:** ADR-002 D5 — *OpenGate is billing truth; Paperclip budgets are a
throttle.*

Two ceilings already exist and never meet:

* the **plan quota** a tenant bought — `seats`, `storageMb`, `jobsPerMonth` in
  `onboarding/plans.json`, assigned by `customers/<t>/subscription.json`, alerted
  on by `gateway/quota_alerts.py` (OpenGate);
* the **agent budgets** Paperclip enforces before it starts work — per agent, per
  unit of work (Paperclip).

Neither is wrong. The failure is the gap: an org can hand out agent budgets that
add up to more than the tenant bought, or spend with no budget behind it, and no
single report says so. This contract is that report.

```
plan quota (bought) ──┐
agent budgets (throttle) ──┼──▶ reconcile ──▶ report: findings, never a charge
metered spend (measured) ──┘
```

## What this contract is not

* **Not a second ledger.** D5: the metering store is the truth about spend; the
  statements (#225 area) price it. Reconciliation reads counts and never prices
  anything, never writes an event, never changes a statement.
* **The report is not an enforcement point.** It is periodic and read-only: it
  explains, it does not gate. **The store is**: the run path asks for an
  allowance before it writes a run record and refuses with `E-BUD-08` when an
  enforced budget is exhausted. That is the throttle D5 promises.
  **The plan is still not a block** — a seat wall refuses an account, but
  storage and jobs stay metered-and-alerted (`docs/quota-alerts.md`); a tenant
  past its plan is `E-BUD-07` in the report, not a refused run.
* **Not a scheduler.** Nightly is the intended cadence (D5); the contract does
  not own the clock.

## Inputs

### 1. The plan (bought capacity)

`gateway/plans.limits(root, tenant)` — the assigned plan's three numbers, with
`-1` meaning unlimited. A tenant with no `subscription.json` is a legacy tenant
and is unlimited **by contract**, exactly as the rest of the platform treats it.

The only two dimensions this contract compares are the two that have both a plan
cap and a metered flow:

| Metering kind | Unit | Plan dimension | Conversion |
|---|---|---|---|
| `jobs` | job | `jobsPerMonth` | 1:1 |
| `storage` | byte | `storageMb` | `limit = storageMb × 1 048 576` |

**Every other metered kind** — `documents`, `seats`, `cases`, `exports`,
`api_calls`, `model_calls`, and any kind added to `metering.KINDS` later — is
budgeted per agent and reconciled against that budget, but has **no plan cap and
no quota row**. The plan caps work units and bytes; a document's cost is its
bytes, which `storage` already carries, and inventing a count limit for the rest
would be a number nobody sold. The report says so by their absence from `quota`,
and a tenant can still throttle them per agent — which is where a kind added
tomorrow lands without this contract changing.

### 2. The budget store (the throttle)

`customers/<tenant>/budgets.json`, written by a tenant admin (`budget-store@1`):

```json
{
  "version": 1,
  "tenant": "acme",
  "period": "monthly",
  "agents": [
    {"account": "agent-co", "unit": "finance",
     "budget": {"jobs": 500, "documents": 200, "storage": 104857600},
     "enforced": true},
    {"account": "agent-research", "unit": "research",
     "budget": {"jobs": -1, "documents": 50, "storage": -1},
     "enforced": true}
  ]
}
```

| Field | Rule |
|---|---|
| `version` | `1` |
| `tenant` | equals the directory it sits in |
| `period` | `monthly` or `daily` — the window Paperclip throttles over; the report always reconciles the **calendar month** and says so when the store's window is narrower |
| `agents[].account` | an **active agent** in this tenant's account store; a person cannot hold a budget |
| `agents[].unit` | optional; if present, the agent's unit in the org chart |
| `budget.<kind>` | a key for any kind in `metering.KINDS`; integer ≥ 0, or `-1` for unlimited; a **missing kind is not zero** — it is unbudgeted; an unknown kind is `E-BUD-02` (the store cannot budget what the platform does not meter) |
| `enforced` | whether Paperclip refuses a run past the budget; `false` budgets are recorded but explicitly advisory |

Budgets are a throttle, and a throttle may be **looser** than the purchase only
if the operator says why — hence `E-BUD-05` below. Nothing in this store can
authorise spend; it can only stop it.

### 3. Metered spend (measured)

`gateway/metering.summary(root, tenant, period)` — per kind, the sum of billed
quantities for the period, per company.

Attribution to an **agent** does not come from the event: a metering event names
`source.tool` and `source.ref` (the run), not an account, and adding a second
copy of the account to the event would create a field that can disagree with the
record it describes. The report joins instead — event → `source.ref` → the run
record's `account` — which is the same join #296 already validates, so an
adapter event that cannot be attributed is already `E-EVD-04`. An event with
**no** ref (a pilot, a backfill) lands in `unbudgeted` and is reported, never
guessed into an agent.

`summary()` is used to cross-check the totals (its `byKind` is the contract's
`totals.spent`); per-agent figures come from the join.

## Outputs

One document — `schemas/budget-reconciliation.json`:

```json
{
  "version": 1, "contract": "budget-reconciliation@1",
  "tenant": "acme", "period": "2026-11", "at": "2026-11-01T00:00:00.000Z",
  "plan": {"id": "team",
           "limits": {"seats": 25, "storageMb": 10240, "jobsPerMonth": 2000}},
  "agents": [
    {"account": "agent-co", "unit": "finance",
     "budget": {"jobs": 500, "documents": 200, "storage": 104857600},
     "spent": {"jobs": 120, "documents": 30, "storage": 5242880},
     "state": "within"}
  ],
  "totals": {
    "budget":     {"jobs": 500, "documents": 250, "storage": 104857600},
    "spent":      {"jobs": 820, "documents": 82, "storage": 15728640},
    "unbudgeted": {"jobs": 0, "documents": 0, "storage": 0},
    "unlimited":  {"jobs": ["agent-research"], "documents": [],
                   "storage": ["agent-research"]}
  },
  "quota": [
    {"kind": "jobs", "limit": 2000, "budget": 500, "spent": 820, "state": "within"},
    {"kind": "storage", "limit": 10737418240, "budget": 104857600,
     "spent": 15728640, "state": "within"}
  ],
  "findings": [], "problems": []
}
```

| Field | Meaning |
|---|---|
| `plan` | `null` with **no** `E-BUD-01` means a legacy tenant (no subscription): unlimited, no quota rows, no finding. `null` **with** `E-BUD-01` means a plan was assigned and cannot be found — the ceiling is unknown, and every quota row is absent because unknown is not infinite |
| `agents[]` | one row per agent **with a budget**, plus one per agent with spend and no budget (`budget: null`) |
| `agents[].state` | `within` · `over` · `unbudgeted` · `unlimited`; precedence `over` › `unbudgeted` › `unlimited` › `within` |
| the three maps | carry the kinds that appear in the store or the period, not a fixed list |
| `totals.budget` | the sum of **finite** budgets per kind; unlimited accounts are named in `totals.unlimited`, never added |
| `totals.unbudgeted` | spend with no budget behind it, per kind |
| `quota[]` | one row per comparable kind (never `documents`) |
| `findings[]` | ordered refusals, each with `code`, `severity`, `message`, `fix` |
| `problems` | shape problems in the store, verbatim — a report can be produced from a broken store, but it says so |

## Errors (ordered, fail closed)

| Code | When | Severity | What the operator does |
|---|---|---|---|
| `E-BUD-01` | an **assigned** plan id is not in the registry | critical | fix the subscription, or restore the plan; the ceiling is unknown, not unlimited (a tenant with *no* subscription is legacy and unlimited — no finding) |
| `E-BUD-02` | the budget store is malformed (shape, version, tenant, negative, unknown kind, duplicate account) | critical | fix `customers/<t>/budgets.json`; the report lists each problem |
| `E-BUD-03` | a budget names an account that is not an active agent in this tenant | warning | remove the entry, or make the account an agent |
| `E-BUD-05` | the finite agent budgets **sum above** the plan cap for `jobs` or `storage` | warning | lower the budgets, or buy a plan that covers them — the promise must fit the purchase |
| `E-BUD-04` | an agent has spend and no budget for that kind | warning | add the budget, or accept it explicitly with `enforced: false` |
| `E-BUD-06` | an agent's spend exceeds its finite budget | warning | the throttle did not hold (or `enforced` was false): fix the budget or the runner |
| `E-BUD-07` | total spend exceeds the plan cap | critical | the tenant is past what it bought: upgrade the plan, and check `quota_alerts` history |
| `E-BUD-08` | an **enforced** budget is exhausted when a run asks to start (spent ≥ budget for the period) — the one refusal, raised on the run path, not in the report | critical | raise the budget, record the stop as expected, or move the work to another agent; the run does not start and no artifact is written |
| `E-BUD-09` | a **closed** period already has a report and would be rewritten, or a future period is requested | critical | record the current period; a closed period is corrected by an amendment, not by rewriting its report |

`E-BUD-08` is the only code raised as an exception rather than reported as a
finding: it stops a run. It fires in `paperclip.begin` **after** the pass
verifies and **before** the run record is written, so a stopped run leaves a
`run.refused` line and nothing else. A budget with `enforced: false` is advisory
and never raises it, and a tenant without a budget store is never throttled — the
legacy behaviour, by contract.

The report order is deliberate: can we know the ceiling (`01`), is the store readable
(`02`), is the budget attributable (`03`), does the promise fit the purchase
(`05`), is all spend owned (`04`), did an agent exceed (`06`), did the tenant
exceed (`07`). Shape and identity before arithmetic; capacity before
consumption.

Two rules that are easy to get wrong, stated once:

* **Unknown is not unlimited.** A missing plan or a missing budget is reported,
  never treated as `-1`. `-1` is something an operator wrote on purpose.
* **A budget stop never changes a statement.** Every finding is about throttling
  or truth; none of them can add or remove a charge (D5).

## The arithmetic

For each kind `k`:

```
budget[k]     = Σ budgets of agents where budget[k] ≥ 0        (unlimited excluded)
unlimited[k]  = accounts where budget[k] = -1
spent[k]      = Σ metered quantity for k in the period
unbudgeted[k] = spent of agents with no budget entry for k
```

`state` for an agent and kind: `unlimited` if `budget[k] = -1`; `unbudgeted` if
the budget has no `k`; `over` if `spent[k] > budget[k]`; else `within`.

`quota` row state: `over` if `spent > limit`, else `within`; a `-1` limit means
no row for that kind is emitted (the plan does not cap it).

**Storage is a level, not a flow.** `jobs` and `documents` accumulate through the
month; `storage` is the tenant-directory size at the moment of the report. The
report says so by comparing the **latest** snapshot to the cap, and a storage
change during the month is not an overrun until it crosses the cap.

## Worked example

`tests/fixtures/budget/case.valid.json` — plan `team` (2 000 jobs, 10 240 MB),
two agents, one month of spend. `agent-co` is inside all three budgets;
`agent-research` is unlimited for jobs and storage but budgeted at 50 documents
and spent 52, so the example carries exactly one finding:

```
E-BUD-06  agent-research: documents 52 > 50 — the throttle did not hold
```

`scripts/check_budget_spec.py` recomputes the report from the case's inputs and
fails if the committed report differs, so the example is not prose: it is
executed. `--self-test` then mutates the inputs seven ways (an unknown plan, a
malformed store, a budget on a person, an overcommitted plan, unbudgeted spend,
an overrun, a tenant past its cap) and asserts each expected code appears.

## The record

A reconciliation is recorded per run, in two halves
(`customers/<tenant>/budget-reports/`):

| Piece | Rule |
|---|---|
| `<YYYY-MM>.json` | the period's snapshot; the **open** period may be re-recorded as spend changes, a **closed** one may not (`E-BUD-09`) |
| `budget-reports.jsonl` | one append-only row per recording run — `at`, `period`, `digest`, `findings`, `agents`, `written` |

The digest is over the report's content, not its `at`: two recordings of the same
facts digest the same and the second is a silent no-op, so "per run" never turns
into "per duplicate". `--sync` validates both halves — the file name is the
period, the document agrees with it, and a finding carries a report code (the two
raised codes never appear in a report).

## The operator surface

`infra/budget.py` in the tenant repo: `status` (plan, agents, quota rows and
findings on one screen, `--fail-on-findings` for cron), `report` (the document,
or the recorded snapshot with `--recorded`), `record` (write the period), and
`history` (the runs). All four are admin-only, and the refusal names *budgets*
rather than identity. `check` takes no actor: it validates the store and the
recorded reports, which is the same read `--sync` makes.

## Hardening

The implementation's edges, each with a code and a fix (#309):

| Failure mode | Refusal |
|---|---|
| the tenant is a path (`..`, a separator, absolute, empty, a newline) | `E-BUD-02 invalid tenant`, checked before the admin lookup |
| the period is not `YYYY-MM` | `E-BUD-02 … not YYYY-MM` — a period is a file name |
| the store, the log or a recorded report is a symbolic link | `E-BUD-02 … a symbolic link to '<target>'`, and the target is never written |
| a second writer holds the tenant's lock | `E-BUD-02 … the store is busy … (budgets.lock)`, which expires after 300 s if the holder crashed |
| a candidate document the validator would reject | `E-BUD-02 refusing to write — …`, and the store that was there survives |

One write primitive validates every replacement, so no caller — including the
CLI — can slip an invalid store past the validator; the log is opened
`O_NOFOLLOW` and appended with a single `write(2)`. **Not defended:** a process
already inside the tenant can rewrite the store wholesale; the recorded report's
digest is what makes that visible afterwards.

## The measurement

`gateway/budget_metrics.py` in the tenant repo evaluates six rules per period
(#310): B1 overcommit, B2 unbudgeted, B3 overrun, B4 tenant-over, B5 stop-spike
and B6 record-integrity. B1–B4 restate the report's findings for a channel;
**B5 measures what no report can carry** — a budget stop is an event (`E-BUD-08`
on a `run.refused` line), not spend, so "this agent keeps being stopped" is only
visible by counting audit lines in a window. Alerts are one line per rule per day
in `customers/<t>/budget-alerts.jsonl`; `--sync` validates the store, and
`drill` proves every rule fires while a clean tenant stays quiet.

## The runbook

`abn.platform.opengate/docs/budget-walkthrough.md` is the generated, end-to-end
transcript (#308): a tenant with no throttle, a seeded budget, two real runs, the
measure firing, the cron exit code, a recording and a silent re-recording, the
history, the throttle refusing a third run (`E-BUD-08`), an overcommit the plan
cannot afford (`E-BUD-05`), the non-admin refusal, and `check`. It is generated
by `infra/budget_walkthrough.py`; `--check` regenerates and diffs it, so a stale
transcript fails the suite.

## The conformance matrix

The implementation's matrix is `abn.platform.opengate/tests/test_budget_matrix.py`
(#305): 44 cases, each asserting which code fires **and why** — a negative test
that accepts the wrong reason hides the regression it was meant to catch. It
covers a clean and a legacy tenant; an assigned plan that does not exist and a
subscription without a plan id; ten malformed stores, each refused as `E-BUD-02`
for its own reason; budgets on a person, a disabled agent and an unknown account
(`E-BUD-03`); unbudgeted spend, spend whose run record is gone and spend from
another tool (`E-BUD-04`, naming `unattributed` when that is the truth);
overcommit on jobs and on storage (through the MB conversion) and two agents
whose budgets are each within but sum above (`E-BUD-05`); overruns past a budget
and *not* at it (`E-BUD-06`); the tenant past its plan and *not* at it
(`E-BUD-07`); an unlimited budget that is excluded from the sum yet does not
suppress the tenant cap; spend from another month; nine allowance cases; and the
exhausted run that is refused, leaves no record and writes one `run.refused`.
A final case asserts the matrix covers every code in `SEVERITY`.

## Where it will live

| Piece | Path (planned) |
|---|---|
| the store | `customers/<tenant>/budgets.json` |
| the arithmetic (and the event → run → account join) | `gateway/budget.py` (#303) |
| the surface | `infra/budget.py` — `status`, `report`, `record`, `history`, `check` (#307) |
| the gate | `--sync` validates the store and the report's shape (#304) |
| the measure | `gateway/budget_metrics.py` — overcommit, unbudgeted spend, overruns (#307) |

## Not in this contract

* Prices, invoices, proration, dunning — the statements own them.
* Per-task or per-document budgets — the unit is the agent and the month.
* Retroactive budgets: a budget applies to the period it names, and a past period
  is reconciled with the budget that was in force then (the store keeps a
  `period` history in later steps, never rewritten).
