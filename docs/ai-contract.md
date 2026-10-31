# AI-step contract v1.0 (issue #61) — non-negotiable containment

Every `kind: ai` step ships with a contract file (`ai/<step-id>.contract.yaml`).
No contract, no deploy. The engine validates the contract at load and at every release.

## Contract template

```yaml
step_id: s2-extract
version: 1.0.0
input_schema: events/doc-extract.in.v1.json   # what the step may read
output_schema: events/doc-extract.out.v1.json # JSON-schema; anything else = violation
model: {name: doc-extract, version: 2026-10-20, temperature: 0}
pii_class: confidential                        # max tier the step may see (D33)
eval_suite: evals/doc-extract/                 # must be green at pinned version (G67)
abstain_below: 0.70                             # confidence floor -> REVIEW
fallback: REVIEW                                # always a human lane, never auto-approve
cost_budget_per_1k: {vnd: 0, ms_p99: 0}        # filled by G69
```

## Violation = auto-REVIEW rule

Any of these diverts the instance to REVIEW with reason code, pages nobody, and
counts against the step's promotion evidence (A10):

- output fails `output_schema` validation (extra fields, wrong types, invented numbers)
- model version != pinned version, or eval suite not green at this version
- confidence below `abstain_below`, or validator/timeout failure
- input contains a higher PII tier than the contract allows (D33)

Silent auto-approve on violation is forbidden and tested: the G68 suite injects
schema-breaking outputs monthly and asserts every one lands in REVIEW.
