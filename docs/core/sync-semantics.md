# Sync semantics: one-way, no dual writes (`sync-semantics@1`)

**Status: enforced (#486) — `sync-semantics@1`.**
[ADR-003](adr-003-sync-semantics.md) is the decision; this page is the contract it ratifies.
Review is closed — eight findings, six resolved here and two deferred with an owner
([the record](paperclip-reviews/PC2-25-02-field-ownership.md)); **both deferred findings are
closed by the enforcement step** (see *Enforcement*). The seam that refuses a second writer
lives in `abn.platform.opengate` (`gateway/sync_semantics.py`), and its operator page is that
repository's `docs/sync-semantics.md`.

**What it settles:** who owns which field, and where a re-run resumes.

Three planes already share one company. Enterprise OS compiles a model, Paperclip runs the
agents, OpenGate holds the tenant and the evidence — and the boundary contract
([paperclip-integration.md](paperclip-integration.md)) says **one-way compile** (D1) and
**one owner per row** in its ownership matrix. What it does not say is what happens at the
granularity an implementation actually writes at: *this* field, *this* process. So two
questions stay open, and both are answered wrongly by default:

- **Who may write `label`?** Two writers to one field do not conflict — they take turns, and
  the last one wins silently. Nobody finds out until somebody reads a stale name in an audit.
- **Where does a re-run resume?** Without a cursor, a sync either re-applies every record or
  skips the ones it thinks it already did. The first is slow, the second is a silent loss.

This contract is the answer to both, and it is deliberately dull: **one writer per field, one
direction per stream, and a watermark that is the only resume point.**

## The decision

> **D-S1 — One writer per field.** Every field that crosses a plane boundary names exactly
> one **owning plane**. A write from any other plane is a **proposal**, and a proposal is
> refused at the seam — not merged, not queued, not reconciled nightly.
>
> **D-S2 — One direction per stream.** Fields live in **streams**, and a stream has exactly
> one **producer**. The consumers receive a copy. A mirror may store a field and may never
> author one; a stream with two producers is the dual write this contract exists to forbid.
>
> **D-S3 — The watermark is the only resume point.** Every record carries a **strictly
> increasing** sequence number in its stream. A consumer stores the last value it applied
> per `(stream, tenant)`, applies only records above it, and treats a record at or below it
> as **already applied** — a no-op, not an error. A gap is a request for the missing range,
> never a skip.

Three clauses, and each has one failure it prevents: a field with two writers, a stream that
flows both ways, and a re-run that cannot tell what it has already done.

## The planes

| Plane | Owns | Never |
|---|---|---|
| **enterprise** (this repo) | the model: org, roles, processes, rules, packs, the company, the contract pin | work state, tenant data, evidence, secrets |
| **paperclip** | work: tickets, comments, run logs, the approvals inbox, budgets as a throttle | the model, the tenant, the record, the ledger |
| **opengate** | the tenant: identity, companies, folders and ACL, `dataMode`, records, metering, the audit chain | the model, work state, secret values |
| **vault** | secret values | anything else it is handed |

Four planes, and every field below names exactly one of them. A field naming anything else
is `E-SYN-05`; a plane whose write nobody accounted for is `E-SYN-06`.

## The streams

One producer each. The watermark is the field that carries the sequence number — it is a
counter, not a clock.

| Stream | Producer | Watermark | Carries |
|---|---|---|---|
| `model` | enterprise | `model.seq` | the company model this repository compiles |
| `tenant` | opengate | `tenant.seq` | the tenant profile, its companies, folders, ACL, `dataMode` |
| `identity` | opengate | `identity.seq` | ONEID accounts and the seats they hold in Paperclip |
| `work` | paperclip | `work.seq` | tickets, comments, run logs, the approvals inbox — ephemeral by D2 |
| `evidence` | opengate | `evidence.seq` | cases, documents and artifacts of record |
| `money` | opengate | `money.seq` | plans, quotas, statements, metered spend — billing truth by D5 |
| `audit` | opengate | `audit.seq` | the signed audit chain |
| `secret-ref` | opengate | `secret-ref.seq` | the name of a secret and where it lives |
| `secret-value` | vault | `secret-value.seq` | the value, injected at heartbeat and never stored by a consumer |

`secret-ref` and `secret-value` are **two streams, not one**, and that is the whole of D7 in
this contract: the name is OpenGate's, the value is the vault's, and no field is owned by
both. A single `secret` stream would have needed two producers — the smallest possible
example of why D-S2 is a structural rule and not a convention.

## The fields

Every field that crosses a boundary. `mirrored to` = the planes that receive a copy; **every
other plane, mirrors included, may never originate a write** (`neverWrittenBy` in the
register — storing a copy is not writing one).

`sensitivity` is the **data** tier from
[confidentiality.md](confidentiality.md) — `PII-strict`, `confidential`, `internal`,
`public` — **not** the industry tier: `restricted` and `classified` describe an industry's
content, and a field labelled with the wrong axis reads as stricter while enforcing nothing
(review F2, #483). The checker compares the register's list with `metamodel/event.schema.yaml`
(`pii_class`), so a fifth level cannot appear on one side only.

### `model` — the company model (enterprise)

| Field | Owner | Mirrored to | Sensitivity |
|---|---|---|---|
| `model.version` | enterprise | paperclip | internal |
| `model.id` | enterprise | paperclip | internal |
| `model.label` | enterprise | paperclip | internal |
| `model.tenant` | enterprise | opengate | internal |
| `model.entity` | enterprise | paperclip | confidential |
| `model.industry` | enterprise | paperclip | internal |
| `model.contract` | enterprise | paperclip | internal |
| `model.departments` | enterprise | paperclip | internal |
| `model.org` | enterprise | paperclip | internal |
| `model.flows` | enterprise | paperclip | internal |
| `model.rules` | enterprise | paperclip | internal |
| `model.packs` | enterprise | paperclip | internal |
| `model.docs` | enterprise | — | internal |
| `model.paperclip` | enterprise | paperclip | internal |

`model.tenant` is a **pointer**, not the tenant: the tenant's own fields are OpenGate's, and
compiling the model copies the pointer so a template can say which tenant it is for. Writing
the tenant itself from the model plane would be the first dual write in the system.

### `tenant` and `identity` — the tenant boundary (opengate)

| Field | Owner | Mirrored to | Sensitivity |
|---|---|---|---|
| `tenant.profile` | opengate | paperclip | internal |
| `tenant.companies` | opengate | paperclip | internal |
| `tenant.folders` | opengate | paperclip | internal |
| `tenant.acl` | opengate | — | confidential |
| `tenant.dataMode` | opengate | paperclip | confidential |
| `identity.accounts` | opengate | paperclip | confidential |
| `identity.roleAssignments` | opengate | paperclip | internal |
| `identity.seats` | opengate | paperclip | internal |

`tenant.acl` is mirrored to **nobody**: the ACL is enforced where the data lives (D3), and a
copy of it in another plane is a second policy to keep in step. It is in this registry because
a field that crosses a boundary and a field that must not are the same question asked twice.

### `work` — the ephemeral half (paperclip)

| Field | Owner | Mirrored to | Sensitivity |
|---|---|---|---|
| `work.tickets` | paperclip | opengate | internal |
| `work.comments` | paperclip | opengate | internal |
| `work.runLogs` | paperclip | opengate | internal |
| `work.approvalsUi` | paperclip | opengate | internal |

`work.approvalsUi` is the inbox, not the decision: Paperclip owns the surface a person clicks
in, and OpenGate records what the click decided (D6). The field is Paperclip's; the outcome
is not.

### `evidence`, `money`, `audit` — the durable half (opengate)

| Field | Owner | Mirrored to | Sensitivity |
|---|---|---|---|
| `evidence.cases` | opengate | paperclip | confidential |
| `evidence.documents` | opengate | paperclip | confidential |
| `evidence.approvals` | opengate | paperclip | confidential |
| `evidence.artifacts` | opengate | paperclip | confidential |
| `money.plans` | opengate | paperclip | internal |
| `money.quotas` | opengate | paperclip | internal |
| `money.statements` | opengate | — | confidential |
| `money.metering` | opengate | paperclip | internal |
| `audit.chain` | opengate | — | confidential |

### `secret-ref` and `secret-value` — the two streams of D7

| Field | Owner | Mirrored to | Sensitivity |
|---|---|---|---|
| `secret-ref.ref` | opengate | paperclip | confidential |
| `secret-value.value` | vault | — | PII-strict |

`secret-value.value` takes the **top data tier** even though a credential is not personal
data: the taxonomy has four levels, and a value that must never be at rest sits above a name.
The label is about handling, not about the kind of data.

It is also the register's one **projection**: `"projection": "run env"`. The run environment is a
destination, not a store — the value is injected at heartbeat, nothing is at rest there, and
there is no copy to reconcile. That is why `mirrored to` is empty and the row still says where
the value goes: the boundary matrix's `run env` column had no way to be expressed until review
F7 (#483) asked for it.

### The watermark fields

Each stream's watermark is a field, and a field needs an owner (review F1, #483). Without
these rows the contract's own resume point would be the one value nobody said who may write.

| Field | Owner | Mirrored to | Sensitivity |
|---|---|---|---|
| `model.seq` | enterprise | paperclip, opengate | internal |
| `tenant.seq` | opengate | paperclip | internal |
| `identity.seq` | opengate | paperclip | internal |
| `work.seq` | paperclip | opengate | internal |
| `evidence.seq` | opengate | paperclip | internal |
| `money.seq` | opengate | paperclip | internal |
| `audit.seq` | opengate | — | internal |
| `secret-ref.seq` | opengate | paperclip | internal |
| `secret-value.seq` | vault | — | internal |

A watermark is **mirrored wherever its stream's fields are** — a consumer that stores the
stream stores the position it has applied. `audit.seq` and `secret-value.seq` are mirrored to
nobody because their streams are: an applied watermark is bookkeeping, not evidence.

## Refusals

One code per rule, each with the fix in the same line — the shape the rest of the program
uses.

| Code | Means | Fix |
|---|---|---|
| `E-SYN-01` | the registry is not an object, or cannot be read | point the check at a registry, or write one: `{version: 1, planes, streams, fields}` |
| `E-SYN-02` | `version` is not 1 | a registry is version 1 (`sync-semantics@1`); an old one is migrated, not read |
| `E-SYN-03` | a field is missing a required key, or is missing its owner | name the field's id, stream, owner, mirrors, the planes that may not write it, and its sensitivity |
| `E-SYN-04` | two fields share an id | an id is a name: two rows with one id make every reference ambiguous |
| `E-SYN-05` | a plane is not one of the four, or one of the four is missing from the list | the planes are enterprise, paperclip, opengate, vault — all four, no others |
| `E-SYN-06` | a field does not have exactly one writer — a plane is left off `neverWrittenBy`, or the owner is listed as its own mirror | every plane except the owner may never originate a write; say so, or the writer nobody granted is the one to blame |
| `E-SYN-07` | a field names a stream that is not declared, a stream has no fields, or two streams share an id | a field belongs to a declared stream, and a stream that carries nothing is a name with no meaning |
| `E-SYN-08` | a stream is not `one-way`, or a field's owner is not its stream's producer | one producer per stream — a second owner in one stream is the dual write this contract forbids |
| `E-SYN-09` | a field the document does not print | print the row: the register is the document's machine form, and a field nobody can read about is a field nobody follows |
| `E-SYN-10` | a stream with no watermark, a watermark that is not monotonic, a replay that is not a no-op, or a watermark that is not a **declared field owned by the stream's producer** | a watermark is a field: give it a row owned by the producer, strictly increasing, with a replay treated as already applied |
| `E-SYN-11` | a field of the company model with no ownership row — in the schema, or in a real company | add the row: a model field nobody owns is a field two planes will eventually write |
| `E-SYN-12` | an ownership row for a `model.*` field the company schema does not have | delete the row, or add the field to `companies/company.schema.yaml` — the registry tracks the schema, not the other way round |
| `E-SYN-13` | the document prints a field the register does not declare | delete the document row: a field the register does not declare is a field with no owner, printed as though it had one |
| `E-SYN-14` | a sensitivity outside the four data tiers, or a register whose tiers disagree with the metamodel | use the data tier from `confidentiality.md`; `restricted` and `classified` are the industry axis, not this one |
| `E-SYN-15` | the ADR that ratifies this contract is missing, is not marked `ACCEPTED`, ratifies another version, or the program doc neither links it nor lists the contract among the ratified | record the decision: an ADR that ratifies `sync-semantics@1`, marked ACCEPTED, linked from and listed in `docs/core/paperclip-program.md` |

| `E-SYN-16` | a field declares a `projection` that is a plane, or is projected *and* mirrored | a projection is not a store: name a destination that is not a plane and mirror the field to nobody, or make it a mirror and give it a consumer |

## The watermark

A watermark is a **position in a stream**, not a time. The rule, in the order an
implementation applies it:

1. **The producer stamps** `seq` when it writes a record, strictly greater than the last one
   in that stream for that tenant. It is a counter; two records never share it.
2. **The consumer stores** the last `seq` it applied, per `(stream, tenant)`, durably and in
   the same transaction as the change it applied. A watermark that moves before the write
   lands is the resume point of a lost record.
3. **A record above the watermark** is applied, and the watermark moves to it.
4. **A record at or below it** is **already applied**: the consumer no-ops and says so. Replay
   is normal — a retry, a restored consumer, a re-delivery — and is never an error.
5. **A gap** (a record at `seq + 2` when the watermark is at `seq`) is a **request for the
   missing range**, never a skip. Skipping is how a sync loses a record and reports success.

Two consequences worth naming, because both are tempting shortcuts:

- **A wall clock is not a watermark.** It goes backwards when a host's time is corrected, and
  two records in one millisecond tie. Either failure silently drops a record.
- **A global watermark is not a watermark.** Tenants advance at different rates; one cursor
  across all of them means a busy tenant pins every quiet one, or a quiet one makes a busy one
  skip.

## Enforcement (#486)

The rule is enforced at the seam, in `abn.platform.opengate` —
`gateway/sync_semantics.py`, `infra/sync.py`, and the tenant gate in `resolve.py --sync`.
Its operator page is the platform repo's `docs/sync-semantics.md`.

**The register ships as a copy with a digest.** `onboarding/field-ownership.json` is a byte copy
of `tests/fixtures/sync/field-ownership.json`, and `onboarding/field-ownership.meta.json` carries
its `sha256` and the commit it came from. The runtime verifies the digest before it uses a single
row: a register that was copied half-way, edited in place or belongs to another contract is
**refused** (`E-SYN-23`), never enforced slightly differently. A rule read from a document nobody
vouched for is worse than no rule, because it looks like one.

| Code | Means |
|---|---|
| `E-SYN-20` | a write from a plane that does not own the field — the write is a **proposal**, refused |
| `E-SYN-21` | a gap (`seq > watermark + 1`), or a watermark moved backwards |
| `E-SYN-22` | the watermark could not be read or recorded, so nothing was applied |
| `E-SYN-23` | the register is not the contract's own copy, or the field has no owner |

**A replay is an answer, not an error.** `apply()` returns `{"applied": false, "reason":
"already"}` for a record at or below the watermark, and the CLI exits `0`. A retry, a restored
consumer and a re-delivery are normal events; making one an error teaches an operator to ignore
the error that matters.

**The order is the contract's:** ownership → position → the write → the watermark. `write()` runs
before the position moves, so a write that raises leaves the watermark where it was and the
record is re-delivered. The alternative — a position that claims a record nobody wrote — is the
lost record this contract exists to prevent.

**The two findings #483 deferred to this step are answered here:**

- **F7** (the run environment is a destination the register cannot express) — the register now
  has a `projection`: a destination that receives the value and is not a store. `secret-value.value`
  declares `"projection": "run env"`, so it no longer reads as mirrored to nobody while one
  transient copy exists. A projected field mirrors to nobody, and `E-SYN-16` refuses both
  mistakes (a projection that names a plane, and a field that is projected *and* mirrored).
- **F8** (nothing blocks on its own) — `E-SYN-20` now refuses the write, and the CLI exits `1`.
  A violation at the seam is no longer reported and then ignored.

## Alternatives considered (and why not)

| Option | Rejected because |
|---|---|
| **Bidirectional sync**, each plane writing the fields it cares about | two writers to one field do not raise a conflict, they take turns; the loser is discovered in an audit, months later, with no trace of who overwrote what |
| **Last-write-wins** on a timestamp | it is bidirectional sync with the conflict hidden: the field looks written, one plane's value is gone, and the clock that decided was a laptop's |
| **Three-way merge / per-record reconciliation** | a merge needs a common ancestor and a human at the end of it; for a `label` and an ACL there is nothing to merge — one plane knows the answer and the other is guessing |
| **Change-data-capture from both databases** | it mirrors the *implementation* rather than the decision: every new column becomes a sync surface, and the direction is decided by whoever wrote the trigger |
| **A shared database with row-level ownership** | one store with two writers is the dual write, one step to the left; it also puts the design plane and the tenant store in one failure domain |
| **Event-sourcing everything, replay to derive each plane** | correct, and a rewrite of both planes; the program needs a boundary now, and D2 already says which half is ephemeral |
| **Ownership at row granularity only** (what the boundary matrix says today) | a row is not a write: "org units are the enterprise's" does not stop a Paperclip profile edit from renaming one — the question is asked per field or not at all |
| **Nightly reconciliation instead of a watermark** | it makes correctness depend on a window: a skipped record is invisible until the next run, and the next run has the same bug |
| **A per-record `updatedAt` as the resume point** | the producer's clock decides what the consumer sees; a clock skew drops records and the run still exits `0` |

## What this does not decide

- **The transport.** Pull or push, batch size, retries — the stream contract is the same
  either way, and #486 is where the runtime enforces it.
- **Where the watermark lives.** The rule is that it is durable and transactional with the
  write; the table is OpenGate's to choose.
- **What to do with a proposal.** This contract refuses it at the seam. A "propose a change
  to the owning plane" workflow is a product decision nobody has asked for yet, and inventing
  one here would be a second writer with better manners.
- **Retention.** How long an applied watermark is kept is a retention question
  ([retention.md](retention.md)), not a sync question.

## Versioning

| Change | Version | What consumers do |
|---|---|---|
| wording, a link, a new example | none | nothing |
| a new field, a new stream, a clarified refusal | **minor** (`1.x`) | the seam accepts the new field; both planes update their pages in the same sitting |
| a field changes hands, a stream changes producer, or a direction reverses | **major** (`2.0`) | a new ADR ratifies it; every consumer re-reads the registry, and a watermark is re-based deliberately — never by resetting it to zero |

A field changing hands is the one change this contract cannot absorb quietly: it is exactly
the dual write D-S1 exists to prevent, made on purpose.

## Checking it today

The register is the machine form of this page, and the checker is the gate:

```bash
python3 scripts/check_sync_spec.py
python3 scripts/check_sync_spec.py --self-test
python3 scripts/check_sync_spec.py --company companies/example-bank
python3 scripts/check_sync_spec.py --json
```

- the **registry** — `tests/fixtures/sync/field-ownership.json`, validated against
  `schemas/field-ownership.json`;
- the **oracle** — `scripts/check_sync_spec.py`, sixteen refusals, `--self-test` mutating the
  committed registry once per code;
- the **company check** — every property of `companies/company.schema.yaml`, and every key of
  **every** company model under `companies/*/`, must have an ownership row. The walk is the
  default, not a flag (review F5, #483): CI runs the bare command, so a flag it never passes
  would have been a check that never ran. `--company` narrows it to one;
- the **ratification** — `E-SYN-15`: [ADR-003](adr-003-sync-semantics.md) exists, is marked
  ACCEPTED, ratifies this contract, and is linked from the program doc. A decision nobody can
  find from the front door is a draft with a better name.

The enforcement in the runtime is #486; until it lands, this page and its register are the
contract the compiler, the adapter and the tenant are written against.

## Review (#483)

The draft was reviewed against the code it names, not against its prose:
[paperclip-reviews/PC2-25-02-field-ownership.md](paperclip-reviews/PC2-25-02-field-ownership.md).
Eight findings; six resolved in this page and its register, two deferred with an owner.
