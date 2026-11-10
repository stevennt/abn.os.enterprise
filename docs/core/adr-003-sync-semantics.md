# ADR-003: sync semantics — one writer per field, one direction per stream, one watermark (issue #484) — ACCEPTED

**Status:** accepted (program) — ratified 2026-11-10 after the #483 review.
**Ratifies:** `sync-semantics@1`.
**Decided by:** the program operator. ADR-002 recorded the absence of a second review seat as
a risk; it is still absent, and it is still recorded here rather than hidden.
**Supersedes:** nothing. **Amends:** **ADR-002's ownership matrix** — *one owner per row*
becomes **one owner per field**, and the row-level matrix is now the summary of a field-level
registry rather than the whole rule.
**Inputs:** `docs/core/sync-semantics.md` (#482 draft),
`docs/core/paperclip-reviews/PC2-25-02-field-ownership.md` (#483 review),
`tests/fixtures/sync/field-ownership.json` (the register, 46 fields in 9 streams).

## Context

ADR-002 settled **which plane owns what**, at the granularity of rows: *org units, roles,
reporting lines → Enterprise OS; tickets → Paperclip; cases → OpenGate*. That is the right
answer to the wrong question at the moment a system writes. An implementation writes **fields**,
and a row is a family of them. "Org units are the enterprise's" does not stop a Paperclip
profile edit from renaming one, and nothing in either plane asks the question per field.

The second gap is the re-run. Every one of these crossings is a copy, and a copy needs a
position: without one, a sync either re-applies every record (slow, and a write storm) or skips
the ones it believes it has already applied (a silent loss that reports success). Neither
failure shows up as an error, which is why both survive a demo.

The #483 review put the question sharply: a watermark that nobody owns is a position in a
stream that **anybody** may write, and the first symptom of two writers is a record skipped
silently — precisely the failure this workstream exists to prevent.

What was true before this ADR: four planes, ten boundary decisions, one ownership matrix by
row, and no answer either question could be checked against.

## Decision

Adopt **`sync-semantics@1`** as written in `docs/core/sync-semantics.md`, with three clauses:

- **D-S1 — one writer per field.** Every field that crosses a plane boundary names exactly one
  **owning plane**. A write from any other plane is a **proposal**, refused at the seam — not
  merged, not queued, not reconciled nightly.
- **D-S2 — one direction per stream.** Fields live in **streams**; a stream has exactly one
  **producer**. A mirror may store a field and may never author one. One stream, one producer:
  `secret-ref` (OpenGate) and `secret-value` (vault) are two streams for that reason alone.
- **D-S3 — the watermark is the only resume point.** Every record carries a strictly increasing
  `seq` in its stream; a consumer stores the last value it applied per `(stream, tenant)`,
  applies only records above it, and treats a record at or below it as **already applied** — a
  no-op, not an error. A gap is a request for the missing range, never a skip.

Three consequences that are part of the decision, not implementation detail:

1. **The plan is a register, and the register is the truth.** `field-ownership.json` names, per
   field, the owner, the planes that receive a copy, **every** plane that may never originate a
   write, and the data tier. The document is its prose; the checker (`scripts/check_sync_spec.py`,
   fifteen refusals, `--self-test`) is what stops the two drifting. A field with no row is
   `E-SYN-11` — the check fires the day a company-model field is added without an owner.
   The fifteenth refusal is this ADR's own: `E-SYN-15` fails if the ratifying decision is
   missing, unmarked, ratifies another version, or is not linked from the program doc.
2. **The watermark is a field, and a field has an owner** (review F1). Nine `.seq` rows, one per
   stream, owned by its producer. A watermark declared in a stream but absent from the register
   is refused (`E-SYN-10`).
3. **One data tier, borrowed rather than invented** (review F2). `sensitivity` is
   `confidentiality.md`'s data tier — `PII-strict`, `confidential`, `internal`, `public` — and
   the checker compares the register against `metamodel/event.schema.yaml` (`pii_class`) so a
   fifth level cannot appear on one side only.

**This does not change any existing store.** The register describes the boundary as it already
is; no file, table or record changes shape. What changes is that the description is now
machine-checkable and the direction is fixed.

## Consequences

- **Positive:** a field's writer is answerable **before** a write, by anyone, with a command;
  a replay is safe by construction rather than by care; a proposal has a defined outcome
  (refused) instead of an undefined one (merged, eventually); a field that changes hands is a
  visible major rather than a quiet edit.
- **Negative (accepted):** a register to maintain, and adding a field to the company model now
  needs an ownership row — a real cost paid by the compiler workstream, and the point of the
  decision. Writes that were previously *assumed* to be somebody's are now written down, plane
  by plane, for all 46 fields.
- **Cost:** none at runtime yet. The enforcement at the seam is #486; until it lands this ADR is
  binding on **design**, and the checker is the only enforcement that exists.
- **Migration:** none. The register's first commit describes today's boundary; no consumer has
  to change to comply, and the first sync implementation is written against the register rather
  than inventing its ownership.

## What would reverse this

1. **A store that enforces field ownership itself**, atomically with the write, with no seam to
   cross — then the register becomes a comment on that store rather than a contract, and D-S1
   moves into the store's privilege model.
2. **Two-way editing becomes a real requirement** — a product decision that a Paperclip UI
   authors org data. That reopens D-S1 and D-S2 **for the fields it touches**; it does not
   reopen D-S3, because a re-run still needs a position no matter who may write.
3. **The watermark proves unusable for a consumer that cannot store it transactionally** — then
   a per-record idempotency key replaces D-S3. The ownership rule is unaffected: idempotency
   answers "have I applied this", ownership answers "may you write it", and they are different
   questions that neither replaces.

## Rejected alternatives

Recorded in the contract's *Alternatives considered* table and the #483 review: bidirectional
sync, last-write-wins on a timestamp, three-way merge, CDC from both databases, a shared
database with row-level ownership, event-sourcing everything, row-level ownership alone (what
ADR-002 says today), nightly reconciliation, and `updatedAt` as a cursor.

The three most tempting share one failure: the field looks written, one plane's value is gone,
and the trace is a clock that a laptop owned.

## Open items inherited by the tiers

| Item | Owner | Issue |
|---|---|---|
| the run environment is a projection, not a store (`secret-value.value` reads as mirrored to nobody while one transient copy exists) | sync workstream | #486 |
| nothing blocks on its own — which findings refuse a write, and whether any refuses a run | sync workstream | #486 |

Both are **enforcement** questions, and both were deliberately left out of the draft: a rule
written where it cannot be enforced is believed because it is written down, which is the failure
mode ADR-002 D9 already names in another shape.

**Reviewer's note (from #483, carried here):** the finding that mattered was the watermark
without an owner — found by asking the register a question the register could not answer about
itself. That is the cheapest kind of finding and the easiest to miss when the document and the
machine form are written in the same sitting, which is why the two are now checked against each
other in both directions (`E-SYN-09`, `E-SYN-13`).
