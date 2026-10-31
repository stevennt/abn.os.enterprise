# Segregation of Duties + delegation v1.0 (issue #19)

SoD failures are audit findings. The inbox (H74) and the authz model (B17)
enforce these pairs at runtime; I88 mines the audit chain for violations quarterly.

## Forbidden pairs (same person, same instance → deny)

| # | Maker (does) | Checker (decides) | Scope |
|---|---|---|---|
| 1 | RM recommends loan (rm_officer) | approves it (credit_manager/head) | all lending |
| 2 | investigates STR case (aml_analyst) | files it (mlro) / peer-reviews it | AML |
| 3 | requests hold (analyst) | confirms hold (compliance_manager) | AML |
| 4 | prepares payment batch (payments_operator) | releases it (payments_manager) | payments |
| 5 | tunes screening threshold | QA-samples the tuning | compliance |
| 6 | provisions access (ops_engineer) | approves prod access (itops_manager) | IT |
| 7 | posts journal (accountant) | approves post (finance manager) | finance |
| 8 | examines trade docs (trade_specialist) | waives discrepancy (trade_manager) | trade |
| 9 | fraud-holds card (fraud_analyst) | writes off loss (cards_manager) | cards |
| 10 | anyone | overrides own veto / approves own recommendation | universal |

Self-approval is always denied, no exceptions, at any amount.

## Delegation rules

- Delegation is **downward-or-lateral only** (manager → officer, never officer → manager),
  per named task type, with start/end dates. Max duration **14 days**; committee
  powers and MLRO filing power are **non-delegable**.
- A delegate inherits the delegator's SoD constraints: if the delegator is maker
  on an instance, the delegate cannot be checker on it (and vice versa).
- **Expiry:** delegations auto-expire at end date; expired grants deny by default.
- **Re-certification:** every delegation is re-certified quarterly by the unit head;
  unused delegations (>90 days no use) are revoked, not renewed.
- Emergency delegation (P1/outage): verbal + ticket, max 48h, dual-logged, reviewed
  next business day. Anything longer follows the normal path.
