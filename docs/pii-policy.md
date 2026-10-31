# PII classification + masking policy v1.0 (issue #33)

Canonical policy. `docs/audit.md` holds the chain-specific view and defers to this
file on any conflict. Event schema `pii_class` (metamodel/event.schema.yaml) uses
these exact tier names.

## Tier table

| Tier | Definition | Examples | Handling |
|---|---|---|---|
| PII-strict | identifies a person alone; bank-secrecy protected | cccd, biometrics, full account numbers | never in logs/chain/twin; encrypted store; permission-gated UI |
| confidential | sensitive in combination or business-critical | income, balances, health-adjacent notes, STR contents | hashed/masked in logs; masked UI; encrypted warehouse |
| internal | staff-only operational data | employee ids, internal notes, rule thresholds | masked in external surfaces; plain internally with access log |
| public | approved for customers/regulators | product names, branch hours, decision reasons (no PII) | plain |

Default tier for any new field: **confidential** until Data Protection downgrades it
in review. Upgrades (public→confidential etc.) apply immediately; downgrades need sign-off.

## Masking examples per surface

| Field | Raw (never stored outside sealed store) | Logs / audit chain | Staff UI | Warehouse / twin |
|---|---|---|---|---|
| cccd `001099000001` | sealed only | absent (hash via inputs_hash) | `*********001`, gated | token `tok_cccd_9f2…` |
| name `Nguyen Van An` | sealed only | absent | `Ng*** An`, gated | token `tok_name_41a…` |
| phone `0901234567` | sealed only | absent | `090***4567`, gated | token `tok_tel_77c…` |
| account `9991•••003` (illustrative) | sealed only | last-4 `****2003` allowed | `****2003`, gated | token `tok_acct_…` |
| amount/balance | — | plain (needed for ops) | plain | plain |
| decision + rule versions | — | plain | plain | plain |

Tokens are format-preserving, non-reversible, and consistent per environment
(dev tokens never match prod). Detokenization requires the sealed-store key with
time-boxed grant (A05). Automated scanner (track F) fails the build on
`\b\d{9,12}\b` (bare CCCD-like runs) in logs, traces, and docs.
