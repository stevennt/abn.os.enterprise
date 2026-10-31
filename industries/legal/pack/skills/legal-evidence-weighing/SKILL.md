---
name: legal-evidence-weighing
version: "1.0.0"
description: Weigh conflicting evidence like an investigator, recording corroboration, credibility, and gaps.
license: Proprietary
compatibility: opencode
metadata:
  domain: legal
  qc_id: QC-LEGAL-003
---

# Legal evidence weighing

Product source: `industries/legal/pack/skills/legal-evidence-weighing/`.

## Method

1. List each material fact with all supporting and contradicting spans.
2. Score corroboration: independent sources > single source > assertion.
3. Record credibility notes (contemporaneous record vs recollection, interested witness).
4. State the gap: what single exhibit would decide the conflict.
5. Conclusion carries the weaker side explicitly ("despite Exh-D, weight favors...").

## Output contract (for QC reviewers)

Return JSON: `{"verdict":"pass|fail","severity":"low|high","quotes":["..."],"gap":"..."}`.
