# Company portability — templates, pins, and a bundle that proves itself (contract `company-portability@1`)

**Status:** interface specified (#322), implemented in `scripts/portable.py`
(#323), wired into the compiler (#324); the record, surface, harden, measure and
demo steps follow (#325–#331). **Shape:** `schemas/portability-manifest.json`. **Checker:**
`scripts/check_portability_spec.py` (CI, `--self-test`). **Boundary:** ADR-002 D8
— *company templates carry a contract pin; import refuses an unresolvable pin;
upgrades are explicit.*

A compiled template is portable only if the things it **names** travel with it.
Today `paperclip-company.json` carries a contract `tag` + `sha` and cites packs,
flows and rules by id, but nothing says what a complete export is, how an import
proves it received the same artefact, or what a rollback restores. This contract
is that answer: one manifest, one bundle id, seven refusals.

```
company model ──compile──▶ template (contract tag+sha, cites packs/rules)
                                │
                                ├──▶ export  ──▶ bundle: manifest + artefacts
                                └──◀── import ◀── verify every digest, then register
```

## What this contract is not

* **Not a tenant backup.** A bundle is the *company* (org shape, routines, rules,
  pins), never tenant data: a bundle that carries `customers/<t>/` is refused —
  a business leaving with another business's documents is not portability.
* **Not a second registry.** Versions stay in the artefacts themselves; the
  manifest records what was shipped, not what is allowed.
* **Not an upgrade mechanism.** Importing a bundle compiled against an older
  contract is allowed and recorded; importing one from a *newer* platform is
  refused, because the importer would silently drop what it cannot read.

## Inputs

### 1. The template

`companies/<id>/paperclip-company.json` — the compiled model, whose `contract`
is `{tag, sha}` and whose `cites` name the rule packs, flows and industry pack it
depends on, each with a version.

### 2. The artefacts

Everything the template cites, by `{kind, id, version, sha256}`. Kinds:
`pack` (an industry or domain pack), `flow`, `rule`, `org` (the org chart the
template was compiled from).

### 3. The platform pin

The contract tag the importing platform is pinned at. Used for one comparison and
one only: a bundle compiled against a **newer** contract cannot be imported.

## Outputs

One manifest — `schemas/portability-manifest.json`:

```json
{
  "version": 1, "contract": "company-portability@1",
  "company": "example-bank",
  "bundleId": "bundle-3f9a1c0d2e4b8a67",
  "createdAt": "2026-11-01T09:00:00.000Z",
  "template": {"path": "companies/example-bank/paperclip-company.json",
               "sha256": "…", "contract": {"tag": "contract-2026.11.1",
                                           "sha": "…"}},
  "artefacts": [
    {"kind": "pack", "id": "banking", "version": "2026.10.1", "sha256": "…"},
    {"kind": "rule", "id": "rules-v3", "version": "1.4.0", "sha256": "…"}
  ],
  "platform": {"contractTag": "contract-2026.11.3"}
}
```

| Field | Meaning |
|---|---|
| `bundleId` | `bundle-` + `sha256(company \| template.sha256 \| each artefact)` — content-addressed, so two exports of the same company are the same id and an import can say "I already have this" |
| `template.sha256` | the template's digest, so the importer verifies the file it received |
| `artefacts[]` | sorted by `kind, id`; each digest is of the artefact's own content |
| `platform.contractTag` | where it is going — recorded, never used to mutate the bundle |

The manifest is the artefact; the archive is only a carrier. An import that
verifies every digest and then registers the template is the whole operation.

## Errors (ordered, fail closed)

| Code | When | What the operator does |
|---|---|---|
| `E-PORT-01` | the manifest is malformed (shape, version, missing field, wrong id form) | fix the export; the importer does not guess |
| `E-PORT-02` | the template's contract pin is missing or malformed | fix the compile (`E-COMP-02`); a bundle without a pin is not portable |
| `E-PORT-03` | an artefact the template cites is absent from the bundle | re-export with the whole set; a partial bundle is a trap, not a portability feature |
| `E-PORT-04` | an artefact's digest does not match the manifest | stop: the bundle was altered in transit, or two versions were mixed |
| `E-PORT-05` | the bundle carries tenant data (`customers/…`) | strip it; company portability never moves a tenant's documents |
| `E-PORT-06` | the bundle was compiled against a **newer** contract than the platform | upgrade the platform first; the importer must not silently drop what it cannot read |
| `E-PORT-07` | a path in the manifest or the template is absolute, or carries a machine-specific root | make it relative to the repository root; an absolute path is a bundle that only works on its own machine |

The order is the graph: can we read it (`01`) → is it pinned (`02`) → is it
complete (`03`) → is it unchanged (`04`) → is it *company* (`05`) → can we read
its era (`06`) → does it travel (`07`).

## The arithmetic

```
bundleId = "bundle-" + sha256(
    company + "\n" + template.sha256 + "\n" + "\n".join(
        f"{a.kind}:{a.id}@{a.version}:{a.sha256}" for a in sorted(artefacts)))
```

The digest covers what was shipped, not where it went, so the same company
exported twice from the same state has one id — and a rollback is
"import bundle `<previous id>`".

**Diff** is manifest-to-manifest: an added artefact, a removed one, or a changed
digest, per `kind:id`. **Rollback** is an import of a previous bundle id; the
platform keeps the last N bundles it verified (a later step), and a rollback that
would move *forward* in contract pin is refused like any other.

## A worked example

`tests/fixtures/portability/case.valid.json` — company `example-bank`, template
pinned at `contract-2026.11.1`, two artefacts (`pack banking@2026.10.1`,
`rule rules-v3@1.4.0`), imported into a platform pinned at `contract-2026.11.3`:
a clean bundle with one finding — none, because the platform is **newer** than
the pin, which is allowed and recorded. The self-test then mutates it seven ways
(an unpinned template, a missing artefact, a wrong digest, tenant data, a stale
platform, an absolute path, a malformed manifest) and asserts each code appears.

## The module

| Call | Does |
|---|---|
| `portable.py export --company <id> [--template P] [--platform T] [--out DIR]` | builds the manifest from the checkout, writes `bundle.json` beside the template; any refusal means no bundle |
| `portable.py verify --bundle <path>` | the bundle's own integrity always; every artefact's digest against the checkout **where the checkout has the company** — an import target that does not have it yet is not a fault |
| `portable.py import --bundle <path> [--platform T]` | verify, then write the template — refusing to overwrite a compiled model that differs |
| `portable.py diff --left A --right B` | added, removed, changed per `kind:id` |
| `bin/paperclip-company --out <path> --bundle` | the compiler writes the template **and** its manifest, through the same module — a template written without one is not portable |

Two behaviours worth naming. **A repo-shipped artefact is versioned by the
contract pin it ships with** unless the file carries its own `version:` — the
repository is the version. And **the pin is resolved with `git cat-file`** where
the checkout is a git repository; where it is not, the manifest records what the
template declared and the import re-checks wherever git is available.

**Two modes of verification, because two questions are asked.** *Is this carrier
intact?* is the bundle's own integrity — its id and the template shipped beside
it — and that is what an import can check in a checkout that does not have the
company. *Does this checkout still match?* compares every artefact's digest, and
that is what CI runs on the source repository. Conflating them made an import into
a clean tree fail on the very artefacts it was delivering.

`--bundle` requires `--out` inside the repository: a manifest whose template sits
outside it would carry an absolute path, which is `E-PORT-07`.

## Where it will live

| Piece | Path (planned) |
|---|---|
| the gate | CI: a committed bundle re-verifies in `--self-test` (#324) |
| the gate | CI: a committed bundle re-verifies in `--self-test` (#324) |
| the surface | `bin/portable` — `export`, `import`, `diff`, `list` (#326) |
| the measure | `scripts/portability_metrics.py` — stale pins, unverifiable bundles (#328) |

## Not in this contract

* Incremental bundles — a bundle is whole or it is not a bundle.
* Migrating tenant data — that is the exit/export path (`docs/exit.md`), and it
  has its own approval.
* Signing the manifest beyond its own digest — the bundle id is integrity, not
  authenticity; a signature is a later contract.
