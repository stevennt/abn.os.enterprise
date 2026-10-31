# Legal pack placeholders (issue #132)

Every item below is **deliberately absent** from `industries/legal/pack/`. They are
tracked here so absence is a recorded decision rather than an oversight.

`scripts/pack_claim_scan.py` enforces the boundary in CI: a line asserting one of
these without a `placeholder:` marker or a same-repo cite fails the build.

## Not asserted anywhere in this pack

| Category | Why absent | Gate to add |
|---|---|---|
| Article/clause numbers (Điều/khoản) | a wrong article is confidently wrong | named VN lawyer review, gazette-verified text |
| Injury percentages and thresholds | numbers drive outcome; unverified numbers mislead | lawyer review + gazette cross-check |
| Penalty ranges / prison terms | sentencing framing is the highest-risk claim | lawyer review |
| Monetary penalties | same | lawyer review |
| Limitation periods / procedural deadlines | procedural errors have hard consequences | lawyer review |
| Charge element lists per offence | the four-element *framework* is included; specific offence elements are not | lawyer review, one charge at a time |
| Precedent (án lệ) application | precedent changes; needs versioned index | knowledge unit + licensed source |

## What *is* included (structural only)

- Four-element method (khách thể / mặt khách quan / chủ thể / mặt chủ quan) — a
  framework, not an assertion about any offence.
- IRAC issue spotting, authority ranking, citation formatting, evidence weighing.
- Output contracts (JSON shapes the checkers evaluate).
- Pointers to `rules/legal-citation-pack.yaml` and `rules/legal-signoff-pack.yaml`.

## Held back in the source product (OpenGate), not moved here

| Artefact | Why it stays there |
|---|---|
| `scenarios/*.json` (27 files) | contains injury percentages and charge ids; each carries `"verify": "pending gazette check — do not rely"` in its own data |
| `corpus.md` | bibliography + acquisition status (operational, not law) |
| `retrieval.md` | RAG/graph design (platform) |
| `connectors/congbao.py` | gazette scraper (platform tooling) |

## Pack status

`industries/legal/industry.yaml` → `pack.status: draft`. It becomes `active` only
when the table above is empty of "pending" and a reviewer is named. Until then the
pack may be resolved but must not be used for client work — stated in the pack's own
`rules.md`.
