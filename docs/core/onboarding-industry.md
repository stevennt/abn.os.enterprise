# Onboarding an industry (issue #138)

One day, one command, and every CI check green before you write a line of domain
content. The scaffolder exists because growth will be by copy-paste and copy-paste
is where duplicated ids, missing traces and asserted-but-unverified claims come from.

```
bin/new-industry <id> --label "..." [--units a,b] [--with-pack] [--dry-run]
```

## The checklist — one line per CI check

Run in this order. Each maps to a check that runs in `.github/workflows/validate.yml`.

| # | Command | What it proves |
|---|---|---|
| 1 | `python scripts/run_all_traces.py` | every flow gets a trace, chains verify |
| 2 | `python scripts/validate.py` | manifest valid, org index==full, catalog non-empty, flow schema, trace chain, tier hosted |
| 3 | `python scripts/rule_lint.py` | every rule has when/then, no duplicate `when`, wildcard coverage row |
| 4 | `python scripts/pack_lint.py` | pack schema + cross-file refs (only if `--with-pack`) |
| 5 | `python scripts/pack_claim_scan.py --industry <id>` | no substantive claim without a cite or `placeholder:` |
| 6 | `python scripts/cross_industry.py` | rule/flow/event ids unique across ALL industries, no cross-refs |
| 7 | `python scripts/no_hardcoded_paths.py` | tooling did not hardcode your industry |
| 8 | `python scripts/tier_guard.py` | tier is `public`/`commercial`; restricted/classified goes to a split repo |
| 9 | `bin/tag-industry <id> --kind policy --push` | the release exists and resolves |
| 10 | `python bin/verify-industry-tags.py` | both declared streams resolve (pack stream only once `pack.status != absent`) |
| 11 | `bin/build-pack <id>` then `--verify` | the pack travels as a verifiable artifact (only with a pack) |
| 12 | `python scripts/validate_company.py` | every `companies/*/company.yaml` validates and its contract pin resolves (`docs/core/onboarding-company.md`) |
| 13 | `python bin/tag-list --check` | every release tag follows its stream's `YYYY.MM.N` shape; legacy tags are listed, not silently pinned (`docs/core/tag-sync.md`) |

## Documented dry-run (2026-10-31)

```
$ bin/new-industry logistics --label "Logistics operations" \
      --units dispatch,warehouse --with-pack --dry-run
would write industries/logistics/pack/agents/dispatch-maker.md
would write industries/logistics/pack/roles.yaml
would write industries/logistics/pack/skills/logistics-skill/SKILL.md
would write industries/logistics/rules/logistics-baseline-pack.yaml
dry-run: 14 files planned, nothing written
```

Real run, then every check, in the order above:

```
$ bin/new-industry logistics --label "Logistics operations" --units dispatch,warehouse --with-pack
... 14 files written + next steps

$ python scripts/run_all_traces.py      PASS   (trace generated for logistics.primary)
$ python scripts/validate.py            PASS
$ python scripts/rule_lint.py           PASS
$ python scripts/pack_lint.py           PASS   (3/3 packs green)
$ python scripts/pack_claim_scan.py --industry logistics   PASS
$ python scripts/cross_industry.py      PASS
$ python scripts/no_hardcoded_paths.py  PASS
$ python scripts/tier_guard.py          PASS
```

And the repo reporting the new industry without any other edit:

```
$ python scripts/industrylib.py
banking   tier=commercial flows=15 rules= 4 pack=active
legal     tier=commercial flows= 1 rules= 2 pack=draft
logistics tier=commercial flows= 1 rules= 1 pack=draft
3 industries, 17 flows, 7 rule files

$ python scripts/validate.py | grep -E "industries:|catalog: logistics|org: logistics|trace:"
catalog: logistics 1 processes indexed — OK
org: logistics 2 units, index==full, headcounts match (plan 6) — OK
industries: 3 manifests valid — banking(commercial,15 flows), legal(commercial,1 flows), logistics(commercial,1 flows)
trace: 17 traces, steps in order, chains verify, owner/rule/SLA/fail-path — OK
```

The scratch industry was then deleted (it was a rehearsal, not a decision to enter
logistics). Nothing else in the repo needed editing to add or remove it — that is the
actual test of multi-industry support.

## What the scaffold gives you, and what it does not

**Gives:** manifest with `tag_stream`, org index + one unit per `--units`, a
process catalog, a structural rule pack (`authority: pending-review`), an end-to-end
flow (intake → AI draft → human check → release), one event example, a `status.md`
and with `--with-pack`: roles, two agent templates, one skill, `MIGRATION.md` with the
`### Migration` line consumers require.

**Does not give:** domain numbers, thresholds, legal/professional statements, client
names. Rule rows say `pending-review`; the pack skill carries a `placeholder:` block.
`pack_claim_scan.py` fails the build if you assert substance without a same-repo cite.

