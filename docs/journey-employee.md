# Employee inbox v1.0 (issue #74) — where employees feel the OS

Builds on F53 (task mapping) and B19 (SoD/delegation): this is the queue behavior spec.

## Queue spec

- One queue per person, fed from role queues (B17); tasks carry SLA countdown,
  breached-first ordering, and full context (instance trace + AI draft + rule version).
- Claim enforces SoD: maker cannot claim checker tasks (B19); claim is exclusive
  (one holder, 30-min soft lock, auto-release with note).
- Delegate-with-expiry inline (max 14d, B19); delegate inherits SoD constraints;
  delegation shown on the task (who → whom → until).
- Done requires decision + note; REVIEW notes need a reason code (G68).

## Escalation matrix

| Trigger | Action | To |
|---|---|---|
| 50% SLA elapsed, untouched | nudge holder + show in manager view | holder |
| 100% SLA, untouched | reassign + breach flag | next role per step on_fail |
| 2nd breach same instance | page duty owner | unit duty roster |
| delegate expires with task open | return to role queue + flag | role queue |
| SoD conflict at claim | deny + suggest eligible peer | claimer |

Managers see aggregate (breach counts, aging buckets), never other units' PII.
Workload balancing: auto-suggest reassignment when a holder exceeds 1.5× median load.
