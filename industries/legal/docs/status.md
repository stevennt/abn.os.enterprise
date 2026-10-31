# Legal industry status (issue #131)

**This industry is a scaffold.** It exists to prove the multi-industry contract, not
to give legal advice.

## What is here

| Artefact | Depth | Notes |
|---|---|---|
| `org/` | skeleton | 3 units, 1 unit with full RACI (litigation) |
| `rules/legal-citation-pack.yaml` | structural | 2 rules: citations resolvable/in-force/topical, quotations verbatim |
| `rules/legal-signoff-pack.yaml` | structural | 2 rules: no unsigned delivery, no AI legal conclusion |
| `flows/legal.charge-review.flow.yaml` | end-to-end | intake → issue spotting (AI) → citation check → counsel review → release |
| `pack/` | absent | agent content arrives only after legal review (issue #132) |

## What is deliberately absent

No statute numbers. No penalties. No limitation periods. No sentencing ranges. No
case outcomes. No element lists for specific charges. Every rule carries
`authority: pending-legal-review`, which means: the *structure* is decided, the
*substance* is not.

Reason: substantive Vietnamese law content in this repo becomes a source of truth that
an AI will paraphrase to a lawyer under time pressure. A wrong element list is worse
than no element list — it is confidently wrong. #132 imports the OpenGate legal pack
structure with placeholders rather than invented content, and a named qualified
reviewer must sign each rule pack before `authority` changes.

## Gate to become real

1. A qualified Vietnamese lawyer reviews each rule pack row-by-row.
2. `authority:` is replaced with the instrument and date; `version` bumps.
3. Only then may `pack.status` become `active` and a `legal-pack-*` tag be cut.

Until all three, `bin/verify-industry-tags.py` will (correctly) not demand a pack tag.
