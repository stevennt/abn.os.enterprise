# The Paperclip compiler — interface specification (issue #252)

The compiler turns one company model into the artefact Paperclip imports. This
page is the interface, written before the code: inputs, mapping, output, refusals
and exit codes. The implementation is PC1-02-02 (#253); the template shape is
`schemas/paperclip-company.json`.

```
companies/<id>/company.yaml ─┐
industries/<industry>/       ├─▶ compile ─▶ template.json ─▶ Paperclip import
(boundary contract version) ─┘                    │
                                                  └─ records boundary + contract pins
```

## Inputs (read-only, never executed)

| Input | Path | Used for |
|---|---|---|
| company model | `companies/<id>/company.yaml` | id, label, tenant, industry, contract pin, departments, adjoined flow/rule/pack ids |
| company org chart | `companies/<id>/org/org-chart.yaml` | units, parent links, heads, roles |
| industry manifest | `industries/<industry>/industry.yaml` | the industry the model adopts |
| flows | `industries/<industry>/flows/*.flow.yaml` | projects and routines; steps, `kind`, `level`, `uses_rule`, `uses_touchpoint` |
| rule packs | `industries/<industry>/rules/*.yaml` | each rule's `authority` (signed vs `pending-*`) |
| packs | `industries/<industry>/pack/`, `onboarding/…` | skills and evals to attach |
| boundary contract | `docs/core/paperclip-integration.md` | the `boundary` version the template records |

**Not inputs:** Paperclip state, tenant data, secrets, `customers/`. The compiler
never reads a credential and never calls a service.

## Mapping

| Model | Template | Rule |
|---|---|---|
| `company.yaml:id` / `label` | `company`, `label` | the id must match the directory |
| `contract.tag`, `contract.sha` | `contract` | copied verbatim; an unresolvable pin is a refusal, not a warning |
| boundary contract version | `boundary` | read from the contract page at compile time |
| org unit | `agents[].unit`, and one **project** per flow | a unit with no role produces no agent |
| role (unit × role) | `agents[]` | `id` = `<unit>-<role>` slug; `title` from the role id; `responsibility` counts the steps it owns; `reportsTo` = the lead agent of the nearest ancestor unit with agents, `null` for a unit with no such ancestor (a company may have several top-level units) |
| flow | `projects[]` | `id` = flow id, `sourceFlow` = flow file |
| step (`kind`, `level`, `uses_rule`, `uses_touchpoint`) | `routines[]` | one routine per non-human step; `level` copied; `autonomy` = `autonomous` only for `L3`+ and a signed rule, else `supervised` |
| rule `authority` | `routines[].ruleStatus` | `pending` if any cited rule starts with `pending-` |
| pack skill | `skills[]` | `id` + repo-relative path |
| evals | `evals[]` | `id` + path |
| files read | `source` | provenance, so the template can be re-derived |

Determinism: the same inputs produce byte-identical output (sorted arrays, no
timestamps in the template; the compile time is recorded outside it).

## Refusals (errors, before writing)

| Code | Refuse when | Message shape |
|---|---|---|
| `E-COMP-01` | `companies/<id>/company.yaml` missing or unreadable | `company <id>: no company.yaml` |
| `E-COMP-02` | the contract pin is missing, malformed, or does not resolve | `company <id>: contract pin <tag> does not resolve` |
| `E-COMP-03` | a flow names a role that no unit/role declares | `flow <f> step <s>: unknown role <r>` |
| `E-COMP-04` | a step is `kind: human` (or the flow is `authority: pending-review`) | `flow <f> step <s>: a human step cannot compile to a routine` |
| `E-COMP-05` | a step cites a `pending-*` rule and claims `autonomous` | `flow <f> step <s>: rule <r> is unreviewed; the routine must be supervised` |
| `E-COMP-06` | two agents/routines/projects/skills share an id | `duplicate id <id> in <collection>` |
| `E-COMP-07` | a cited pack skill or eval path does not exist | `flow <f>: skill <s> not found` |
| `E-COMP-08` | `reportsTo` names no agent, or no agent is a root | `agent <a>: reportsTo <b> does not resolve` / `no root agent` |
| `E-COMP-09` | the boundary version in the template and the contract page disagree | `boundary <v> != contract <w>` |
| `E-COMP-10` | the emitted template fails `schemas/paperclip-company.json` | `template invalid: <jsonschema message>` |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | compiled, or a template validated |
| `1` | the input is refused (a row above); nothing written |
| `2` | usage error |
| `3` | the template on disk does not validate (check mode) |

## Check mode

`scripts/check_paperclip_template.py --template <path>` validates a template
against the schema **and** the semantic rules the schema cannot express (one
root, resolvable `reportsTo`, unique ids, `autonomous` only at L3+ with signed
rules, boundary matches the contract page). `--self-test` mutates a valid
fixture and proves each refusal. That checker is the acceptance test the compiler
must satisfy before Paperclip import is attempted.

## Operation (the real path, #254)

A company opts in with one block in its model:

```yaml
paperclip:
  compile: true
```

`companies/company.schema.yaml` validates the block (a typo cannot silently
skip a company). Then:

| Command | Does |
|---|---|
| `bin/paperclip-company --all --check` | compiles every company; an **opted-in** refusal fails the run (exit 1), a non-opted model is reported with its code and skipped |
| `bin/paperclip-company --all --out-dir build/paperclip` | writes one `<company>.json` per compiled company |
| `bin/paperclip-company --company <id> --check` | one company, nothing written |

CI runs `--all --check`, so the compiler is the build's company gate, not a
script someone remembers to run. The reference model `example-bank` is not opted
in — see the input gap below — so the gate is green while the packs are
incomplete, and becomes meaningful the moment a model declares the intent.

## Walk through it (verbatim)

Every command below was run from the repository root; the output is copied, not
paraphrased. The fixture model (`tests/fixtures/paperclip-model`) is the safe
playground — it has nothing to do with a customer.

Prerequisites: `python3` with `pyyaml` and `jsonschema` (CI installs them), and
`git` (the compiler resolves the contract pin with `git cat-file`).

### 1. Compile one company — writes nothing

```
$ bin/paperclip-company --root tests/fixtures/paperclip-model --company demo --check
paperclip-company: demo compiles — 2 agents, 1 projects, 2 routines, paperclip-boundary@1.0
```

### 2. Look at the crew

```
$ bin/paperclip-company --root tests/fixtures/paperclip-model --company nested --show
nested — Nested Company
  boundary paperclip-boundary@1.0 · contract contract-2026.11.1 (a7baab409dce…)

agents (3)
  bank-ops-credit-officer          Credit officer           bank.ops         → —
  bank-ops-credit-analyst          Analyst                  bank.ops.credit  → bank-ops-credit-officer
  …
```

### 3. Render the sheet a reviewer reads

```
$ bin/paperclip-company --root tests/fixtures/paperclip-model --company demo --render
paperclip-company: rendered tests/fixtures/paperclip-model/companies/demo/crew.md — 2 agents, 2 routines
```

The file opens with the "generated … do not edit" comment, then the agent,
project and routine tables.

### 4. Compile everything that opted in — the CI gate

```
$ bin/paperclip-company --root tests/fixtures/paperclip-model --all --check
  demo: compiled — 2 agents, 2 routines
  nested: compiled — 3 agents, 3 routines
paperclip-company --all: 2/2 compiled
```

On the repository itself the same command reports the reference model as skipped
rather than failing — it has not opted in:

```
  example-bank: skip E-COMP-07 flow aml.str.filing step s3-investigate: rule(s) not defined by any pack: AML-INV-03
paperclip-company --all: 0/1 compiled
```

### 5. Prove the compiler itself

```
$ bin/paperclip-company --self-test
paperclip-company --self-test: fixture compiles deterministically, pending rules stay supervised, L2 never autonomous — OK
```

### When it refuses

```
$ bin/paperclip-company --root /tmp/broken --company demo --check
paperclip-company: E-COMP-07: flow demo.flow step s1-check: rule(s) not defined by any pack: GHOST-01
```

Exit code 1, and nothing is written.

| Code | Fix |
|---|---|
| `E-COMP-01` | the company's `company.yaml` or its `org.chart` file is missing, or the id does not match the directory |
| `E-COMP-02` | the contract pin is malformed or its sha is not a commit — use a released `contract-YYYY.MM.N` and its sha |
| `E-COMP-03` | a flow's department has no unit in the company chart, or a step has no `owner_role` — fix the model, not the compiler |
| `E-COMP-07` | a cited rule is defined by no pack, or a flow/skill/eval path is missing — add the rule to the pack, or fix the citation |
| `E-COMP-09` | the contract page carries no `paperclip-boundary@X.Y` — fix the contract, then re-run |
| `E-COMP-10` | the template fails the checker: read the S1–S8 message it prints (root, manager, ids, autonomy, paths, skills) |

## Surface (#257)

An operator should not have to read the JSON to see the crew.

| Command | Gives |
|---|---|
| `bin/paperclip-company --show --company <id>` | the crew on stdout: agents with their reporting lines, projects, routines with level, autonomy, rule status and the rules they cite |
| `bin/paperclip-company --render --company <id> [--out …]` | `companies/<id>/crew.md` — a reviewable sheet (generated; do not edit). Deterministic, model-only: no secrets and no tenant data |

A refused compile renders nothing: the command exits 1 with the `E-COMP` code.

**Who may see and act on it.** In this repository the reader is the operator or
the reviewer in the pull request. A change to `companies/` (including the
generated sheet) is gated by `.github/CODEOWNERS` and requires a review from the
delivery team; that gate only bites once branch protection requires code-owner
reviews, which is a repository setting, not a file.

The **tenant-admin** view of its own crew (scoped by role and unit, inside the
portal) is a platform task — PC2-14-01 (#372). It reads the same template, and
its permission check is OpenGate's role/unit ACL, not this repository's.

## Compile records (#256)

Every real run can leave evidence:

```
bin/paperclip-company --all --out-dir build/paperclip --record
```

appends one line per company to `companies/<company>/compiles.jsonl`:

```json
{"version": 1, "at": "2026-11-01T08:21:54Z", "company": "demo",
 "compiler": "paperclip-company@1", "boundary": "paperclip-boundary@1.0",
 "contract": {"tag": "contract-2026.11.1", "sha": "a7baab…"},
 "result": "compiled", "templateSha256": "d0bc3a…", "agents": 2, "routines": 2,
 "inputs": {"companies/demo/company.yaml": "6c4525…", "…": "…"}}
```

A refusal writes `result: "refused"` with the `E-COMP-NN` code and the message,
so a failed build is in the record too. `--check` never records (a dry run leaves
no trace). `scripts/validate_compiles.py` is the repo's check on those records:
required fields, outcome shapes, boundary and pin shapes, monotonic timestamps,
and the rule that **an opted-in company's latest record is `compiled`** — a stale
success cannot outlive a broken model.

## Known input gap (found while implementing, #253)

The compiler is stricter than `scripts/validate.py`: it refuses a step that cites
a rule **no pack defines** (E-COMP-07). On the reference model this bites —
`companies/example-bank` adopts two banking flows whose steps cite rules the
banking packs do not contain (for example `DISPUTE-*`, `NOTIFY-TPL-01`,
`AML-4EYES-04`), so that model does not compile today. That is a content gap in
the banking packs, not a compiler bug, and it is why the golden test compiles a
small consistent fixture (`tests/fixtures/paperclip-model`) instead. Fixing the
packs is a tier-3 task; until then the compiler refuses rather than invent a
rule status.

## Non-goals

- no model call inside the compiler (deterministic mapping; judgement belongs to
  the model, not the build);
- no partial template (a refusal writes nothing);
- no secret or tenant-data read;
- no import into Paperclip from here (that is the operator/Paperclip step).
