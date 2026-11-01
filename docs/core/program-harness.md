# Program harness — a fake Paperclip, a fake tenant, and the contracts between them (contract `program-harness@1`)

**Status:** interface specified (#332), implemented in
`abn.platform.opengate/gateway/harness.py` (#333) and run as
`abn.platform.opengate/infra/harness.py` (#334); the record, surface, harden,
measure and demo steps follow (#335–#341). **Shape:** `schemas/harness-run.json`. **Checker:**
`scripts/check_harness_spec.py` (CI, `--self-test`). **Boundary:** ADR-002 — the
three planes meet nowhere else.

Every workstream so far proved one seam with a real executor on one side. The
program's claim is that the **whole** chain holds: a company compiled here, run
as Paperclip would run it, against a tenant that OpenGate would accept, with the
decision, the evidence and the money all landing where the contracts say. The
harness is the only place those two meet, and it meets them as **fixtures** — a
fake Paperclip and a fake tenant — so the claim is testable without either
production system.

```
fake-paperclip ──scripted run──▶ platform APIs ──▶ fake-tenant
 (template + steps)              (the contracts)     (accounts, grid, budgets)
                                        │
                                        ▼
                                   run record: every assertion, its code, the verdict
```

## What this contract is not

* **Not a second implementation of any plane.** The harness calls each plane's own
  validators and refuses nothing they accept; if it ever disagreed with `--sync`,
  the harness would be wrong.
* **Not an integration environment.** No network, no provider, no clock beyond the
  fixtures — a run is a directory tree and a script.
* **Not a demo.** The demo is a transcript of the harness; this is what the
  transcript is a recording of.

## Inputs

### 1. The fake tenant

A tenant tree the platform accepts: `customers/<t>/accounts.json`, `org.json`,
`authority.json`, `budgets.json`, `instructions.md` — built by the platform's own
provisioner, not by hand, so a harness fixture cannot drift into a shape the
product rejects.

### 2. The fake Paperclip

A compiled company template (from this repository) plus a **script** of steps:

```json
{"id": "S1", "actor": "agent-co", "action": "read",
 "target": "finance/report.docx", "expect": "allowed"}
{"id": "S2", "actor": "agent-co", "action": "approve", "request": "REQ-1",
 "amount": 800000000, "expect": "refused", "code": "E-GOV-04"}
```

`action` is one of `read`, `write`, `begin`, `finish`, `refuse`, `approve`,
`reconcile`, `offboard`. `expect` is `allowed` or `refused` with the `code` the
platform must give — the harness asserts the **reason**, not only the outcome.

### 3. The pins

Both fixtures are built for one contract pin (`contract-YYYY.MM.N`). A pair built
for two different pins is refused: a harness that mixes eras proves nothing about
either.

## Outputs

One run record — `schemas/harness-run.json`:

```json
{
  "version": 1, "contract": "program-harness@1",
  "runId": "hrn-5c2e1b7a94f0d638",
  "at": "2026-11-01T09:00:00.000Z",
  "pin": {"tag": "contract-2026.11.1", "sha": "a7baab40…"},
  "fixtures": [
    {"id": "fake-tenant", "sha256": "…"},
    {"id": "fake-paperclip", "sha256": "…"}
  ],
  "assertions": [
    {"step": "S1", "expect": "allowed", "observed": "allowed", "ok": true},
    {"step": "S2", "expect": "refused", "code": "E-GOV-04",
     "observed": "refused", "observedCode": "E-GOV-04", "ok": true}
  ],
  "dirty": [],
  "verdict": "pass"
}
```

| Field | Meaning |
|---|---|
| `runId` | `hrn-` + `sha256(pin \| each fixture digest \| each assertion)` — content-addressed, so two runs of the same fixtures and the same behaviour are the same run |
| `repeatRunId` | what an immediate second run produced; it must equal `runId`, which is the only way a *record* can show its own repeatability |
| `fixtures[].sha256` | the digest of the fixture tree at the moment of the run: a silent edit to a fixture changes the run id |
| `assertions[]` | one per scripted step: what was expected, what happened, and whether the **reason** matched |
| `dirty` | paths that differ from the fixture's **baseline** (captured when it was built) and that the script did not declare — an edit *between* runs is dirt too |
| `verdict` | `pass` only when every assertion is `ok` and `dirty` is empty |

## Errors (ordered, fail closed)

| Code | When | What the operator does |
|---|---|---|
| `E-HRN-01` | a fixture is missing, or its digest does not match the one the run claims | re-provision the fixture; a run against an edited fixture proves nothing |
| `E-HRN-02` | a step's outcome differs from its `expect` | read the step: the contract changed, or the fixture is stale |
| `E-HRN-03` | a step's **code** differs from the expected `code` (refused for the wrong reason) | the refusal fired for another rule — fix the fixture or the contract's checker |
| `E-HRN-04` | the run left the tenant dirty | the harness must not mutate what it measures; add the change to the script or stop writing |
| `E-HRN-05` | the two fixtures were built for different contract pins | rebuild one of them; a mixed pair proves nothing |
| `E-HRN-06` | a scripted step has no assertion, or an assertion has no step | the record must account for **every** step |
| `E-HRN-07` | the record's `repeatRunId` — the id an immediate second run produced — differs from `runId` | non-determinism: a clock, a path, or an unsorted set leaked into a fixture |

The order is the graph: is the fixture real (`01`) → did it behave (`02`) → for
the **right reason** (`03`) → did it leave a mess (`04`) → is the pair coherent
(`05`) → is every step accounted for (`06`) → is the run repeatable (`07`).

`E-HRN-07` is why the record carries a second id rather than a timestamp: a run cannot prove its own determinism, so the runner performs the run twice and the record says so.

`E-HRN-03` is the one worth the space: a refused step that was refused for a
different rule than the contract says is a **passing test of the wrong thing**,
which is how a harness rots. Every other code catches a failure; that one catches
a false success.

## The arithmetic

```
assertion.ok   = observed == expect and (expect == allowed or observedCode == code)
verdict        = "pass" if all ok and not dirty else "fail"
runId          = "hrn-" + sha256(pin.tag | fixture digests | assertion lines)
```

## A worked example

`tests/fixtures/harness/run.valid.json` — tenant `acme`, a pair pinned at
`contract-2026.11.1`, six steps (a permitted read, a `mật` read refused for the
right code, a finish that meters, an approval the requester may not sign, a
reconciliation that reports the overcommit, and an offboarding that needs a second
signature): every assertion `ok`, `dirty` empty, verdict `pass`. The self-test then
mutates it seven ways — a drifted fixture, a wrong outcome, a right outcome for the
wrong code, a dirty tree, a mixed pin pair, a step with no assertion, a run that is
not repeatable — and asserts each code fires.

## Where it will live

| Piece | Path (planned) |
|---|---|
| the fake tenant | built at run time by the platform's own provisioner, never checked in (#333) |
| the fake Paperclip | `scripts/fake_paperclip.py` — a script runner over the real surfaces (#334) |
| the runner | `abn.platform.opengate/gateway/harness.py` — `build`, `run`, `record`, `verify` (#333) |
| the command | `abn.platform.opengate/infra/harness.py` — `run` (exit 1 on a failed verdict), `verify` (#334) |
| the record | `harness/runs/<runId>.json`, committed per release (#336) |
| the measure | `scripts/harness_metrics.py` — assertions per contract, coverage per plane (#338) |

## Not in this contract

* Performance or load — that is `docs/core/loadtest.md`, and it needs a real
  deployment.
* Provider fakes (ONEID, S3) — the harvest of the planes happens above them.
* A second demo: the demo is `docs/core/program-walkthrough.md`, generated from a
  harness run (#341).
