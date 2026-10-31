# Pack contract mapping (issue #127)

`metamodel/pack.schema.yaml` is the L2-content contract. It is **ours**; OpenGate
consumes it. Every field below was verified against
`abn.platform.opengate/gateway/resolve.py` (`load_roles`, `skill_version`,
`validate_pack`) and against the five real packs in that repo.

## roles.yaml

| Field | Type | Required | Read by resolver | Notes |
|---|---|---|---|---|
| `roles` | map | yes | `load_roles()` raises if absent | key = role id, must match `^[a-z][a-z0-9-]*$` |
| `roles.<id>.position` | `maker\|checker\|orchestrator` | yes | `docs/roles.md` triad | checkers must not invoke others |
| `roles.<id>.template` | `agents/<id>.md` | yes | `validate_pack` checks file + frontmatter | path relative to pack dir |
| `roles.<id>.skills_required` | array | no | `validate_pack` checks skill dirs | `base-*` resolves to the shared base pack |
| `roles.<id>.rubric` | string | no | checker pins exactly one rubric | must be a skill in the pack |
| `roles.<id>.tools_allow` | array | no | `validate_pack` checks `qc/tools/<t>.py` | qc tools stay in OpenGate |
| `roles.<id>.may_invoke` | array | no | resolver reads | must be empty for `checker` |
| `roles.<id>.harness_allow` | array | no | enabled-harness check | optional |
| `roles.<id>.note` | string | no | human only | prose; cite rule versions here |

## SKILL.md frontmatter

| Field | Type | Required | Read by resolver | Notes |
|---|---|---|---|---|
| `name` | string | yes | dir/skill lookup | should equal the skill directory name |
| `version` | semver `x.y.z` | **yes** | `skill_version()` raises if missing at release | strict semver |
| `description` | string ≥10 | yes | product listing | |
| `license` | string | no | display | |
| `compatibility` | string | no | display | `opencode` today |
| `metadata.domain` | string | no | registry grouping | |
| `metadata.qc_id` | `QC-<AREA>-NNN` | no | gate script linkage | gate script itself stays in OpenGate |

## agents/<role>.md frontmatter

| Field | Type | Required | Read by resolver | Notes |
|---|---|---|---|---|
| `description` | string ≥10 | yes | display | |
| `mode` | `primary\|subagent\|all` | yes | engine | |
| `temperature` | number 0–1 | yes | engine | |
| `steps` | int ≥1 | yes | engine step cap | |
| `permission` | map | no | engine | value = decision **or** pattern→decision map |

### Permission value shape (found by testing real packs)

Real packs use the map form to allow one command family while denying the rest:

```yaml
permission:
  edit: deny
  bash: { "*": deny, qc_schema: allow, qc_citation: allow }
  skill: allow
```

The schema accepts both forms (`$defs/permissionValue`). This was not guessed — the
`legal` pack failed a narrower schema, which is why the schema was widened.

## What deliberately stays in OpenGate

- `qc/tools/*.py` gate scripts (platform tooling; `tools_allow` points at them).
- `gateway/resolve.py` (the consumer).
- `domains/base/` shared skills (`base-*` prefix is allowed by the pack lint).

## Verified against real packs (2026-10-31)

| Pack | Result |
|---|---|
| banking | OK (3 roles, 1 skill) |
| legal | OK (4 roles, 4 skills) |
| medical | OK (3 roles, 3 skills) |
| civil-protection | OK (2 roles, 3 skills) |
| defense-ops | **RED** — `skills/defense-ops-triage/SKILL.md` frontmatter has an unquoted `description: TODO(EXPERT): ...` (colon in scalar). Reported to OpenGate; the pack is classified-tier and is not imported here. |

## Validating

```
python scripts/pack_lint.py                     # every industries/*/pack
python scripts/pack_lint.py --path <dir>        # any pack dir (used to pre-check OpenGate)
python scripts/pack_lint.py --self-test         # green fixture + broken fixture
```

## First tenant pack set (issue #177)

Which packs the first enterprise tenant gets, and **who masters each one**. One
pack, one owner: a pack is either in OpenGate `domains/` (product code, shipped
with the platform) or a pinned bundle from this repo (industry content, shipped
as `<id>-pack-<version>`).

| Pack | Owner (master) | Where | In tenant #1's set |
|---|---|---|---|
| `base` | OpenGate | `domains/base` | yes — always on |
| `business` | OpenGate | `domains/business` | yes — ops department |
| `hr` | OpenGate | `domains/hr` | yes — HR department |
| `documents` | OpenGate | `domains/documents` | yes — documents department |
| `marketing` | OpenGate | `domains/marketing` | yes — marketing department |
| `banking` | **this repo** | `industries/banking/pack` (`status: active`) | no — industry pack, opt-in |
| `legal` | **this repo** | `industries/legal/pack` (`status: draft`) | no — industry pack, opt-in |

The set follows the transcript that seeded loop 5: a company with business, HR,
documents and marketing departments. It is deliberately **four department packs
plus base** — an industry pack is added when the tenant's practice needs it, not
by default.

The machine-readable copy of this table lives in OpenGate at
`onboarding/pack-set.json`, and `tests/test_pack_set.py` enforces the OpenGate
half: every OpenGate-owned pack must be registered in `opengate.json` and exist
on disk, and no enterprise-owned pack may also be registered there — with one
recorded exception, below.

### The rule

1. **Department packs are product**, so they live in OpenGate `domains/` and
   ship with the platform version.
2. **Industry packs are content**, so they live here under `industries/<id>/pack`
   and travel as a signed bundle that a tenant pins by tag
   (`customers/<t>/domains.json`, see #176). This repo is where the citations,
   rules and sign-offs for an industry can be reviewed together.
3. Adding a pack means picking one of those two homes. A pack that needs both a
   product surface and industry content is split, not copied.

### Known violation, tracked

`legal` is mastered in **two** places today: `industries/legal/pack/` (a port of
the OpenGate pack, `status: draft` per #131) and OpenGate's `domains/legal/`
(`source: in-repo`, enabled). `banking` shows the intended end state — this repo
masters it and OpenGate consumes it as a pinned bundle with no in-repo copy.

Retiring the duplicate is a migration, not a doc edit: publish `legal` as a
`legal-pack-<version>` bundle, switch `domains.legal` to `source: bundle`, and
remove the in-repo tree (the same three steps #137 took for banking). Tracked
as **#241**; until it lands, `pack-set.json` records `legal` in
`known_duplicates`, and the OpenGate test fails if that list ever grows — and
again once it is emptied before the migration is done.

`medical`, `civil-protection` and `defense-ops` remain OpenGate-owned: no
industry copy exists here, so there is no duplication to resolve yet.
