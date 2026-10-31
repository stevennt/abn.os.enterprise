# Commercial onboarding pack

What sales hands over so engineering is not improvising. One pack per tenant,
filled before provisioning and validated before the first account exists.

The pack is a file, not an email thread:

```
customers/<tenant>/commercial-pack.json          the handover, one per tenant
onboarding/tenant-template/commercial-pack.json  the template (OpenGate repo)
python3 infra/commercial_pack.py check --tenant <tenant>
```

The machine-readable schema lives where it is enforced:
`schemas/commercial-pack.json` in the OpenGate repo. This document is the
authority on **what** is collected and **who owns it**; the schema is the
authority on **shape**.

## The checklist

| # | Area | Fields | Owner | Required |
|---|---|---|---|---|
| 1 | **Profile** | `legal_name`, `jurisdiction` | legal | yes |
|   |         | `practice_focus`, `working_languages` | sales | yes |
|   |         | `confidentiality`, `default_data_mode` | legal | yes |
| 2 | **Companies** | `id`, `name`, `departments` | sales | yes (one entry for a single entity, `id` = tenant) |
|   |             | `legal_name`, `registration_number`, `registered_address` | legal | yes |
| 3 | **Tax ids** | `companies[].tax_id`, one per legal entity, unique | legal (customer supplies) | yes |
| 4 | **SSO** | `mode` (`sso` / `password`) | sales (decision) | yes |
|   |       | `provider`, `issuer`, `clientId`, `redirectUri`, `scopes`, `linkClaim` | engineering (customer IT supplies) | when `mode: sso` |
|   |       | `ssoOnly` | security | when `mode: sso` |
| 5 | **Packs** | `packs[]` — pack ids from `onboarding/pack-set.json` | sales | yes |
| 6 | **Contacts** | `contacts.sales` | sales | yes |
|   |             | `contacts.billing` | finance | yes |
|   |             | `contacts.technical` | engineering | yes |
|   |             | `contacts.security` | security | no |

Every contact is `{name, email, phone?}` with a non-empty name and a valid
email. The pack itself is prepared by sales: `preparedBy` (an email) and
`preparedAt` (a date) are part of the file.

## Handover rules

1. **No pack, no provisioning.** A tenant without a complete pack is a lead, not
   a customer; engineering does not improvise the missing fields.
2. **Tax ids belong to legal entities.** A group has one tax id per company (a
   branch suffix is part of the recorded id, not a new entity). A single entity
   is one company entry whose `id` is the tenant id.
3. **SSO values, never secrets.** The pack carries the IdP decision and the
   public configuration. The client secret lives in an environment variable and
   the platform's `customers/<tenant>/sso.json` is written by engineering — a
   secret in the pack fails the contract.
4. **Packs are entitlement, not data.** Sales names the packs the contract
   includes; engineering checks them against what the platform ships
   (`onboarding/pack-set.json`) and against the tenant's plan (a downgrade keeps
   the data and disables the packs gracefully).
5. **`status: ready` means the validator says ready.** A pack claiming ready
   while incomplete fails validation; a complete pack still in `draft` is
   reported as ready-to-hand-over.
6. **Contacts are roles, not names in a chat.** Each role has a reachable owner
   before the pilot starts; a missing billing or technical contact is a
   blocking gap.

## Exit criteria (engineering)

Before provisioning, all of the following are true:

- `python3 infra/commercial_pack.py check --tenant <tenant>` exits 0;
- every company in the profile has a tax id in the pack (and vice versa);
- `packs[]` is a subset of the platform's pack set and of the plan;
- SSO is either `password` or fully specified (and the secret is not in the
  file);
- the three required contacts are reachable.

`python3 gateway/resolve.py --root . --sync` also validates any pack that is
already on disk: a `ready` pack with missing fields, an unknown company, a pack
the platform does not ship, or a secret in the file fails the gate.

## Template

`docs/core/templates/commercial-onboarding-pack.yaml` is the blank form with the
owner inline on every field; the OpenGate template
(`onboarding/tenant-template/commercial-pack.json`) is the same shape with the
placeholders the provisioner substitutes. `infra/commercial_pack.py template`
generates a pre-filled draft from the tenant's profile so sales starts from what
is already known instead of a blank page.
