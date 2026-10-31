# Workflow vs AI vs Human — routing checklist (copy into every process PR)

1. Is input structured + rule exists? → **workflow**.
2. Needs reading/unstructured extraction/scoring/drafting with verifiable output? → **ai** (JSON schema + eval + fallback to human).
3. Legal/financial sign-off, threshold breach, complaint, STR? → **human** (AI may draft, human decides).
4. No precedent / first version? → **human** at L2/L3, collect labels, then promote.
5. AI confidence < threshold or validator fails? → **human REVIEW**, never silent auto-approve.
