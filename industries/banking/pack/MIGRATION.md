# Banking pack — migration notes

Every released pack version documents its migration impact here. Consumers pin a
pack tag (`banking-pack-YYYY.MM.N`, see `docs/core/release.md`); bumping the pin
certifies the consumer reviewed the notes below.

## [1.1.0] — imported from OpenGate (loop 4, issue #128)

**Breaking for consumers that resolved policy through `abn.os.enterprise@<tag>`
citations.** The pack now lives in the same repository as its rules, so:

- `abn.os.enterprise@banking-2026-10-31.1` style citations are gone; the skill cites
  `rules/aml-pack.yaml` and `flows/aml-str.flow.yaml` relative to the industry dir.
- `skills/banking-kyc-screening` version 1.0.0 → 1.1.0 (prose re-pointed, no
  behavioural change: same screens, same holds, same thresholds).
- OpenGate's `qc/tools/check_enterprise_cites.py` no longer applies to this pack;
  the equivalent guarantee is same-repo file identity (see issue #129).

No migration needed for agent behaviour: roles, templates, temperatures and step
caps are unchanged from 1.0.0.

## [1.0.0]

Initial versioned release.
