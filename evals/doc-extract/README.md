# doc-extract eval set v1.0 (issue #62) — 300-doc golden set

## Composition (all synthetic, `_synthetic_pii: true`)

| Slice | Count | Notes |
|---|---|---|
| CCCD front/back, clean scans | 100 | baseline readability |
| CCCD worn/expired/glare | 50 | abstain expected on ~half |
| payslips (3 common formats) | 80 | income field is the hard one |
| bank statements (income proof) | 40 | multi-page, tables |
| adversarial (forged font, mismatched face) | 30 | must abstain or flag, never hallucinate |

## Targets

- Field F1 ≥ 0.97 on clean slices, ≥ 0.90 overall; number fields (income, CCCD digits)
  exact-match ≥ 0.99 — a wrong digit is worse than an abstain.
- Abstain threshold 0.70: golden set asserts every sub-threshold doc lands in REVIEW
  (G68) and no invented values appear in outputs.

## Protocol

Golden set frozen by hash; model bumps re-run the full set (G67 harness) and the
promotion gate (A10) reads the report. New failure modes found in prod become new
golden docs within 14 days (trace-to-data loop).
