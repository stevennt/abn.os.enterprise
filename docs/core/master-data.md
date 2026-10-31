# Master-data model v1.0 (issue #32) — one truth per entity, or flows disagree

## Entities, keys, owners

| Entity | Golden key | Natural keys | Owner | System of record |
|---|---|---|---|---|
| Customer (individual) | `customer_id` (C-...) | cccd_hash, phone_hash | retail | core CIF |
| Customer (corporate) | `customer_id` (C-...) | tax_id | corporate | core CIF |
| Account | `account_id` | (customer_id, product, opened_date) | owning unit | core |
| Loan facility | `facility_id` (APP-/FAC-...) | (customer_id, product, application_id) | credit units | LOS |
| Employee | `employee_id` (E-...) | national_id_hash, email | hr | HRMS |
| Case (dispute/complaint/STR) | `case_id` | (channel, external_ticket_id) | owning unit | case-mgmt/CRM |

Golden key is immutable, never reused, never contains PII. Natural keys may change
(phone, address); the golden record survives them.

## ER sketch

```
Customer 1---* Account 1---* Txn
Customer 1---* LoanFacility 1---* Tranche --* CovenantTest
Customer 1---* Case 1---* AuditEvent
Employee 1---* TaskAssignment *---1 ProcessInstance
Rule - - -* ProcessStep (pinned versions, not FKs)
```

## Golden-record rules

1. One writer per attribute family (e.g. only KYC refresh writes verified name).
2. Survivorship: verified > self-declared > inferred; newer verified beats older.
3. Every merge/split is itself an audit event (who, why, rule version).
4. Downstream flows read golden keys only; display names are resolved at the edge.

## Duplicate-merge rule

- Candidate pairs score on (name similarity, id hash match, phone hash, DOB):
  score ≥0.90 → auto-propose merge; 0.70–0.90 → human review queue; <0.70 → ignore.
- Merge keeps the oldest golden key, retires the other as alias (never delete —
  history must resolve). Unmerge window: 30 days with full reversal.
- Corporate duplicates additionally match on tax_id (exact) + UBO chart overlap.
