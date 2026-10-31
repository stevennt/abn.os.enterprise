# Onboarding a company (issue #231)

A company model is one **legal entity's operating model** inside an OpenGate
tenant, built from this repo's contract — the counterpart of
`docs/core/onboarding-industry.md`, which models an industry. One command
scaffolds it; the checks prove it before any content is real.

```
bin/new-company <id> --tenant <tenant> --label "..." [--units retail,risk]
                     [--industry banking] [--entity <id>] [--dry-run] [--force]
```

It writes the minimum that passes every check:

```
companies/<id>/
  company.yaml          the model: tenant, entity, industry, contract pin,
                        departments (each mapped to an org unit), flows/rules/packs
  org/org-chart.yaml    units + parent_id + headcount_plan (industry org shape)
  docs/status.md        what is real and what is still a scaffold
```

## The checklist — one line per check that can fail

| # | Command | What it proves |
|---|---|---|
| 1 | `yamllint companies/` | the manifests and org charts are well-formed YAML (house style) |
| 2 | `python scripts/validate_company.py` | schema, id == directory, industry exists, departments resolve to org units, adopted flows/rule packs exist, contract pin resolves |
| 3 | `python scripts/validate_company.py --self-test` | the validator still goes red on a broken model (unknown industry/flow/unit, tag mismatch, missing departments) |
| 4 | `python scripts/no_hardcoded_paths.py` | the tooling does not hardcode a company or an industry path |
| 5 | `python scripts/playbook_sync.py` | this playbook still names every script CI runs |
| 6 | `python scripts/validate.py` | the industry the company adopts is still valid (company models do not replace industry validation) |

CI runs 1-3 on every push; `companies/example-bank/` is the reference model that
keeps the check meaningful.

## The contract pin

Every model declares the contract release it was built from:

```yaml
contract:
  repo: abn.os.enterprise
  tag: contract-2026.11.1
  sha: a7baab409dce013bd296b57aafc500565b878dfa
```

- The **tag** is a release tag (`<stream>-YYYY.MM.N`, `docs/core/release.md`):
  create one with `git tag -a contract-YYYY.MM.N -m "contract release"` and push
  it. `bin/new-company` picks the newest local `contract-*` tag.
- The **sha** is what an audit needs: tags can be moved, a commit cannot. The
  validator checks the sha is a real commit and, when the tag resolves locally
  or on origin, that it points at **that** sha.
- Offline (or before the tag is pushed) the tag lookup reports `UNKNOWN` as a
  warning — it never claims a pin resolves when it cannot see it.

## Documented dry-run

```
$ bin/new-company example-bank --tenant abnasia --label "Example Bank" \
      --units retail,risk,compliance --dry-run
would write companies/example-bank/company.yaml
would write companies/example-bank/org/org-chart.yaml
would write companies/example-bank/docs/status.md
dry-run: 3 files planned, nothing written
```

Real run, then the checks:

```
$ bin/new-company example-bank --tenant abnasia --label "Example Bank" \
      --units retail,risk,compliance
companies/example-bank: 3 files written, pinned to contract-2026.11.1 (a7baab409dce)

$ python scripts/validate_company.py
company example-bank: OK
companies: 1 model(s), 0 failure(s), 0 warning(s)
```

## Splitting a company into its own repo

A company that needs its own lifecycle (or a restricted tier) copies the folder
out; the pin makes the copy reproducible:

```bash
# from this repo, at the pinned commit
git archive --format=tar <sha> metamodel docs/core | tar -x -C ../company-x
cp -R companies/<id>/. ../company-x/
# the new repo keeps company.yaml unchanged: contract.tag + contract.sha still
# name the release it was built from, and its CI runs a vendored copies of
# scripts/validate_company.py (same schema, same checks)
```

The rule from `docs/core/confidentiality.md` still holds: a `restricted` /
`classified` company never lives in this repo — the folder is the template, the
split repo is where the content goes.

## Limits

- **Structure, not commercial data.** Tax ids, SSO and contacts are the
  commercial onboarding pack (`docs/core/commercial-onboarding.md`); this model
  is org, departments, adopted flows and the contract pin.
- **No credentials, no customer content.** Units, counts and references only.
- **A company can adopt less than its industry ships** (`flows: []` and
  `rules: []` mean "all of it"; a list means exactly those ids, and the
  validator proves each one exists).