## Naming rules the scaffolder enforces for you

- rule ids `<ID-UPPER>-NN`, flow `<id>.primary`, event `<id>.primary.requested` —
  prefixed by the industry so `cross_industry.py` cannot find a collision
- `tag_stream` prefixes must start with `<id>-` (checked by `verify-industry-tags.py`)
- tier must be hosted here; `restricted`/`classified` is refused by `tier_guard.py`

## After the scaffold

1. Name a reviewer in `industries/<id>/docs/status.md`.
2. Replace `authority: pending-review` row by row as each is signed, bumping
   `version` on the pack.
3. Add flows; every step needs owner + rule + SLA + on_fail (validator enforces).
4. When `pack.status` becomes `active`, tag `--kind pack` and build the bundle the
   consumer fetches (`docs/core/bundles.md`).

## Appendix — every other CI check, and why the scaffold does not touch it

The table above is the industry path. These run in CI too; they are shared
assurance, so a new industry inherits them rather than exercising them:

| Check | What it covers | Why an industry does not edit it |
|---|---|---|
| `scripts/audit_chain.py --demo` | audit hash chain + tamper detection | shared contract, exercised by the loan trace |
| `scripts/authz_check.py` | OpenFGA role→permission samples | shared (`engine/authz.fga`) |
| `scripts/inbox_demo.py` | human task escalation | shared pattern |
| `scripts/dlq_drill.py` | dead-letter triage → replay | shared router behaviour |
| `scripts/money_drill.py` | 10k-transfer duplicate drill | money flows only; industries without money are unaffected |
| `scripts/sod_mine.py` | SoD mining queries on a fixture | shared SoD policy (`docs/core/sod.md`) |
| `scripts/chaos_exec.py` | crash recovery + lag storm on the demo flow | picks the demo flow via `industrylib.demo_paths()` |
| `scripts/render_explainer.py` | decision explainer grounding | shared template (`docs/core/explainer.md`) |
| `scripts/pilot0_rehearsal.py` | pilot checklist rehearsal | programme-level, not per industry |
| `scripts/risk_pack.py` | 7-section governance pack | programme-level |
| `scripts/promo_pack.py` | promotion evidence pack | programme-level; blocks on human sign-off |
| `scripts/test_bundle.py` | bundle determinism + tamper refusal | packaging, not content |
| `scripts/eval_harness.py` | AI contract + golden suites | only industries with `ai/*.contract.yaml` |
| `scripts/export_bpmn.py` | flow → BPMN export | automatically includes new flows |
| `scripts/pii_scan.py` | bare-CCCD scanner | repo-wide |
| `scripts/gen_goldens.py` | golden regeneration determinism | banking evals today |
| `scripts/gen_sandbox.py` | synthetic dataset determinism | programme-level |
| `scripts/migrate_check.py` | semver classification on flow diffs | applies to every flow edit |
| `scripts/industrylib.py` | inventory (also a smoke test) | lists your industry automatically |
| `frappe/test_os_task.py` | inbox DocType logic | shared runtime |
| `bin/verify-industry-tags.py` | both tag streams resolve | **your industry must pass this** |
| `scripts/pack_cite_check.py` | pack cites resolve to same-repo rules/flows | only with `--with-pack` |
| `scripts/run_trace.py` | single-flow trace regeneration | the demo flow; `run_all_traces.py` covers yours |
| `scripts/docs_link_check.py` | front-page docs point at real paths | applies to shared docs, not to your industry folder |
| `scripts/loop_ledger_check.py` | the loop review matches its ledger, and recorded commits exist | programme-level; `--repos <path>` also checks the platform repo |
| `scripts/check_plane_boundary.py` | the model plane carries no work state, secrets or tenant policy | programme-level (ADR-002); `--self-test` proves each rule bites |
| `scripts/test_plane_contract.py` | the boundary pages still say what they said: decisions, seams, owners, findings, ADR, index | programme-level (ADR-002); `--self-test` mutates the pages and proves red |
| `scripts/audit_boundary.py` | the boundary audit: runs its checks and records exit + output digest + guarded file digests; `--verify` re-runs and compares | programme-level (ADR-002); not a CI gate — it produces the evidence file |
| `scripts/check_paperclip_template.py` | the compiled company template: schema, one root, resolvable managers, unique ids, autonomy only on signed rules | programme-level (ADR-002); `--self-test` mutates a fixture and proves each refusal |
| `scripts/pack_rule_drift.py` | prose thresholds match the rule tables | **your pack must pass this if it states numbers** |
| `scripts/test_drift.py` | proves the drift check still bites | shared assurance |

Kept in sync by `scripts/playbook_sync.py`: CI fails if the workflow runs a script
the playbook never mentions, so this appendix cannot silently rot.
