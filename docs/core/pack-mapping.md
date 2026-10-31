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
