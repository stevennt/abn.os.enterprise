# Audit chain (issue #5) — construction + PII-masking rule

Envelope: `metamodel/audit.schema.yaml` (v1.0.0). Every process step emits one
event; `scripts/audit_chain.py` builds and verifies the chain.

## Construction

- `hash[i] = sha256(canonical_json(envelope minus hash))`, `hash_prev[0] = GENESIS`.
- Canonical form: sorted keys, no whitespace, UTF-8. Replay reproduces the exact digest.
- `seq` is gapless per instance; verifier rejects gaps, reordered links, and edits.

## PII-masking rule

Raw PII **never** enters the chain. Store `inputs_hash` (sha256 of canonical
inputs) + `payload_ref` (pointer to the sealed payload store) instead.

| Field | In audit chain | In sealed payload store | In staff UI |
|---|---|---|---|
| cccd / national id | absent (only its hash via inputs) | encrypted at rest | last 3 digits, permission-gated |
| name / phone / address | absent | encrypted at rest | masked (`Ng*** An`), permission-gated |
| income docs | absent (hash only) | encrypted, retention per E48 | view-on-approval, watermarked |
| decisions / rule+model versions | plaintext (auditable) | — | plaintext |

Joining audit to payload requires the sealed-store key: auditors get
time-boxed grants, never standing access.
