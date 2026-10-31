# Policy-as-code pipeline v1.0 (issue #46) — git to deploy for every rule pack

## Pipeline diagram

```
rule PR (rules/*.yaml)
  -> CI: schema-valid + coverage/no-overlap + version-bump check
  -> review: pack owner + required approvers (table below)
  -> merge to DEV -> versioned release tag (rules-YYYYMMDD.N)
  -> deploy: routing table + engine load new version; dual-run window opens (A06)
  -> audit link: every decision cites RULE-ID@version (A05); release notes archived
```

Emergency path (wrong threshold live): MLRO/CRO may hotfix with post-merge review
within 24h; the hotfix still gets a version + release note, never a silent edit.

## Required approvers per pack

| Pack | Owner | Required approvers | Notes |
|---|---|---|---|
| kyc-pack | retail + compliance | compliance_manager, risk_manager | front-door risk |
| aml-pack | compliance (MLRO) | mlro, risk_manager | criminal liability |
| credit-grid-pack | risk (CRO) | cro, retail/corporate director | SBV-linked |
| fee-pack | finance + retail | finance manager, retail_director | revenue leakage |
| new pack | proposing unit | unit head + risk + legal | legal always on new packs |

Quorum: 2 approvals minimum, one must be outside the proposing unit (SoD, B19).
Stale reviews (>14 days) need re-confirmation after a rebase.
