# Tenant → enterprise-repo company mapping (issue #232)

Which repo owns which company's model, recorded where the OpenGate resolver can
read it: the tenant's `customers/<tenant>/domains.json`, next to the domain
overlays and bundle pins (`docs/core/bundles.md`).

The company model itself is `companies/<id>/company.yaml` (see
`docs/core/onboarding-company.md`); this document is the join between the
platform's tenant/company ids and the model that owns them.

## The block

```json
{
  "version": 1,
  "domains": {}, "versions": {}, "bundles": {},
  "enterprise": {
    "repo": "stevennt/abn.os.enterprise",
    "tag": "contract-2026.11.1",
    "sha": "a7baab409dce013bd296b57aafc500565b878dfa"
  },
  "companies": {
    "abnasia": { "company": "example-bank", "note": "company #1" }
  }
}
```

| Field | Owner | Meaning |
|---|---|---|
| `enterprise.repo` | engineering | the repo that owns the models |
| `enterprise.tag` | engineering | the **contract release** the tenant is built on (`<stream>-YYYY.MM.N`, `docs/core/release.md`) |
| `enterprise.sha` | engineering | the commit the tag must resolve to — tags move, commits do not |
| `companies.<local id>.company` | engineering | the model directory in that repo (`companies/<id>/`) |
| `companies.<local id>.repo/tag/sha` | engineering | optional; if present must equal the tenant pin |
| `companies.<local id>.note` | sales | free text, like a bundle note |

`<local id>` is the company id inside the tenant — the tenant id itself for a
single entity, `profile.companies[].id` for a group.

## What the resolver refuses

OpenGate `gateway/company_map.py` reads the block; `resolve.py` and `--sync`
enforce it:

- a mapping key that is not a declared company of the tenant;
- a company mapped to a **different contract release** (or repo/sha) than the
  tenant pin — the message names both, e.g. *"company 'abnasia' maps model
  'example-bank' to 'contract-2025.01.1', but tenant 'abnasia' pins
  'contract-2026.11.1'"*;
- two companies mapped to the same model directory — one model names one
  entity;
- `companies` without an `enterprise` pin, or a malformed tag/sha/entry.

`--show` reports the map at `opengate.company_map`; `--org --company <id>` and
`--industry --company <id>` refuse on a mismatch instead of running the wrong
model's configuration.

## Company #1

The first real mapping, recorded in
`abn.platform.opengate/customers/abnasia/domains.json` and documented here:

| | |
|---|---|
| tenant | `abnasia` (single legal entity, entity id = `abnasia`) |
| model | `companies/example-bank` in `stevennt/abn.os.enterprise` (scaffold — `companies/example-bank/docs/status.md`) |
| contract release | `contract-2026.11.1` |
| commit | `a7baab409dce013bd296b57aafc500565b878dfa` |
| industry | `banking`, pack `banking-pack-2026.10.1` |

The model is a scaffold on purpose: the mapping, the pin and the refusal rules
are real, the org content is the next turn's work. When the customer's model
lands, the entry keeps its shape and only `company` (and the model's content)
changes.

## Relationship to packs and bundles

- **Bundles** (`docs/core/bundles.md`) pin *content* (industry packs) the tenant
  consumes; the bundle entry carries its own `repo`/`tag`.
- **`enterprise`** pins the *contract* the tenant's company models are built
  from; it is a different stream (`contract-*` vs `<industry>-pack-*`).
- **`companies`** maps the tenant's legal entities to model directories. A
  company may consume a bundle the tenant already pins; the two blocks answer
  different questions and neither replaces the other.

The enterprise side validates a model's own pin with
`python scripts/validate_company.py` (tag+sha against the repo); OpenGate checks
the tenant side (shape + equality with the tenant pin). A model pinned to a
release the tenant did not pin is refused by the resolver, which is the point.
