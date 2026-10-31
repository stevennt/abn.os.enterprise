---
name: legal-issue-spotting
version: "1.0.0"
description: Spot legal issues completely using IRAC per issue, jurisdiction check, and authority ranking before concluding.
license: Proprietary
compatibility: opencode
metadata:
  domain: legal
  qc_id: QC-LEGAL-001
---

# Legal issue spotting

Product source: `industries/legal/pack/skills/legal-issue-spotting/`. Active only
when `legal` is on in `opengate.json`. Judgment skill (prompt-side); the
completeness checker, not the citation formatter.

## Checklist

1. Jurisdiction first: governing law, venue, conflicts. State assumptions.
2. List every issue separately (liability, defenses, procedure, remedies, limitations).
3. Per issue use IRAC: Issue → Rule (cited) → Application (cited facts) → Conclusion + confidence.
4. Rank authority: statute/regulation > binding precedent > persuasive > commentary.
5. Holding vs dicta: never present dicta as a holding.
6. End with: limitations, what counsel must verify, what would flip the answer.

## Example

Good: `Issue 2 (limitation): Rule: Art. X §Y (3-year) [stat:12]. Applied to accrual 2023-05-01 [exh-C:2] → time-barred 2026-05-01 (high).`

Bad: `Probably time-barred under the statute.` (no article, no date math, no citation).
