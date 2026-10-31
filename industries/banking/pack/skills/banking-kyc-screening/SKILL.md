---
name: banking-kyc-screening
version: "1.1.0"
description: Screen sanctions, PEP, and adverse media before any banking recommendation; missing data blocks.
license: Proprietary
compatibility: opencode
metadata:
  domain: banking
  qc_id: QC-BANK-001
---

# Banking KYC screening

Pack path: `industries/banking/pack/skills/banking-kyc-screening/` in
`abn.os.enterprise`. Consumed by OpenGate as a pinned bundle (never a git checkout).
The customer provides the sanctions/PEP lists (licensed files, never committed);
evals use a synthetic mini-list. Gate script stays in OpenGate:
`qc/tools/qc_bank_screen.py` (QC-BANK-001).

## Source of truth (same repo — no tag dance)

Thresholds, dispositions and authority live **in this repository**, next to this
file. The citations below are relative paths, so a rule change and its prose change
land in the same commit and the same release tag.

- Screening thresholds/holds: `rules/aml-pack.yaml` → `AML-SCREEN-02@1.0.0-2026-10-01`
- Triage: `rules/aml-pack.yaml` → `AML-TRIAGE-01@1.0.0-2026-10-01`
- Holds / release authority: `rules/aml-pack.yaml` → `AML-HOLD-02@1.0.0-2026-10-01`
- Identity / liveness / blacklist: `rules/kyc-pack.yaml` → `KYC-01`, `KYC-02`, `KYC-03` @ `1.0.0-2026-10-01`
- Case flow (triage→hold→investigate→4-eyes→MLRO file): `flows/aml-str.flow.yaml` v1.0.0
- Approval bands: `org/org-retail.yaml` (B11), `org/org-corporate.yaml` (B12)

## Checklist (all three, every note)

1. **Sanctions**: screen consolidated list version pinned in evidence.
   Hit → evidence spans + timestamp; disposition cleared|escalated with
   reviewer + ref. Never cleared by the drafter (`AML-HOLD-02`).
   Thresholds as declared in `AML-SCREEN-02`: hold at 0.95, review from 0.80.
2. **PEP**: domestic + foreign PEP/adverse-media screen. Same hit rules.
3. **Adverse media**: name + DOB + id-number match; near-misses dispositioned
   (cleared with mismatch reason, never silently dropped).
4. **Amounts**: value + currency + value date + source ref, verbatim. No
   netting, no rounding, no reclassification (`docs/core/master-data.md`).
5. **Decision**: ship only over zero uncleared hits; otherwise revise
   (needs re-screen) or escalate (`LEG-TRIAGE-01` is not used here — see
   `AML-TRIAGE-01`).
