# Accessibility + VI language QA v1.0 (issue #78) — the bank serves everyone

## QA checklist (every template + journey passes before deploy)

- [ ] Reading level: plain VI, one idea per sentence, no jargon without explanation.
- [ ] Tone: polite, neutral, correct pronouns (Quý khách); no blame, no slang, no ALL-CAPS.
- [ ] Numbers formatted VI (`1.000.000 VND`, never `1000000`); dates `dd/mm/yyyy`.
- [ ] Diacritics correct on push/Zalo/app; SMS-only variant allowed ASCII (registry notes which).
- [ ] Screen-reader order sane; no meaning in color alone; contrast AA on app surfaces.
- [ ] Touch targets ≥44px, timeout warnings before logout, error messages actionable.
- [ ] Consent + opt-out present where required (E47); no dark patterns.

## Sample review (templates/registry.yaml v1.0.0)

- `app-declined`: PASS with note — reason variable must use explainer text (I86),
  never a code; appeal CTA present. Fixed wording before deploy: "lý do" + human sentence.
- `otp-sign`: PASS — 5-min expiry stated, never-share warning present.
- `promo-optin`: CONDITIONAL — opt-out (`Soạn TC`) present, PASS; re-review on copy change.
- `transfer-done`: PASS — masked payee, txn ref present, no balance disclosed.
- Finding carried to H77: registry `vi` fields stay SMS-safe ASCII until per-channel
  diacritics variants land; track in templates/registry.yaml v1.1.0.
