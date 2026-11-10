# Threat model v2.0 (issue #462) — the OS, and the agents that act in it

Scope: router, process engine, human-task inbox, Axum gateway, audit store,
event bus, **and the agent surfaces — prompt injection, agent credentials,
cross-tenant** (v2.0, added by the security workstream). Out of scope:
core-banking internals (trusted via adapters, H75), client device security.
Review quarterly or after any Sev1.

**v1.0 (issue #9)** covered the OS itself. **v2.0** adds the three surfaces an agent
brings, because an agent is the one component that reads untrusted text and then *acts*:
the v1.0 table assumed a step whose inputs were structured, and a step that reads a
customer document does not have that.

The register is machine-readable: `tests/fixtures/security/threat-register.json`, the
schema `schemas/threat-register.json`, and `scripts/check_threat_model_spec.py` is the
gate. Every `A` row below must exist in both, and the check says so when they drift.

## The OS itself (v1.0, issue #9)

## STRIDE table

| # | Component | Threat (STRIDE) | Scenario | Mitigation | Status |
|---|---|---|---|---|---|
| T1 | Gateway | **S**poofing | stolen session acts as RM, approves loans | short-lived scoped JWTs (F54), step-up auth for approvals | planned F54 |
| T2 | Gateway | **D**enial | loan-spike / bot flood starves engine | rate limits per client_key, queue + backpressure, F60 load SLO | planned F60 |
| T3 | Router | **T**ampering | attacker edits routing table → transfers skip sanctions | routing table versioned via E46 pipeline, 4-eyes deploy, change alerts | spec A04/E46 |
| T4 | Router | **R**epudiation | "I never approved that" | every route decision in audit chain (A05) with actor + versions | done A05 |
| T5 | Engine | **T**ampering | replayed event re-fires payout | idempotency keys + processed-keys store (A07) | done A07 |
| T6 | Engine | **D**enial | poison event loops retries, stalls partitions | 5-attempt cap → DLQ (A04), per-step timeouts (F58) | spec A04 |
| T7 | Engine | **E**levation | workflow step calls admin API beyond its role | OpenFGA per-step service identity, least privilege (B17) | planned B17 |
| T8 | Inbox | **S**poofing / **E**levation | delegation abused to self-approve (SoD break) | SoD pairs enforced in inbox, delegation expiry + re-cert (B19) | planned B19 |
| T9 | Inbox | **R**epudiation | approver denies clicking approve | signed approval records in audit chain | planned F53 |
| T10 | AI steps | **T**ampering | prompt injection in complaint text flips triage | input sandboxing, schema-validated outputs, abstain→REVIEW (G68) | planned G68 |
| T11 | AI steps | **I**nfo disclosure | PII leaks into model logs/prompts | PII-masking rule (A05): hashes only in chain, egress filters (G70) | done A05 |
| T12 | Audit store | **T**ampering | insider rewrites decision history | hash chain + sealed append-only store, verify job nightly (A05) | done A05 |
| T13 | Audit store | **I**nfo disclosure | auditor bulk-exports PII | time-boxed grants, no standing access, masked UI (A05) | done A05 |
| T14 | Event bus | **I**nfo disclosure | eavesdrop on customer payloads | mTLS in transit, encryption at rest, PII tiering (D33) | planned D33 |
| T15 | Event bus | **D**enial | consumer lag hides fraud holds | lag SLO + paging, holds fail-closed on timeout (H75) | planned H75 |

## Top-5 risks (owners)

1. **Double-posting money on redelivery** — owner: Payments lead. Controls: A07 keys + monthly money drill. (T5)
2. **Routing table tamper skipping sanctions** — owner: Risk + Platform. Controls: E46 pipeline, change alerts. (T3)
3. **SoD breach via delegation (self-approval)** — owner: Compliance. Controls: B19 pairs, quarterly SoD mining (I88). (T8)
4. **PII in AI surface (prompts/logs)** — owner: Data Protection. Controls: A05 masking, G70 red-team. (T11)
5. **Audit history rewrite by insider** — owner: InfoSec. Controls: hash chain, nightly verify, sealed store. (T12)

## Agent surfaces (v2.0, issue #462)

Three surfaces, and the columns are the register's own: **control** is what stops it,
**evidence** is where that control (or its proof) lives, and **status** is what the gate
reads. A row is `mitigated` only when the evidence path exists; `planned` names the issue
that builds it; `accepted` needs a signature in the register's `accepted` list; and `open`
— no control at all — **fails the gate**.

| # | Surface | STRIDE | Scenario | Control | Evidence | Status |
|---|---|---|---|---|---|---|
| A1 | prompt-injection | T | A customer document tells the agent to ignore its task and release a memo it was asked to review | The instruction never reaches the model as authority: the task arrives in the pass, the document is data, and the output is schema-validated before anything acts on it | — | planned #464 |
| A2 | prompt-injection | T | A tool result (a page, a file, an API error) carries instructions that the model follows | Tool output is untrusted data with a declared shape; an instruction-shaped result is flagged and the step returns REVIEW rather than acting | — | planned #465 |
| A3 | prompt-injection | E | Multi-turn pressure walks an agent from its task to an action its pass does not allow | Every action is checked against the pass at the tool boundary, not in the prompt — the conversation is not an authorisation surface | `docs/core/ai-contract.md` | mitigated |
| A4 | prompt-injection | R | An injected instruction is followed and the run looks like an ordinary one | The attempt is recorded: the prompt, the tool calls and the refusal are evidence in the run record, and a flagged injection is an alert | — | planned #466 |
| A5 | agent-credentials | S | A stolen agent credential is used to begin runs as that agent | No long-lived agent credential exists: the pass is short-lived, bound to task and run, and signed; a stolen one is expired or bound elsewhere | `docs/core/ai-contract.md` | mitigated |
| A6 | agent-credentials | I | A secret reaches a model prompt, a log or an artifact | Secrets resolve at run time from references; the record keeps names and references, never values, and the redactor reports counts only | `schemas/secret-ref.json` | mitigated |
| A7 | agent-credentials | E | An agent keeps acting after its run closed, using a pass that still verifies | A closed run cannot be resumed and the pass carries an expiry; a stale pass is a refusal, not a second run | `docs/core/ai-contract.md` | mitigated |
| A8 | agent-credentials | R | An action is taken with an agent's identity and the agent's owner denies it | Every agent action names the agent and its owner in the chain, so a denial is checkable rather than arguable | `schemas/tenant-identity.json` | mitigated |
| A9 | cross-tenant | I | A retrieval or a tool call returns another tenant's document to this tenant's agent | Every read is scoped by tenant at the store, and a tool call carries the tenant in the pass — a foreign path is refused at the boundary | `docs/core/confidentiality.md` | planned #468 |
| A10 | cross-tenant | I | An agent's output quotes an id or a fact belonging to another tenant | The egress filter blocks foreign instance ids and routes them to REVIEW before a human or a system sees them | `docs/core/redteam.md` | planned #469 |
| A11 | cross-tenant | E | A connector credential provisioned for one tenant is used to reach another | Connector tokens are per tenant and per connector, and the connector contract refuses a token that names another tenant | — | planned #470 |
| A12 | cross-tenant | D | One tenant's load (or a retry storm) starves another's runs | Budgets and the retry budget are per tenant and per agent; a queue row belongs to one tenant and cannot be replayed into another | `docs/core/threat-model.md` | mitigated |

### Why these three, and not more

An agent is the only component that **reads text it did not choose and then acts**. The
three surfaces are that sentence read carefully: what it reads (prompt injection), what it
acts **as** (agent credentials), and whose data it acts **on** (cross-tenant). Anything
else — a compromised host, a bad deploy — is the v1.0 table's job.

## The gate's interface (what the implementation must satisfy)

| | |
|---|---|
| **Input** | the register (`tests/fixtures/security/threat-register.json`), and the repository it points into |
| **Output** | a verdict: `ok`, the findings with a code each, and the **blocking** subset — a row with no control |
| **Errors** | `E-TM-01`…`E-TM-11`, each naming its fix; an `open` row is the only one that blocks on its own |
| **Side effects** | none: the gate reads the register and the tree, and prints |

```bash
python scripts/check_threat_model_spec.py                 # the committed register
python scripts/check_threat_model_spec.py some.json --json
python scripts/check_threat_model_spec.py --self-test     # every code fires
```

Exit `0` green, `1` findings, `2` the arguments were wrong.

## Errors

| Code | When | What the operator does |
|---|---|---|
| `E-TM-01` | the register is not an object, or cannot be read | point the check at a register, or write one |
| `E-TM-02` | `version` is not 2 | a register is version 2; an old one is migrated, not read |
| `E-TM-03` | a row is not an object, or is missing a required field | every row names id, surface, stride, scenario, control, status and owner |
| `E-TM-04` | two rows share an id | an id is a name; two rows with one id make every reference ambiguous |
| `E-TM-05` | a `stride` letter that is not S, T, R, I, D or E | pick one letter — the class is what a reviewer argues about |
| `E-TM-06` | a `status` outside mitigated / planned / accepted / open, or `planned` with no issue | say which of the four states the control is in, and name the issue for a planned one |
| `E-TM-07` | a surface with no row | add its rows, or say in the review why it has none |
| `E-TM-08` | `evidence.path` that does not exist | point at a file that exists, or leave it null and mark the row planned |
| `E-TM-09` | `accepted` with no justification | say who accepted it and why |
| `E-TM-10` | a row the document does not print | print it: the register is the table's machine form |
| `E-TM-11` | an `open` row — a threat with no control | give it a control, accept it with a reason, or plan it against an issue |

## Review

Quarterly, or after any Sev1. The review is `python scripts/check_threat_model_spec.py`
**and** a human answer to one question: *did anything here stop being true?* The gate can
see a missing file and a missing row; it cannot see that a control no longer does what its
sentence says. `docs/core/redteam.md` is the empirical half: the same three surfaces, as
suites that must hold.
