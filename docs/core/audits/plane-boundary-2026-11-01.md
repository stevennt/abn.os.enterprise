# Plane boundary audit

- contract: `paperclip-boundary@1.0`
- commit: `0cf7fd6`
- at: 2026-11-01T08:09:06Z
- **verdict: PASS**

| Check | Exit | What it said |
|---|---|---|
| boundary | 0 | plane-boundary: 91 model files stay in the design plane — OK |
| boundary self-test | 0 | plane-boundary --self-test: 8 cases, each rule bites — OK |
| contract tests | 0 | plane-contract: 10 decisions, 4 seams, one owner per field, 9 findings dispositioned, ADR accepted, version + upgrade path, explainer + reader check, index links — OK |
| contract self-test | 0 | plane-contract --self-test: 13 mutations, each caught — OK |
| docs links | 0 | docs-link: 6 front-page docs, no dangling references — OK |
| playbook | 0 | playbook: all 39 CI scripts are referenced — OK |
| industry model | 0 | readme-map: 10 entries all exist — OK |
| company model | 0 | companies: 1 model(s), 0 failure(s), 0 warning(s) |

## Open items inherited by the tiers

| Item | Issue |
|---|---|
| run-context mode in resolve.py | #283 |
| agent service accounts (no password) | #273 |
| per-agent budget vs tenant ceiling, group split | #302 |
| company-template schema | #252 |
| OpenGate-down semantics (fail closed) | #352 |

## Guarded files (sha256)

- `docs/core/paperclip-integration.md` — `41d2711b130254c7…`
- `docs/core/adr-002-paperclip-three-planes.md` — `5cf1325f2a160b8a…`
- `docs/core/paperclip-reviews/PC1-01-02-plane-contract.md` — `9b6a5e8b854184e6…`
- `docs/core/paperclip-explainer.md` — `8f051c377c9eeebe…`
- `docs/core/paperclip-reviews/PC1-01-09-explainer.md` — `eb50541a968e6963…`
- `scripts/check_plane_boundary.py` — `641b11e2e57dd4cb…`
- `scripts/test_plane_contract.py` — `1f20fa2f8b3a3582…`
- `scripts/audit_boundary.py` — `2da23f10007a4ee2…`

Re-verify with `python scripts/audit_boundary.py --verify <this file>`.
