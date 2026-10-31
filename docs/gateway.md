# Axum gateway pattern v1.0 (issue #54) — one front door, RLS-safe identity

Reuses the proven `axum.abnasia.org` session-exchange pattern (see house
Supabase/PostgREST rules): clients never hold service keys; the gateway mints
short-lived scoped JWTs per call.

## Auth flow

```
client session (cookie/OIDC)
  -> POST /session/exchange {intent, instance_id?}
  -> gateway verifies session, checks (role, relation, object) via B17 policy
  -> mints JWT: {sub, role, scope:[named permissions], exp:5m, aud:downstream}
  -> downstream (PostgREST/Temporal/Camunda/Frappe) verifies JWT + enforces RLS
```

Scopes are minimal per intent (e.g. `loan:read:INST-1`, never `loan:*`).
`POSTGREST_URL`-style handoff: clients learn downstream endpoints from the gateway,
never hardcoded — moving services needs no app update.

## Threat note — no JWT-stripping proxies

- Kong/routes carrying user JWTs are **add-only**: a `request-transformer` with
  `replace:` on `Authorization` silently breaks RLS and attribution (lived outage 2026-10-05).
- Every hop forwards the original user JWT untouched; service-to-service auth uses
  a SEPARATE header (`X-Service-Token`), never by replacing `Authorization`.
- Downstream must reject calls with missing/unscoped JWTs (fail-closed); anonymous
  paths are explicit allowlist entries, not accidents.
- Secret rotation (JWT secret, service tokens) follows the SOPS-vault flow with
  rollout restart; live-vs-file mismatches page immediately (same 2026-10-05 lesson).
