# complaint-triage eval v1.0 (issue #65) — golden 200 complaints (synthetic)

## Golden set (200, all `_synthetic_pii: true`)

50 S1/S2 (loss, safety, regulatory keywords) + 100 S3 (service failures across
products) + 50 S4 (queries, tone traps: angry-but-simple, polite-but-complex).
Covers VI north/central/south phrasing and the top-20 intents.

## Checks

- Severity accuracy ≥ 0.95 (S1/S2 recall 1.00 — missing an S1 is unacceptable).
- Intent accuracy ≥ 0.90 on top-20 intents; below-threshold → REVIEW.
- Tone check: reply rated polite + neutral by rubric (no blame, no slang, correct
  pronouns); failures counted per template, fixed in H77 copy.
- Policy compliance: draft must not promise compensation, admit fault, disclose
  internal rule ids, or invent timelines — each violation fails the suite.

## Targets

- Severity accuracy ≥0.95, S1/S2 recall 1.00, intent ≥0.90.
- Tone pass 100%, policy violations 0.
