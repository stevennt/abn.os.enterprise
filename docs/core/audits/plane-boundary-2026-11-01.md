# Plane boundary audit

- contract: `paperclip-boundary@1.0`
- commit: `393b071`
- at: 2026-11-01T08:25:22Z
- **verdict: PASS**

| Check | Exit | What it said |
|---|---|---|
| boundary | 0 | plane-boundary: 91 model files stay in the design plane — OK |
| boundary self-test | 0 | plane-boundary --self-test: 11 cases, each rule bites — OK |
| contract tests | 0 | plane-contract: 10 decisions, 4 seams, one owner per field, 9 findings dispositioned, ADR accepted, version + upgrade path, explainer + reader check, index links — OK |
| contract self-test | 0 | plane-contract --self-test: 13 mutations, each caught — OK |
| template spec | 0 | paperclip-template: paperclip-company.example.json valid — example-bank (3 agents, 2 routines, paperclip-boundary@1.0) |
| template self-test | 0 | paperclip-template --self-test: 11 cases (1 valid, 10 refused) — OK |
| compiler | 0 | paperclip-compiler tests: 2 goldens, determinism, hierarchy, shared role, touchpoint, human/system/external exclusion, 9 refusals, --all opt-in policy, compile record, surface — OK |
| compiler self-test | 0 | paperclip-company --self-test: fixture compiles deterministically, pending rules stay supervised, L2 never autonomous — OK |
| compiler --all | 0 | paperclip-company --all: 0/1 compiled |
| compile records | 0 | compiles: 2 record(s) across the companies — OK |
| compile records self-test | 0 | compiles --self-test: 6 cases (1 clean, 5 refused) — OK |
| docs links | 0 | docs-link: 6 front-page docs, no dangling references — OK |
| playbook | 0 | playbook: all 43 CI scripts are referenced — OK |
| industry model | 0 | readme-map: 10 entries all exist — OK |
| company model | 0 | companies: 1 model(s), 0 failure(s), 0 warning(s) |

## Open items inherited by the tiers

| Item | Issue |
|---|---|
| run-context mode in resolve.py | #283 |
| agent service accounts (no password) | #273 |
| per-agent budget vs tenant ceiling, group split | #302 |
| OpenGate-down semantics (fail closed) | #352 |

## Guarded files (sha256)

- `docs/core/paperclip-integration.md` — `15a6f91526dc0fbf…`
- `docs/core/adr-002-paperclip-three-planes.md` — `5cf1325f2a160b8a…`
- `docs/core/paperclip-reviews/PC1-01-02-plane-contract.md` — `9b6a5e8b854184e6…`
- `docs/core/paperclip-explainer.md` — `8f051c377c9eeebe…`
- `docs/core/paperclip-reviews/PC1-01-09-explainer.md` — `eb50541a968e6963…`
- `scripts/check_plane_boundary.py` — `9f0f42e84db35eaf…`
- `scripts/test_plane_contract.py` — `1f20fa2f8b3a3582…`
- `scripts/check_paperclip_template.py` — `5909e3da947dc11a…`
- `scripts/test_paperclip_company.py` — `5df02a216a05f2da…`
- `scripts/validate_compiles.py` — `6398706ea8257d1e…`
- `bin/paperclip-company` — `ee7debc5ae986c48…`
- `schemas/paperclip-company.json` — `ffa3738ce881bba0…`
- `tests/fixtures/paperclip-company.example.json` — `164b2fa6d3d9e4a6…`
- `docs/core/paperclip-compiler.md` — `290119a70c37f47e…`
- `scripts/audit_boundary.py` — `9712a8da18a9ae2e…`

Re-verify with `python scripts/audit_boundary.py --verify <this file>`.
