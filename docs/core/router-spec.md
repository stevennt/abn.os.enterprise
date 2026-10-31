# Router spec v1.0 (issue #4) — Event → (Process id, version)

The Router is a **deterministic classifier**. LLM must never be the router
(see ARCHITECTURE.md). Same input → same route, always; every decision logged.

## Inputs

- `event_type` (e.g. `loan.application.submitted`)
- `event_version` (semver of the payload contract)
- payload flags: small routing-relevant fields (e.g. `product`, `channel`,
  amount tier). Never free text.
- routing table version (itself versioned, deployed via the E46 pipeline).

## Resolution algorithm

1. **Exact match:** look up `(event_type)` in the routing table → candidate process list.
2. **Variant select:** evaluate flag rules top-to-bottom, first match wins
   (rules are ordered, mutually exclusive by construction; CI asserts no overlap).
3. **Version resolve:** within the matched process id, pick version by pinning policy below.
4. **Else:** no match at any step → dead-letter (never silent drop, never guess).

## Truth table (excerpt; full table lives with the routing table in D31/D35)

| event_type | event_ver | flags | → process | → version | note |
|---|---|---|---|---|---|
| loan.application.submitted | 1.x | product=unsecured | loan.retail.unsecured | pinned minor, latest patch (today 1.3.x) | worked example |
| loan.application.submitted | 1.x | product=mortgage | loan.retail.mortgage | same policy | C23 |
| transfer.requested | 2.x | rail=napas, amount<50M | transfer.domestic | default | J93 L4 slice |
| transfer.requested | 2.x | rail=swift | transfer.swift | default | sanctions re-check |
| complaint.received | 1.x | severity=S1 | complaint.handle | default, priority lane | C28 |
| (anything) | (anything) | no rule matches | — | — | dead-letter `NO_ROUTE` |
| loan.application.submitted | 0.x (retired) | — | — | — | dead-letter `VERSION_RETIRED` |

## Version-pinning + default-version policy

- Consumers (channels, schedulers) pin **`major.minor`** of the process they want.
  Patch rolls forward automatically (patches are backward-compatible by contract).
- **Default version** = latest released `minor` of a process. Changing the default
  is a rule PR (reviewed, audit-linked), never a hot edit.
- **Minor bump** (new flags/branches): dual-run window — old minor keeps serving
  in-flight instances; new instances take the new minor after the cutover date.
- **Major bump** (contract break): explicit migration per A06; old major serves
  until its sunset date, then routes become `VERSION_RETIRED` → dead-letter.
- In-flight instances always finish on the version they started with.

## Unknown-event → dead-letter spec

- DLQ envelope: `{received_at, event_type, event_version, producer,
  idempotency_key, reason_code, raw_payload_ref}` — payload stored, never dropped.
- Reason codes: `NO_ROUTE`, `VERSION_RETIRED`, `SCHEMA_INVALID`, `PII_CLASS_UNKNOWN`.
- Retention: 90 days queryable, then cold archive per E48.
- Alert: `NO_ROUTE` rate spike pages the owning team (new event family?);
  `SCHEMA_INVALID` pages the producer team.
- Triage SLO: 1 business day to route-or-rule (add routing row) or reject-with-reason.
- Replay: D39 backfill tool re-emits DLQ items after a routing fix (idempotent —
  idempotency keys survive the round trip).

## Classifier tiers v1.0 (issue #35) — deterministic first, ML only for ambiguity

Tier 1 (exact, ~99% traffic): `(event_type, event_version)` lookup — pure table, no model.
Tier 2 (flag rules, e.g. product/rail/amount tier): ordered first-match rules (see truth table).
Tier 3 (small ML, ambiguous intents only): complaint-text → (category, severity).
Nothing else may call the model; LLM is never in this path.

### Feature list (tier 3 model)

- char/word 3-5-grams (Vietnamese word-segmented) + channel + hour-of-day + customer
  tenure bucket + prior-complaint count. No raw PII features (hashed ids only, D33).
- Model: linear-logistic baseline, ≤5MB, CPU inference p99 <50ms. Versioned like data
  (model card + training hash pinned in the routing table release).

### Fallback threshold + version-pin policy

- Fallback: max-class probability <0.70 → route to human triage (`REVIEW`), never guess;
  threshold itself is versioned and tuned only on the golden set (G67).
- Version-pin: routing table release pins `(model version, threshold, flag-rule set)`
  together; rollback flips all three atomically. Model bump = MINOR release with
  dual-run shadow scoring for 7 days before it decides anything (A06).
