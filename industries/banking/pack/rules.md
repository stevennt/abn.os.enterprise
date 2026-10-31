# Banking domain rules (apply only when `banking` is on in opengate.json)

Business substance lives **in this repository** (`industries/banking/`), not here —
these bullets are pointers, and the pointer is a relative path so code and prose
cannot drift apart:

- Screen sanctions/PEP/adverse-media before any recommendation. Missing data = blocked, not assumed clean. → `rules/aml-pack.yaml` `AML-SCREEN-02`, `rules/kyc-pack.yaml` `KYC-01`
- Never round, net, or reclassify amounts. Preserve currency, value dates, and source references. → `docs/core/master-data.md` (golden-record discipline)
- Flag structuring, layering, and jurisdiction-hopping patterns explicitly with evidence spans. → `rules/aml-pack.yaml` `AML-TRIAGE-01`; case flow `flows/aml-str.flow.yaml`

Pack version and release stream are declared in
`industries/banking/industry.yaml`; consumer pins are recorded by the consumer
(e.g. OpenGate `docs/enterprise-pins.yaml`), never here.
