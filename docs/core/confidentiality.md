# Confidentiality tiers + repo-split rule v1.0 (issue #134)

Two different things share the word "tier" in this repo. Do not conflate them:

| Axis | Question | Values | Where declared |
|---|---|---|---|
| **Data tier** | how sensitive is a *field*? | `PII-strict` / `confidential` / `internal` / `public` | `docs/core/pii-policy.md`, `metamodel/event.schema.yaml` (`pii_class`) |
| **Industry tier** | how sensitive is an *entire industry's content*? | `public` / `commercial` / `restricted` / `classified` | `industries/<id>/industry.yaml` (`tier`) |

A bank's *field* can be `PII-strict` inside a `commercial` industry. A defence
industry is `classified` even if every individual field is `public`.

## The rule

> **This repository hosts `public` and `commercial` industries only.**
> `restricted` and `classified` industries live in their own repository, reusing
> `metamodel/` at a pinned tag.

Why a repo split rather than a folder with a warning label: git history is forever
and clones are unlimited. One `git clone` of a mixed repo hands an attacker (or an
auditor from a different programme, or a contractor) the classification-defining
content of every industry at once. Access control applied to files inside a single
clone is not access control.

Enforced by `scripts/validate.py` (manifest tier must be `public` or `commercial`)
and re-checked by `scripts/cross_industry.py`. A `restricted`/`classified` manifest
in this tree fails CI — the failure message points here.

## Tiers

| Tier | Content examples | Hosted | Clone risk if leaked |
|---|---|---|---|
| `public` | open methodology, published tariffs | here | none |
| `commercial` | bank processes, thresholds, SLAs, client org charts | here | competitive + contractual |
| `restricted` | law-enforcement procedure, named-source material | own repo | legal + personal safety |
| `classified` | defence operations, unit structures, mobilization plans | own repo, air-gap capable | national security |

`restricted`/`classified` may still appear as **structure only** here — e.g. a
generic "case triage" flow with no names, no units, no real thresholds — but the
industry manifest for that content must not be `restricted`/`classified` in this
repo. If the content needs the tier, the content goes elsewhere; the tier label does
not travel to make it acceptable.

## Path for a restricted/classified industry repo

```
abn.os.<industry>-restricted/          (private repo, own access list)
├── README.md            — points at the pinned metamodel tag below
├── metamodel/           — VENDORED copy at a tag, never a git submodule
│   └── PINNED-FROM      — "abn.os.enterprise@<policy tag>"
├── industries/<id>/     — same layout as here (org, rules, flows, pack, docs)
└── .github/workflows/   — same checks, vendored scripts/
```

Rules for the split repo:

1. **Vendom the metamodel, do not submodule it.** A submodule URL leaks the private
   repo's existence and makes an air-gapped build impossible.
2. **`PINNED-FROM` is checked by CI** in that repo: the pinned tag must exist and the
   vendored `metamodel/` must be byte-identical to it (same trick as
   `bin/build-pack --verify`).
3. **No back-references.** The split repo never pushes content here. Sharing goes
   one way: shared *contracts* down, content never up.
4. **Packs from a split repo are never published as bundles** by this repo's
   `bin/build-pack`; they are built and consumed inside that boundary.
5. **Cross-tier pointers are forbidden both ways.** This repo must not reference a
   split repo's paths, and a split repo's public README must not name this repo's
   restricted counterparts.

## What a reviewer checks on an industry PR

- [ ] `industry.yaml` tier matches the content, not the ambition
- [ ] no real unit names, thresholds, or client identifiers in a `public` manifest
- [ ] if content is `restricted`/`classified`: it is not in this PR at all
- [ ] `pii_class` on new events is not downgraded without Data Protection sign-off

## Migration note

`defense-ops` and `civil-protection` packs currently live in the acquiring product
(OpenGate `domains/`). Under this rule they may **not** move here as
`commercial` industries just to keep the layout tidy; they either stay where they
are or move to a split repo. `industries/legal` is scaffold-and-structure only for
the same reason (see `industries/legal/docs/placeholders.md`).
