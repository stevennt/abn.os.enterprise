# Review — field ownership, one-way sync (`PC2-25-02`, issue #483)

- **Reviewer:** operator (single reviewer; the program still has no second seat — recorded as a
  risk in ADR-002, and it is still true here).
- **Subject:** `docs/core/sync-semantics.md` and its register at `e7e4f03` (draft from #482).
- **Verdict:** **accepted for ratification** (#484). Eight findings: six resolved in the
  contract, its register and the oracle; two deferred to the enforcement step (#486) with an
  owner. None of the deferred findings blocks the decision — they are about *how* it is
  enforced, not about *who owns what*.
- **Method:** read each clause against the code it names, not against the prose. Evidence is a
  command and its output, or a file/line, quoted per finding. Every "resolved" was re-run after
  the fix; every "deferred" names an issue and an owner.

## Findings

| # | Sev | Finding | Evidence | Disposition |
|---|---|---|---|---|
| F1 | **major** | **The watermark is not an owned field.** All nine streams declare `watermark.field = "<stream>.seq"` and no such field had a row — so by D-S1 nobody owned the contract's own resume point, and the checker only proved the string was non-empty. The one value whose writer decides whether a record is applied or lost was outside the contract. | `python3 -c "…['watermark']['field'] in fields"` → `model.seq declared=False` … `secret-value.seq declared=False` (all nine) | **resolved**: nine `.seq` rows added at 46 fields; `E-SYN-10` now requires the watermark to be a **declared field owned by the stream's producer**, and the self-test fires it by deleting `model.seq` |
| F2 | **major** | **`sensitivity` used the industry axis, not the data axis.** The register labelled four fields `restricted`, which `confidentiality.md` defines as an *industry* tier, and omitted `PII-strict`, the data tier's top level. A field labelled with the wrong axis reads as stricter while enforcing nothing. | `confidentiality.md:7` (data tier: `PII-strict / confidential / internal / public`) vs `:8` (industry tier: `public / commercial / restricted / classified`); `metamodel/event.schema.yaml:14` `pii_class: [PII-strict, confidential, internal, public]` | **resolved**: the four data tiers in schema, register and document; `E-SYN-14` compares the register's list with `pii_class` so the two cannot drift, and `secret-value.value` takes the top tier with the reasoning printed |
| F3 | **major** | **The approval decision was not a field.** D6 says *clicked in Paperclip, decided by the authority grid — OpenGate records the decision and the signer.* The register stopped at `work.approvalsUi` (the inbox) and had no row for the decision itself, so the durable half of D6 was unowned. | `gateway/approvals.py:2` ("one request, one decision, one signer") and `:298` (an agent cannot approve); the register had one `approv` row: `work.approvalsUi` | **resolved**: `evidence.approvals` added — opengate owns it, Paperclip receives the link, `confidential` |
| F4 | **major** | **The drift check ran one way.** `E-SYN-09` asked whether every registered field is printed; nothing asked whether every printed field is registered. Deleting a row from the register left its document row standing, so the prose would keep asserting an ownership that no longer existed — the failure the code is named for, undetected. | delete `model.contract` from the register, run: `E-SYN-11: … no row owns model.contract` — and **no** finding about the stale document row (`"document" in out` → `False`) | **resolved**: `E-SYN-13` added for the reverse direction; self-test fires it by printing a `model.ghost` row. It immediately caught the two `secret.ref`/`secret.value` rows this review renamed |
| F5 | minor | **CI never ran the company walk.** The document promised that a company field without an ownership row "exits 1", but CI runs the bare command and `--company` was opt-in — a check that only fires when a human remembers to pass a flag is a check that does not run. | `.github/workflows/validate.yml:53` — `check_sync_spec.py && check_sync_spec.py --self-test`, no `--company` | **resolved**: every `companies/*/company.yaml` is walked by default (discovered, not named); `--company` narrows to one. The success line now reports how many were walked |
| F6 | minor | **An unknown owner swallowed the stream finding.** The owner check `continue`d before the stream was resolved, so a field with a bad owner *and* an undeclared stream reported only `E-SYN-05` — one round trip to find two problems. | before: `E-SYN-05` only; after: `E-SYN-05: field 0: owner 'nobody'` **and** `E-SYN-07: … stream 'nowhere' is not declared` | **resolved**: the stream is resolved and checked first; the owner check continues afterwards |
| F7 | minor | **The run environment is a destination the register cannot express.** The boundary matrix says secrets are mirrored to `run env`; `run env` is not a plane, so `secret-value.value` reads as `mirroredTo: []` — "nobody receives it" — when in fact exactly one copy exists, transiently, in a process's environment. | `docs/core/paperclip-integration.md:120` `| secrets | vault | run env | both stores |`; register: `secret-value.value` → `mirroredTo: []` | **deferred** → #486 (enforce), owner: sync workstream. A `projection` marker (a destination that is not a store: no watermark, no copy at rest) is a modelling change that belongs with the code that injects it. The field's own note states the fact today |
| F8 | minor | **Nothing blocks on its own.** `verdict()` returns an empty `blocking` list: every finding is a shape problem, and the exit code is the only consequence. For a draft that is right; for a contract it means a violation is reported and then ignored, at the seam where ignoring it is a dual write. | `scripts/check_sync_spec.py` `verdict()` → `(not findings, [])` | **deferred** → #486 (enforce), owner: sync workstream. Which findings refuse a write — and whether any refuses a *run* — is the enforcement decision, not the draft's |

## What changed in the contract because of this review

- **nine `.seq` rows** and a *Watermark fields* table: the resume point is a field with an
  owner, and `E-SYN-10` refuses a watermark nobody owns;
- **the data tier** (`PII-strict` / `confidential` / `internal` / `public`) replaces the
  industry tier in the register and the page, tied to `metamodel/event.schema.yaml` by
  `E-SYN-14`;
- **`evidence.approvals`** — the decision and its signer are OpenGate's, and D6 now has a field
  it can be checked against;
- **`E-SYN-13`** — the document can no longer print a field the register does not declare;
- **the company walk is the default**, so CI checks it;
- **`E-SYN-07`** — a field id must begin with its stream, which is why the two secret fields are
  now `secret-ref.ref` and `secret-value.value` rather than `secret.ref` / `secret.value`;
- **fourteen refusals**, up from twelve.

## What is still open (with an owner and an issue)

| Finding | Owner | Issue | Blocks |
|---|---|---|---|
| F7 the run env is a projection, not a store | sync workstream | #486 | a truthful `secret-value` mirror |
| F8 nothing blocks on its own | sync workstream | #486 | enforcement at the seam |

**Reviewer's note.** F1 is the one that would have shipped: a watermark with no owner is a
position in a stream that anybody may write, and the first symptom of two writers is a record
that is skipped silently — the exact class of failure this workstream exists to prevent. It
was found by asking the register a question the register could not answer about itself, which
is the cheapest kind of finding and the easiest to miss when the document and the machine form
are written in the same sitting.

F2 and F3 are the same mistake in two shapes: a vocabulary borrowed from a neighbouring
concern (`restricted` from industries) and a field that stopped one step short of the thing it
describes (the inbox, not the decision). Both read as complete until somebody greps.

The two deferrals are deliberate. Both are enforcement questions, and answering them in the
draft would repeat the pattern this program already rejected once: a rule written where it
cannot be enforced, believed because it is written down.
