# Threat model v1.0 (issue #9) — the OS itself

Scope: router, process engine, human-task inbox, Axum gateway, audit store,
event bus. Out of scope: core-banking internals (trusted via adapters, H75),
client device security. Review quarterly or after any Sev1.

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
