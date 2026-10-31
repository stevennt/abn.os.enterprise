# Legal domain rules (apply only when the legal industry pack is pinned and enabled)

Business substance is **not** in this file and not in this repository yet. These
bullets are methodology + pointers; every pointer is a same-repo path so prose and
rule cannot drift apart:

- Governing law defaults to Vietnam for ABNAsia matters; if the matter points
  elsewhere, state the deviation — never silently switch jurisdiction.
- Rank authority under Vietnamese law: constitution/statute/code > guiding precedent
  (án lệ) > persuasive/foreign > commentary. Distinguish holding from dicta,
  statute from commentary. → enforced structurally by `rules/legal-citation-pack.yaml` `LEG-CITE-01`
- Every legal conclusion needs rule statement + cited authority + application to
  cited facts. → the conclusion itself always needs a recorded human decision:
  `rules/legal-signoff-pack.yaml` `LEG-SIGNOFF-02`
- Opinions are decision support, not legal advice. End with limitations and what
  counsel must verify. → `flows/legal-charge-review.flow.yaml`

## Placeholder (explicit, not implied)

placeholder: which article, which clause, which penalty range, which limitation
period — **none of it is here**. Those live behind a qualified reviewer; see
`industries/legal/docs/placeholders.md` for the tracked list. Scripts enforce this:
`scripts/pack_claim_scan.py` fails the build if a substantive legal claim appears
without a `placeholder:` marker or a same-repo cite.

## Corpus and retrieval

The bibliography (which instruments are licensed and where they come from) and the
hybrid retrieval design stay with the acquiring product (OpenGate `domains/legal/corpus.md`,
`retrieval.md`) — they describe *acquisition*, not law. The scenario bank
(`scenarios/*.json`, 27 files with injury percentages and charge ids) also stays
there until each scenario is gazette-verified: it already carries
`"verify": "pending gazette check — do not rely"` in its own data.
