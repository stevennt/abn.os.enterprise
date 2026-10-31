# Glossary (ubiquitous language, v0.1)

- **Situation:** one business moment needing handling (loan request, complaint, STR hit).
- **Event:** typed trigger of a situation, with versioned Data payload.
- **Router:** deterministic classifier Event → (Process id, version).
- **Process:** versioned steps; each step is workflow|ai|human.
- **Rule:** versioned policy row (DMN), never embedded in code.
- **Touchpoint:** meeting point with C/E/S/X, with channel + SLA.
- **Instance:** one running process (has id, trace, audit chain).
- **Level L0–L5:** automation degree per step (see engine/automation-levels.md).
- **Promotion:** L3→L4 only via eval + 30-day audit gate. **Demotion:** auto on Sev1/breach.
