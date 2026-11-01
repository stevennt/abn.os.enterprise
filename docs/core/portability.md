# Company portability — templates, pins, and a bundle that proves itself (contract `company-portability@1`)

**Status:** interface specified (#322), implemented in `scripts/portable.py`
(#323), wired into the compiler (#324), tested (#325), recorded (#326),
surfaced (#327), documented (#328), hardened (#329), measured (#330); the demo
step follows (#331). **Shape:** `schemas/portability-manifest.json`. **Checker:**
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
| `E-PORT-08` | a rollback would overwrite a live compiled model that differs, and `--force` was not given | pass `--force` if that is what you mean; a rollback is deliberate and it is logged |

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

## The runbook

[portability-walkthrough.md](portability-walkthrough.md) is the generated,
end-to-end transcript: one company exported, recorded, re-recorded silently,
listed, shown, verified, diffed, imported into a clean checkout, refused three
ways (a newer contract, tenant data, a rollback without `--force`), rolled back
with `--force`, and checked. It is generated by
`scripts/portable_walkthrough.py`, and
`python scripts/portable_walkthrough.py --check` regenerates and diffs it — a
stale transcript turns the suite red instead of quietly ageing.

## The operator surface (#327)

```
$ bin/portable export   --company <id> [--template P] [--platform T] [--out DIR]
$ bin/portable record   --company <id> [--template P] [--platform T]
$ bin/portable bundles  --company <id> [--limit N]
$ bin/portable show     --company <id> --bundle <id>
$ bin/portable import   --bundle <path> [--platform T]
$ bin/portable rollback --company <id> --to <id> [--force]
$ bin/portable verify   --bundle <path>
$ bin/portable diff     --left A --right B
$ bin/portable check
```

The binary is a surface over `scripts/portable.py`, never a second implementation.
Its lines say what an operator needs and nothing else:

```
$ bin/portable export --company acme --platform contract-2026.11.3
acme  bundle-7428f5cbc337d64d  3 artefact(s)  pinned at contract-2026.11.1  → contract-2026.11.3
$ bin/portable record …
acme  bundle-7428f5cbc337d64d  stored at companies/acme/bundles/bundle-7428f5cbc337d64d
$ bin/portable record …            # again
acme  bundle-7428f5cbc337d64d  unchanged (already stored)
```

`--json` prints the payload for machines, and every refusal exits 1 with its code
and fix on stderr. **There is no actor model here** — the tenant-facing gate lives
in the platform; in this repository the operator has the checkout, and what the
surface owes them is an explicit action and a refusal they can act on.

## Hardening (#329)

A bundle is **untrusted input**: it arrives from another checkout, and `import`
writes the template where the manifest says. The edges are attacker-shaped, and
each refusal names its code and fix:

| Failure mode | Refusal | What it protects |
|---|---|---|
| the company id is a path (`..`, a separator, absolute, empty) | `E-PORT-01 invalid company id` | `companies/<id>/…` cannot escape its root |
| the bundle id is not `bundle-<16 hex>` | `E-PORT-01 invalid bundle id` | a carrier is named by content, never by a path |
| a manifest's template path is not `companies/<company>/<name>.json` | `E-PORT-07` | **the manifest is untrusted**: import and rollback write where it says, so a path that climbs out is refused before anything is written |
| the template, a carrier or a manifest is a symbolic link | `E-PORT-04` (the link target is named) | a link would make the checkout read — or write — somewhere else |
| a second writer holds the store's lock | `E-PORT-01 … the store is busy` | two records cannot interleave a carrier and its log row |
| a log row names an unknown action or a missing carrier | `E-PORT-01` / `E-PORT-03` from `check` | the log is a record, not a scratch file |

**Two of these are worth more than the others.** The manifest path is the one that
matters most: `import` and `rollback` copy a file *to a path the bundle chooses*,
so an unvalidated path is a write primitive from a bundle into the checkout — now
refused against a strict `companies/<company>/<name>.json` pattern. And the carrier
is written **atomically** (built beside its name, moved in one step), because a
refused or crashed record previously left a half-written carrier that failed
integrity forever — a bug the hardening test found by trying one.

## The record (#326)

```
companies/<id>/bundles/<bundleId>/bundle.json              the carrier
companies/<id>/bundles/<bundleId>/paperclip-company.json   and its template
companies/<id>/bundles/index.jsonl                         one row per action
```

`portable.py record` stores the carrier under its own id and appends one row
(`bundleId`, template digest, artefact count, `action: export|rollback`). Three
rules make it a record rather than a cache:

- **the id is the name.** Recording the same state twice is a silent no-op, and a
  *different* carrier at an existing id is `E-PORT-04` — history that can be
  rewritten is not history.
- **a rollback is deliberate.** `rollback --to <id>` imports a stored carrier; it
  refuses to overwrite a live template that differs unless `--force`
  (`E-PORT-08`), and either way it appends a `rollback` row naming what it
  restored.
- **`verify-bundles` checks the store**, not just one file: every carrier against
  its own manifest, the directory named by its bundle id, and every log row naming
  a carrier that exists. CI runs it over the committed store.

The contract's own word for this is *rollback is an import of a previous bundle
id* — which is now literal: the id names the directory, the directory holds the
carrier, and the carrier is what `import` consumes.

## The conformance matrix

`scripts/test_portability_matrix.py` runs 18 cases against the **implementation**
(not only the oracle), each asserting which code fires **and why**:

| Group | Cases |
|---|---|
| the pin | a template with no pin; a pin whose sha is not a commit in the repository |
| completeness | a cited file the checkout does not have |
| scope | a cited tenant file; a cited absolute path |
| era | a platform older than the pin |
| the carrier | a manifest that is not JSON; another contract; an id that no longer matches its contents; a shipped template whose digest is wrong; a bundle with no template beside it |
| the checkout | an artefact tampered after export |
| import | over a different compiled model; a bundle newer than the platform |
| positives | a clean export; two exports of one state share an id; a newer platform accepts an older bundle; the id agrees with the oracle's own |

The last line is the invariant: **every code in the matrix has a case**, and the
four positives keep a checker that refuses everything from passing.

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
