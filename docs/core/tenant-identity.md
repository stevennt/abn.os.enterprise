# Tenant identity — people, agents, and the principal (contract `tenant-identity@1`)

**Status:** interface specified (issue #272); implementation is PC1-04-02…10
(#273–#281). **Shape:** `schemas/tenant-identity.json`. **Checker:**
`scripts/check_identity_spec.py` (CI, with `--self-test`). **Boundary:** ADR-002,
`docs/core/paperclip-integration.md` D4.

This page fixes the identity seam before code: **who acts, in which tenant and
company, with which role and unit, and whether they are a person or an agent.**
One identity tree, one mapping, one refusal vocabulary.

```
ONEID assertion ──▶ identity.resolve ──▶ principal ──▶ run context ──▶ Paperclip run
                         ▲                    ▲
      accounts.json ─────┘                    └───── org chart (role posted at unit)
```

## Inputs

### 1. The ONEID assertion (a person)

ONEID is the only human identity (ADR-002 D4). It is an OIDC provider:

| Piece | Value |
|---|---|
| issuer | `https://axum.abnasia.org/oneid/oidc` (per tenant in `profile.json` → `identity.issuer`; default ONEID) |
| discovery | `<issuer>/.well-known/openid-configuration` |
| browser authorize | `<issuer>/browser` — the sign-in page; the API-first `/authorize` stays for machine clients |
| token | `<issuer>/token` — authorization-code + PKCE (**S256 required** for public clients) |
| keys | `<issuer>/jwks.json` — RS256; the token's `kid` must exist there |
| userinfo | `<issuer>/userinfo` — authoritative for `email_verified` |
| scopes | `openid`, `profile`, `email`, `offline_access` |

The ID token claims this contract consumes, and no others:

| Claim | Rule |
|---|---|
| `iss` | exactly the tenant's configured issuer |
| `aud` | the tenant's registered `client_id` |
| `sub` | ONEID's stable subject (sticky id) — the identity anchor |
| `exp` / `iat` | `exp` in the future; clock skew tolerated ±60 s |
| `nonce` | equals the nonce this login started with (reject a replay) |
| `auth_time` | present; a session older than the tenant's `identity.maxAgeSeconds` (default 12 h) forces re-authentication |
| `email`, `email_verified` | carried for display and invite matching; `email_verified` must be `true` to be shown as verified |
| `name`, `preferred_username` | display only |

Signature and algorithm are checked against the JWKS; `alg: none` and HMAC
tokens are refused. The assertion is never trusted for **authorisation** — it
says *who*, never *what*.

### 2. The account store (`customers/<tenant>/accounts.json`)

One store for people and agents (schema above). Unchanged top level
(`version: 1`, `accounts[]`); rows gain identity fields:

| Field | Person | Agent |
|---|---|---|
| `id`, `name`, `role`, `unit` | required | required |
| `company` | group tenants only: which chart posts the role | same |
| `kind` | `person` (or absent, for existing stores) | `agent` |
| `status` | `active` (or absent) / `disabled` | **required**: `active` / `disabled` |
| `credential` and/or `sso` | at least one | **forbidden** |
| `owner` | — | **required**: a person account in the same tenant |
| `purpose` | — | **required**: one sentence a reviewer can check |

An agent is an identity without a login: no password, no SSO binding, no
session. It acts only through a signed run pass (`paperclip-adapter@1`), and
every action names `owner` as the responsible person.

### 3. The org chart

The role and unit must be posted: the unit exists on the tenant's chart (or, for
a group, the company named by the account), and `role` appears in that unit's
`portalRoles`. Unit ids are local to a company (#148) — in a group, ambiguity is
refused, never guessed.

## Outputs

### The principal (what every surface resolves to)

```json
{
  "version": 1,
  "tenant": "demo-bank",
  "company": "demo-bank",
  "account": "an.nguyen",
  "kind": "person",
  "role": "admin",
  "unit": "finance",
  "dataMode": "không mật",
  "name": "An Nguyen",
  "subject": "oneid:u_01HZX4M8Q3"
}
```

`subject` is present for a person and absent for an agent; an agent principal
also carries `owner`. `dataMode` is the unit's mode (the stricter of the tenant
default and the unit), never the caller's claim. The same resolver feeds
`resolve.py --run-context`; the pass carries `account`, `role`, `unit`,
`dataMode`, and never a secret.

### Agent creation (admin surface, #273)

Input: `{id, name, role, unit, owner, purpose}` plus the acting admin's
principal. Output: the public account row (`kind: "agent"`, `status: "active"`,
no credential) and one audit line `identity.agent_created`. The store is the
single source; no second registry.

## Errors

Every refusal names the fix. Codes are stable; the implementation maps them to
HTTP 4xx and to the CLI's exit codes.

| Code | When | What the operator does |
|---|---|---|
| `E-IDN-01` | the assertion is malformed (missing claim, bad type, wrong `alg`) | redo the login; the IdP client is misconfigured |
| `E-IDN-02` | the assertion is untrusted (issuer, audience, signature, `exp`, `nonce`, `auth_time`) | check the tenant's `identity` config and the clock; never retry with another tenant's token |
| `E-IDN-03` | the role is not posted at the unit (or the unit is not on the company's chart / is ambiguous) | fix the org chart, or move the account |
| `E-IDN-04` | no account is bound to this subject in this tenant | invite the person, then link (`identity.bind`) |
| `E-IDN-05` | an email matches but no subject is bound | link the subject; an email alone is not authorisation |
| `E-IDN-06` | the account is disabled | re-enable it, or complete the offboarding |
| `E-IDN-07` | an agent invariant is broken (owner missing / owner disabled / owner is an agent / credential present) | fix the store; reassign the agent first |
| `E-IDN-08` | `accounts.json` is malformed or the tenant has no store | repair the store; `resolve.py --sync` lists every problem |
| `E-IDN-09` | the acting account is not an active admin | use a tenant admin or platform admin for identity changes |
| `E-IDN-10` | another identity change holds the tenant lock, or the change was applied but its audit line could not be written | retry (a crashed lock expires after 5 minutes); repair the audit log before the next change |

Refusals are recorded in the tenant's audit chain (`identity.refused`, with the
code) and never mint a session or a pass.

## Invariants (checked by `--sync` once implemented)

1. One account per `id`; ids are path-safe and stable.
2. One account per `sso.subject` per tenant — a subject bound twice is an
   impersonation waiting to happen (`E-IDN-07`).
3. Every agent has an `owner` that is an **active person** in the same tenant.
4. An agent has no credential and no SSO binding; a person has at least one.
5. `role` is a portal role posted at `unit` on the named company's chart.
6. A disabled account resolves to no principal (`E-IDN-06`); a disabled owner
   cannot keep an agent active.
7. The audit line for an agent action names the account; the pass names the
   `owner` in `responsibleUser`.
8. Offboarding order: **disable the agent first, then the person** — a store
   that reverses it is `E-IDN-07`, not a silent orphan; the **last active admin**
   cannot be disabled (it would lock the tenant out).
9. One email per account: two accounts sharing an email cannot be told apart at
   invite time (`E-IDN-07`).
10. A store with a duplicate id or a subject bound twice is refused at
    resolution, never resolved to "the first match" (`E-IDN-07`).
11. Changes are serialised per tenant (`.identity.lock`); a change whose audit
    line cannot be written is reported as applied-but-unrecorded (`E-IDN-10`).

## Records

Every identity change writes one record beside the store:
`customers/<tenant>/identity-state.json`.

```json
{
  "version": 1,
  "contract": "tenant-identity@1",
  "tenant": "demo",
  "sha256": "<digest of the account rows, order-independent>",
  "accounts": 3, "people": 2, "agents": 1,
  "updatedAt": "2026-11-01T09:00:00Z",
  "by": "an.nguyen"
}
```

It is written by `create_agent`, `bind`, `unbind` and `set_status`, in the same
step as the store (both atomic). `resolve.py --sync` recomputes the digest and
the counts: a store edited by hand is `identity-state.json: accounts.json changed
outside identity.py …` (an `E-IDN-08` condition), not a silent change. A tenant
that never used the identity path has no record and stays valid; the first change
creates one. An intended out-of-band change is accepted explicitly —
`identity.py seal --tenant <t> --actor <admin>` re-records it and appends
`identity.sealed` (with the new digest) to the audit chain.

There is no second record of *who did what*: the events stay in the tenant's audit
chain (`identity.*`); this record is the *state witness* that the store still is
what the last change made it.

## Measurement

`identity.py metrics --tenant <t> --actor <admin>` is the tenant's identity
health: counts (people, agents, active admins, subjects bound), the record's
state, and the full problem list. Three rules raise alerts:

| Rule | Fires when | Why it matters |
|---|---|---|
| `I1` record-drift | the store no longer matches `identity-state.json` | a change outside `identity.py` — the record exists to catch exactly this |
| `I2` single-admin | fewer than two active admins | the last-admin rule refuses a lockout, but one lost password is still one |
| `I3` unrecorded | accounts exist, no record | the store predates the identity path; a hand-edit would be invisible |

`identity.py alerts` records them once per rule per day in
`customers/<tenant>/identity-alerts.jsonl`; `--sync` validates that store, and
`identity.py drill` proves I1 and I2 fire. The drill is the evidence that the
alert is not decorative.

## Lifecycle

| Event | Effect |
|---|---|
| invite + accept | a pending invite reserves a seat (`gateway/seats.py`); on acceptance the account is created with a subject binding |
| first ONEID login | resolves only through an existing binding; **no auto-provisioning** from email |
| role change | the org chart and the account move together; a pass minted before the change keeps the role it was signed with |
| disable person | no new principal; owned agents must already be disabled or reassigned |
| disable agent | `run-context` refuses (`E-IDN-06` mapped to the adapter's `E-ADP-04/05`); the record stays |
| delete | refused while the account owns an agent or has audit history — disable, never delete |

## Where this is implemented (PC1-04-02…10)

| Piece | Path | Issue |
|---|---|---|
| account model + validation, wired into `--sync` | `gateway/identity.py` | **done** (#273) |
| the identity record (digest manifest) written per change, validated by `--sync` | `gateway/identity.py` (`identity-state.json`) | **done** (#276) |
| admin surface: status, list, show, resolve, history, create agent, bind/unbind, disable/enable, validate, seal | `infra/identity.py` | **done** (#273, #277) |
| run-context consumes the principal (no second mapping) | `gateway/resolve.py` | **done** (#273) |
| ONEID login: the SSO callback uses the same resolver (no second mapping) | `apps/api/src/sso.service.ts` + `identity.core.ts` → `infra/identity.py` | wired (#274); lands with the SSO layer (#208) |
| tests, records, docs, hardening, metrics, demo | — | #275–#281 |

**As built (#273).** `identity.principal_for_account` is the only mapping:
`resolve.py --run-context` calls it and refuses a disabled account, a role not
posted at the unit, or an agent whose owner is missing/disabled/inactive — before
a pass exists (identity codes map to `E-ADP-04`/`E-ADP-05`). Identity changes are
admin-only (`E-IDN-09`) and append `identity.agent_created`, `identity.bound`,
`identity.unbound`, `identity.disabled`, `identity.enabled` to the tenant's audit
chain with the acting admin. `--sync` runs `identity.validate_tenant`; an absent
store is valid (a provisioned tenant with no accounts yet), but resolution refuses
it with `E-IDN-08`.

**The surface (#277).** Every operator verb is admin-only (`E-IDN-09`):
`status` (counts, the identity record's digest/time/author and whether it still
matches, the tenant's problems), `list`, `show`, `resolve`, `history` (the
`identity.*` events from the audit chain, per account if asked), the mutations,
`validate` and `seal`. `identity.py subject` stays open: it is the login mapping
the API calls, not an operator view.

**One resolver (#274).** The adapter gate (`paperclip.verify`) and
`resolve.py --run-context` call `identity.principal_for_account`; the OIDC callback
(`apps/api/src/sso.service.ts` → `identity.core.ts` → `infra/identity.py subject`)
is wired to the same resolver in the SSO layer, which is still uncommitted in the
OpenGate worktree (#208) and lands with it. When it does, the old `findBySso`
email fallback disappears: an email match without a linked subject is `E-IDN-05`,
a disabled account is `E-IDN-06`, an unknown subject is `E-IDN-04`, each refusal
audited as `auth.sso_login_denied`. Until then the run path is the wired one; the
API's fallback is a known gap, not a second rule for runs.

Until #273 lands, the rule stands: **no agent credential in this repo**, and no
run without an account whose role is posted at its unit.

## The commands, in order

`docs/identity-walkthrough.md` in the OpenGate repository is the operator runbook:
status, create an agent, bind a ONEID subject, resolve the principal, an email
refused, the history, a hand-edit caught and sealed, the offboarding order, and
the repo's own `--sync` — each command with its committed output. It is generated
by `infra/identity_walkthrough.py` and re-run in CI, so it cannot drift.

## The contract, checked

```
$ python scripts/check_identity_spec.py
identity: 3 account(s) — 2 people, 1 agent(s) — validate against tenant-identity@1 — OK

$ python scripts/check_identity_spec.py --self-test
identity --self-test: 9 mutations refused, the committed example validates — OK
```

The self-test mutates `tests/fixtures/identity/accounts.valid.json` one rule at
a time — an agent with a password, two accounts on one subject, an agent owned by
an agent, a disabled owner, a role that is not a portal role — and fails if any
mutation is accepted. `scripts/test_identity_matrix.py` goes further: each of 14
named cases must earn **its own sentence** (a negative test that accepts the
wrong refusal hides a regression), and the clean cases — including the offboarded
agent whose owner is disabled — must stay clean. CI runs all three commands.

The tenant side mirrors the matrix (`tests/test_identity_matrix.py` in
OpenGate): the same shapes through `identity.validate_tenant`, plus a local
cross-check against this checker when both repositories are checked out.

## Not in this contract

- No new identity provider, no local password policy, no MFA policy: ONEID owns
  authentication; this repo owns the **mapping**.
- No SCIM or directory sync: a tenant's people arrive through invites and ONEID
  logins.
- No cross-tenant principal: a token for tenant A never resolves in tenant B
  (`E-IDN-02`), and a platform admin acts through `customers/_platform`, not by
  widening a tenant.
