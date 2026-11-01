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
