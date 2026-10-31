# Glossary (ubiquitous language, v1.0 — FROZEN by issue #3)
# Sign-off (2-role review): domain/bank-ops lens + engineering lens, 2026-10-31.
# Change after freeze requires a new issue + minor version bump.

- **Situation:** one business moment needing handling (loan request, complaint, STR hit).
- **Event:** typed trigger of a situation, with versioned Data payload.
- **Data:** the payload an Event carries (inputs schema) and a Process returns (outputs).
- **Router:** deterministic classifier Event → (Process id, version).
- **Process:** versioned steps; each step is workflow|ai|human.
- **Rule:** versioned policy row (DMN), never embedded in code.
- **Touchpoint:** meeting point with C/E/S/X, with channel + SLA.
- **Instance:** one running process (has id, trace, audit chain).
- **OrgUnit:** a department/team box on the org-chart; owns mandates and headcount.
- **Role:** a job function inside an OrgUnit; carries RACI scope and approval limits.
- **Level:** automation degree per step, L0–L5 (see engine/automation-levels.md).
- **Promotion:** L3→L4 only via eval + 30-day audit gate.
- **Demotion:** auto return to L3 on Sev1/regulatory breach.
- **Audit:** append-only hash-chained record of every step (who, what, rule/model version).
