# Onboarding a tenant — the contract view (issue #238)

A **tenant** is one customer of OpenGate: one or more legal entities, their
people, folders and login. This page is the contract half — what must be true
when the customer goes live, who owns each part, and what evidence is kept. The
operator's step-by-step commands live in the platform repo:
`abn.platform.opengate` → `docs/onboarding-tenant.md`.

Two artefacts describe a tenant, and they must agree:

| Artefact | Where | What it is |
|---|---|---|
| the **tenant** | OpenGate `customers/<tenant>/` | profile, companies, org charts, folders, accounts, SSO config |
| the **company model** | this repo `companies/<company>/` | the operating model (org units, flows, rules, packs) pinned to a contract release |

A single entity has one company model whose `id` may equal the tenant id. A
group has one company model per legal entity; the tenant is the container.

## Shapes

| Shape | Tenant `profile.json` | Org charts | Company models |
|---|---|---|---|
| Single legal entity | no `companies[]` | `customers/<tenant>/org.json` | one, `companies/<company>/` |
| Group | `companies[]`, two or more | one per company under `customers/<tenant>/companies/<c>/` | one per legal entity |

The shape is an onboarding decision, not a setting: a single entity is grown
into a group by a deliberate re-onboard, and a group is never silently reduced
to one company (the platform refuses to remove the last two companies).

## Who owns what

| Area | Owner | Must produce | Checked by |
|---|---|---|---|
| commercial pack (legal name, tax ids, contacts, packs) | sales, with legal/finance | a `ready` pack, one per tenant | `infra/commercial_pack.py check` |
| jurisdiction, confidentiality, data modes | legal | profile values that match the pack | `opengate sync` (`tenant_model`) |
| tenant skeleton, companies, folders | engineering | `profile.json`, `folders.json`, `folders/` | `gateway/provision.py` + sync |
| departments → org units | engineering, with the customer's HR | one chart per company; unit ids that post roles | `infra/org_import.py` + sync |
| company model, contract pin | engineering | `companies/<company>/` pinned to a release tag | `scripts/validate_company.py` (this repo) |
| plan and packs | sales decision, engineering execution | `subscription.json` + the packs inside the plan | `infra/plan.py show` |
| identity | tenant admin | first admin, then every account | `apps/api` roster, `infra/seats.py` |
| 1ID (SSO) | security + the customer's IT | `sso.json` (no secret), IdP registration, secret in the vault | `opengate sync`, `infra/sso_secret.py status` |
| go-live sign-off | the operator | the evidence below | `/readiness` at 100% + sync green |

## The sequence and what "done" means at each step

| # | Step | Done when |
|---|---|---|
| 1 | handover | the pack validates `ready`; every gap went back to its named owner |
| 2 | provision | the dry-run plan was read and the apply wrote exactly that plan; sync green |
| 3 | organisations | every company has a chart whose unit ids post the roles its people hold |
| 4 | folders and access | roots come from the platform taxonomy; the ACL names units, not roles; a folder with no rule is denied on purpose |
| 5 | plan | the subscription names a registered plan and every pack the contract bought is inside it |
| 6 | people | one admin can sign in; every account's unit exists on that company's chart |
| 7 | 1ID | `sso.json` matches the IdP registration, the secret is in the vault/env (never a file), `ssoOnly` only where the login path is proven |
| 8 | sign-off | `opengate sync` green **and** `/readiness` has no open required item |

## The contract pin

Every company model declares the release it was built from
(`docs/core/onboarding-company.md`):

```yaml
contract:
  repo: abn.os.enterprise
  tag: contract-2026.11.1
  sha: a7baab409dce013bd296b57aafc500565b878dfa
```

The **tag** is a release (`<stream>-YYYY.MM.N`); the **sha** is what an audit
needs, because tags can move. A tenant onboarding must not pin a branch or
`latest`: the model is read months later, and the contract it was built against
has to resolve then. When an industry or pack moves, the company model is
re-pinned deliberately — `docs/core/versioning.md`.

## Evidence to file with the tenant

- the commercial pack (the handover, with `preparedBy`/`preparedAt`);
- the `provision` plan and apply output;
- the org sheet the customer approved, and the imported `org.json`;
- the `opengate sync` output (the commit it ran at);
- the `/readiness` snapshot at 100%;
- the screenshot set from the platform guide (`/org`, `/files`, `/roster`,
  `/admin/branding`, `/readiness`);
- for a group, each company model's pin (`tag` + `sha`) and
  `validate_company.py` output.

## Status at `contract-2026.11.1`

The contract above is stable; two implementation pieces are not merged in the
platform repo yet, and the operator guide marks them rather than describing them
as working:

- **group portal** — the file/CLI path for a group is complete and syncs green,
  but portal login for a group tenant is rejected until per-company charts are
  served (the tenant has one chart per company, the API loads one per tenant);
- **1ID login endpoints** — `sso.json` is configured and validated, but the SSO
  login route ships with issue #208; `ssoOnly` stays `false` until then.

Neither changes the contract: a group is still modelled as a group, and SSO is
still the enterprise login. They change what an operator can demonstrate on
day one, and the guide says which.

## Where to run it

- operator guide (commands, screenshots, failure modes):
  `abn.platform.opengate` → `docs/onboarding-tenant.md`
- company model: `docs/core/onboarding-company.md`, `bin/new-company`
- industry model: `docs/core/onboarding-industry.md`, `bin/new-industry`
- commercial handover: `docs/core/commercial-onboarding.md`
- tenant→repo mapping and the contract pin: `docs/core/company-mapping.md`
