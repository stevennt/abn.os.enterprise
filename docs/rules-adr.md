# Rules ADR v1.0 (issue #41) — where rules live, how flows reference them

## Decision

- **DMN for business decision tables** (credit grids, fee ladders, triage matrices):
  analysts own them, versioned, rendered from `rule.schema.yaml`. Engine evaluates
  DMN at runtime (Camunda DMN or a DMN library beside Temporal — F51 decides which).
- **OPA/Rego for technical policy** (authz enforcement, deployment guardrails):
  engineers own it; the OpenFGA model (B17) is its runtime cousin.
- **One interchange format:** every rule — DMN or Rego — is registered as a
  `rule.schema.yaml` row (id, authority, version, inputs, table, effect). Flows never
  embed logic; they cite `RULE-ID@version`. No rule in code, no rule in chat.

## Sample DMN table (SBV-DSTI-04 — unsecured retail)

| # | dsti | income_verified | product | → decision |
|---|---|---|---|---|
| 1 | ≤ 0.40 | yes | unsecured | APPROVE (score decides limit) |
| 2 | 0.40 – 0.60 | yes | unsecured | APPROVE with manager review |
| 3 | > 0.60 | * | unsecured | REVIEW (human, cannot auto-approve) |
| 4 | * | no | unsecured | REVIEW (verify income first) |

Hit policy: first-match, ordered. The `*` rows ensure total coverage (no gaps);
CI asserts coverage + no overlap when rule packs land (E42–E45).

## Rule-reference convention

- In flows: `uses_rule: [SBV-DSTI-04]` pins by release (the release resolves the version;
  see A04/A06). In audit: full `SBV-DSTI-04@2026-10-01`.
- Rule ids: `<DOMAIN>-<TOPIC>-<NN>` (e.g. `AML-SCREEN-02`, `CREDIT-GRID-11`).
- Renaming a rule = new id + alias row; old id serves until sunset (never silent break).
