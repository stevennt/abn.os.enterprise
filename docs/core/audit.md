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

## Query API spec (issue #49) — "why was I declined?" must be answerable

Base: `GET /api/v1/audit`. Auth: staff JWT with case scope, or auditor grant.
PII in responses follows the masking table above; full payloads need the sealed key.

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/audit/instances/{id}` | full step chain + actor/rule/model versions + hashes |
| `GET /api/v1/audit/decisions?customer_id=…&from=…&to=…` | all decisions for a customer in a window, with reasons |
| `GET /api/v1/audit/verify/{instance_id}` | recompute chain, return OK/broken-at-seq |

Sample queries:

1. Explain one decline:
   `GET /api/v1/audit/instances/INST-88123` → steps s1–s6 with
   `SBV-DSTI-04@2026-10-01`, dsti 0.68 cited, actor chain, linked hashes.
2. Customer history: `GET /api/v1/audit/decisions?customer_id=C-88123&from=2026-01-01`
   → every decision + reason codes, masked PII.
3. Integrity proof: `GET /api/v1/audit/verify/INST-88123` → `{"ok":true,"events":6}`
   or `{"ok":false,"broken_at":3}` for tamper evidence.
