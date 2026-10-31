# Human-task inbox v1.0 (issue #53) — one queue (Frappe), not 12 systems

Every `kind: human` step materializes as exactly one inbox task. Humans approve,
delegate, or escalate there; the engine only resumes on task completion events.

## Task schema mapping (flow step → Frappe)

| Flow step field | Frappe Task field | Notes |
|---|---|---|
| step id + instance_id | `subject` = `[loan.retail.unsecured#INST-1] s5-decide` | unique, searchable |
| owner_role | `allocated_to` (role queue, not a person) | avoids single-person dependency |
| sla_minutes | `expected_end_date` = created + SLA | countdown visible |
| on_fail | escalation rule on breach | e.g. `escalate:risk` → reassign role queue |
| uses_rule | linked Rule version (read-only ref) | approver sees the exact grid version |
| AI draft (memo/score) | `description` prefix | human decides, AI only drafts |
| decision | custom result field (APPROVE/DECLINE/REVIEW + note) | completion event carries it back |

SoD (B19) enforced at claim time: maker of the instance cannot claim its checker task.

## Escalation demo (`scripts/inbox_demo.py`)

Builds s5-decide as a task, advances the clock past its 240-min SLA, and shows:
`OPEN → SLA_BREACHED → ESCALATED to risk queue (per on_fail) → claimed by
risk_manager → APPROVED`. Delegation (B19: 14-day max) modeled as reassignment
with expiry. Run: `python scripts/inbox_demo.py`.
