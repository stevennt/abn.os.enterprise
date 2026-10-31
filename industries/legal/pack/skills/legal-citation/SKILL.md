---
name: legal-citation
version: "1.0.0"
description: Format and verify legal citations so every authority is checkable and every quote is exact.
license: Proprietary
compatibility: opencode
metadata:
  domain: legal
  qc_id: QC-LEGAL-002
---

# Legal citation

Product source: `industries/legal/pack/skills/legal-citation/`. Pairs with the
deterministic `qc/tools/qc_citation.py` script. This skill is the judgment
half; the script is the verification half.

## Rules

- Cite in a fixed form: `[authority:pinpoint]` plus exhibit spans for facts.
- Pinpoint required: article/section/page, not the document title alone.
- Quote holdings exactly. Ellisions marked with `[...]`, never silent.
- If an authority cannot be located, cite as `UNVERIFIED` and let `qc_citation` fail the gate.
