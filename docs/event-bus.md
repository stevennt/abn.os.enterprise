# Event bus design v1.0 (issue #36) — Redpanda (Kafka API), 3 brokers to start

One topic per event family (not per event — 40 topics is operable, 40×partitions fine).
Key = idempotency key (ordering per key, exactly the dedupe unit from A07).
Compression lz4, min.insync.replicas=2, acks=all on money topics.

## Topic table

| Topic | Events | Partitions | Retention | Cleanup | Notes |
|---|---|---|---|---|---|
| `bank.lending` | loan.*, mortgage, corp term/wc | 12 | 7y | delete | money trail; matches E48 |
| `bank.onboarding` | ekyc.*, deposit.*, corp account | 6 | 7y | delete | PII-strict payloads, encrypted |
| `bank.payments` | transfer.*, salary, billpay | 24 | 7y | delete | highest throughput; key=client key |
| `bank.cards` | card.*, auth.*, disputes | 12 | 7y | delete | scheme evidence window |
| `bank.trade` | lc, lg, collections, guarantees | 3 | 7y | delete | low volume, long life |
| `bank.compliance` | aml.*, kyc.*, sanctions | 6 | 7y | delete | regulator-visible, immutable |
| `bank.cs` | complaint.*, call.*, appointments | 6 | 3y | delete | links to CRM |
| `bank.hr` | recruit, onboard, leave, perf, exit | 3 | 3y | delete | internal tier |
| `bank.finance` | ap, gl-close, tax, budget | 3 | 7y | delete | ledger-adjacent |
| `bank.ops` | incidents, changes, access, eod | 3 | 1y | delete | high churn, short value |
| `bank.risk` | scoring, limits, early warnings | 3 | 3y | delete | feeds twin |
| `bank.treasury` | fx, mm, liquidity | 3 | 3y | delete | market data ages fast |
| `bank.audit` | audit chain events (A05) | 12 | 7y | delete | append-only, sealed readers |
| `bank.dlq` | all dead-letters (A04) | 6 | 90d hot | delete | then cold archive per E48 |
| `bank.ops.replay` | backfill/replay output (D39) | 3 | 7d | delete | short-lived by design |

## Retention + compaction choices

- **Delete, not compact**, everywhere: events are facts, never updates — the current
  state lives in Postgres + the audit chain, not in the log. (No `compact` topics
  in v1; revisit only if a config-broadcast need appears.)
- Money/compliance/audit topics: 7y to match record-retention (E48); storage sized
  for ~50M events/day at p99 payload 8KB before lz4.
- DLQ 90d hot (triage SLO is 1 day, A04) then cold archive; replay topic 7d.
- Partition counts scale with throughput (payments 24 first); re-partitioning needs
  a key-preserving migration plan, never mid-pilot.
