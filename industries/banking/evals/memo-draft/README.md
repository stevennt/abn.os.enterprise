# memo-draft eval v1.0 (issue #64) — cited, no hallucinations

## Citation format

Every factual sentence ends with one or more citations:
`[input:requested_amount]`, `[rule:SBV-DSTI-04@2026-10-01]`, `[s3:income=85M]`.
Recommendation cites the deciding rule row. Uncited facts = violation → REVIEW (G61).

## Number-grounding test

For each of 200 golden memos: extract every number in the draft, assert each one
appears verbatim in a cited input/rule/step output. Metrics: grounding rate 100%
(zero tolerance — one invented number fails the suite), citation coverage 100% of
factual sentences. Suite also includes 30 adversarial cases (missing inputs, conflicting
sources) where the correct behavior is explicit abstain ("insufficient data"), not a guess.

## Targets

- Number grounding 100% (zero invented numbers), citation coverage 100%.
- 30/30 adversarial cases abstain explicitly.
