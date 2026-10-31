# Versioning & migration policy v1.0 (issue #6)

All model artifacts carry semver `version`. The bank never stops, so
**in-flight instances always finish on the version they started with** —
a new version only affects instances created after cutover.

## MAJOR / MINOR / PATCH per artifact

| Artifact | PATCH (auto-roll) | MINOR (dual-run) | MAJOR (migrate + sunset) |
|---|---|---|---|
| Process | SLA minutes, texts, owner display names | new step (with owner + on_fail), new optional input/output, new KPI | remove/rename step, change step kind, new required input, reorder decision meaning |
| Rule | threshold typo fix with same effect, clarifying text | new row that only narrows REVIEW→APPROVE paths, new input with default | any row flipping APPROVE→DECLINE semantics, removed input, authority change |
| Event | description, example, retention increase | new optional payload field | removed/renamed field, new required field, idempotency-key change |
| Org / Touchpoint / Audit | headcount plan, channel display text | new role, new channel fallback | removed role, SoD-relevant change, envelope field change |

PATCH rolls forward automatically. MINOR and MAJOR never auto-roll.

## Dual-run window (MINOR)

- Old minor keeps serving until cutover date (default 14 days, in the release note).
- New instances after cutover take the new minor; in-flight ones finish old.
- Router holds both rows during the window; dashboards split metrics by version.
- Rollback = flip the default row back (one rule PR, no code deploy).

## Migration (MAJOR)

- Release note states: sunset date of old major (min 30 days), affected
  instances estimate, and the migration map (old step → new step).
- After sunset, routes to the old major resolve `VERSION_RETIRED` → dead-letter (A04).
- `scripts/migrate_check.py` classifies any process diff as PATCH/MINOR/MAJOR
  and prints the required action; CI runs it on the loan-flow fixtures.

## In-flight rules

1. Instance pins `(process id, full version)` at creation.
2. Rule rows are read at pinned rule version, never "latest".
3. A version with live instances cannot be deleted, only sunset.
