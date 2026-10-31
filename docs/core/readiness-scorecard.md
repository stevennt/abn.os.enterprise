# Tenant readiness scorecard — the go/no-go contract (issue #239)

Before a tenant goes live it passes a checklist, not a vibe. The checklist is
ten gates; every gate names an owner, the evidence that proves it, and whether a
failure blocks go-live. The decision is recorded, and the platform keeps
checking it afterwards. Commands live in the platform repo
(`abn.platform.opengate` → `docs/readiness-scorecard.md`).

## The ten gates

| # | Gate | Owner | Blocking | Passes when | Evidence (minimum) |
|---|---|---|---|---|---|
| 1 | **Commercial handover** | sales | yes | the commercial pack validates `ready`, with no gap returned unnoticed | the pack file (sha256), `preparedBy`, the finding counts |
| 2 | **Tenant profile and shape** | engineering | yes | the profile validates, the layout matches the shape, jurisdiction/confidentiality/instructions are present | `profile.json` (sha256), shape, company list |
| 3 | **Organisations** | engineering | yes | every company has a valid chart: a root, unique unit ids, no cross-company references | each `org.json` (sha256), unit ids |
| 4 | **Roster plan** | tenant admin | **no** (advisory) | at least one position is declared and valid | the position counts per company |
| 5 | **Folders and access** | tenant admin | yes | the folder declaration is valid, the ACL names real units, and every root has a rule | `folders.json` (sha256), roots, rule paths |
| 6 | **Identity and seats** | tenant admin | yes | an admin exists, every account sits on a unit that posts its role, seats are inside the plan | `accounts.json` (sha256), account ids, seat totals |
| 7 | **Plan and packs** | sales | yes | a real subscription names a registered plan, and the contracted/declared packs are inside it | `subscription.json` (sha256), plan id, packs |
| 8 | **Terms, privacy and data policy** | legal | yes | required terms are accepted at the current version, the tenant declares its own privacy controller, data modes and a retention policy are on disk, the PII classification is clean | `terms-acceptance.jsonl`, `privacy.json`, `retention.json` (sha256), data modes |
| 9 | **1ID (SSO) decision** | security | yes | the pack's `sso.mode` is executed: an `sso` tenant has a valid enabled config, a `password` tenant has none, and no rotation is left open | `sso.json` (sha256), pack mode, config summary, rotation count |
| 10 | **Platform gate** | operator | yes | `resolve.py --sync` exits 0 at the recorded commit — the repository the tenant runs is valid | the command, its exit code, the last line, the commit |

The gate set is versioned (`gatesVersion: 1`); adding or re-classifying a gate
is a new version, never a silent edit.

## The decision rule

- **GO** requires all nine blocking gates to pass. One blocking failure is
  **NO-GO** — there is no waiver for a blocking gate, because every one of them
  is either a legal obligation or something the tenant cannot operate without.
- The **advisory** gate (`roster`) may be open at go-live; it is listed in the
  report's *Conditions* with an owner and a date. An empty roster plan is a
  known gap, not a hidden one.
- **NO-GO** can always be recorded. It is a legitimate outcome; a written NO-GO
  with the failing gates is how a launch slips a week instead of failing at
  cutover.

## Evidence rules

- Evidence is a **file and its sha256**, or a **command, its exit code and the
  line it printed** (with the commit for the platform gate). Hand-written
  evidence is not evidence.
- The scorecard adds no new truth: each gate calls the module that owns the
  rule (`commercial_pack`, `tenant_model`, `tenant_registry`, `folders`, `acl`,
  `seats`, `plans`, `terms`, `retention`, `pii`, `sso_secret`) and reports what
  it says. When a rule changes, the scorecard follows it.
- A gate that cannot read its input **fails**; it never passes by default.

## The record

`customers/<tenant>/go-no-go.jsonl` — append-only, one JSON line per decision,
newest last:

```json
{"version": 1, "tenant": "acme", "decision": "go", "at": "2026-11-01T09:00:00Z",
 "by": "ops@abnasia", "note": "pilot go-live", "commit": "e287f18",
 "gates": [{"id": "handover", "blocking": true, "passed": true}, "…"]}
```

Rules:

- a `go` line must have every blocking gate `passed: true` — an inconsistent
  line fails validation;
- the latest line is the standing decision;
- **a recorded GO is re-checked**: `opengate sync` re-runs the blocking gates
  for that tenant and goes red if one now fails, naming the gate. A decision is
  a claim the platform keeps checking, not a snapshot filed and forgotten.

## Sign-off

| Role | Signs that |
|---|---|
| operator | the scorecard ran at the recorded commit; the evidence is attached |
| tenant admin | the chart, folders, accounts and plan are the customer's |
| security | the 1ID decision is executed; the login smoke test passed (the secret-rotation runbook's Step 4 is the proof) |

The filled document (`customers/<tenant>/go-no-go.md`) is generated from a live
run, never typed by hand: `infra/scorecard.py report`. The blank form is
committed at `onboarding/tenant-template/go-no-go.md`.

## How this relates to the other lists

| List | Question | Owner |
|---|---|---|
| `/readiness` (platform page) | "what is left for *this tenant admin* to do?" | tenant admin |
| pilot checklist (`docs/pilot-checklist.md`) | "is this *domain pack* safe to enable on pilot day?" | operator |
| **this scorecard** | "may this *tenant* go live, and who says so?" | operator + tenant + security |

They overlap on purpose: the readiness page is the working list, the scorecard
is the signed gate.
