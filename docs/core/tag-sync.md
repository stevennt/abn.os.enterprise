# Enterprise tags to tenant pins (issue #233)

A policy release upstream must become a **visible pin bump**, not an invisible
change. This repo owns the tags; each OpenGate tenant pins the release it is on;
the platform reports the drift and refuses a bump nobody confirmed.

## The tag list check

```bash
bin/tag-list            # human list: stream, industry, version, date, sha
bin/tag-list --json     # the snapshot a consumer commits
bin/tag-list --check    # CI: no malformed release tags
```

Three streams (`docs/core/release.md`):

| Stream | Shape | Means |
|---|---|---|
| contract | `contract-YYYY.MM.N` | metamodel + `docs/core` |
| policy | `<industry>-policy-YYYY.MM.N` | an industry's business truth |
| pack | `<industry>-pack-YYYY.MM.N` | an industry's agent pack |

`--check` fails a tag that *looks* like a release tag but has a malformed
version (`banking-pack-2026.13.1`), so a typo cannot become a release. Tags that
predate the scheme (`banking-2026-10-31.1`) are listed as `legacy` with a
warning — history, not a pin source.

## The snapshot

Consumers do not call `git ls-remote` on every run. `bin/tag-list --json` emits a
snapshot that the OpenGate repo commits at `onboarding/enterprise-tags.json`:

```json
{ "version": 1, "repo": "stevennt/abn.os.enterprise", "generatedAt": "2026-10-31",
  "tags": [ { "name": "contract-2026.11.1", "stream": "contract",
              "version": "2026.11.1", "sha": "a7baab4…", "date": "2026-11-01" } ] }
```

The snapshot carries the **sha of each tag**: a tag can be moved, a commit
cannot, and the sha is what a tenant pins for the contract stream.

Refresh flow (release captain → ops):

```bash
# in this repo, after cutting tags
bin/tag-list --json > ../abn.platform.opengate/onboarding/enterprise-tags.json
# in OpenGate: the drift report moves; --sync fails if a pin is not in the list
```

## What a tenant pins

| Pin | Tenant field | Checked against |
|---|---|---|
| contract | `enterprise.tag` + `enterprise.sha` | the snapshot's `contract-*` tags and the tag's sha |
| policy:<industry> | `versions.<industry>` | the industry's `*-policy-*` tag versions |
| pack:<industry> | `bundles.<industry>.tag` | the industry's `*-pack-*` tags |

A pin the snapshot does not contain is a **validation error** (the tenant pins a
release that does not exist); a pin behind the latest release is **drift** — a
report, never a failure, because the gap between a release and a bump is normal.

## Bump requires confirmation

`infra/tag_sync.py bump` (OpenGate) previews and writes nothing without
`--confirm`:

```bash
python infra/tag_sync.py bump --tenant abnasia --pin contract \
    --to contract-2026.11.1 --by ops-1 --reason "contract release review"
# → needsConfirmation: true, applied: false, exit 3

python infra/tag_sync.py bump ... --confirm
# → applied: true; customers/abnasia/domains.json updated;
#   customers/abnasia/pin-changes.jsonl gets {pin, from, to, tag, sha, by, reason}
```

- **No silent bumps.** The preview names from → to, the sha, and the latest
  release; the CLI exits 3 until it is confirmed.
- **Records are append-only.** A pin edited out of band (config changed, no
  record) fails `--sync`: the latest record no longer matches the current pin.
- **The contract bump moves the sha**, not just the tag string — that is the
  point of pinning a commit.

## Ownership

| Step | Owner |
|---|---|
| cut a release tag | release captain (`bin/tag-industry`, contract tag) |
| refresh the snapshot | ops / platform admin |
| bump a tenant pin | platform admin, with `--by` and a `--reason` |
| confirm the bump is wanted | tenant admin (commercial conversation) |

## Company #1

Tenant `abnasia` pins `contract-2026.11.1` (sha `a7baab4…`), policy
`banking 2026.10.1` and pack `banking-pack-2026.10.1` — all three current in the
snapshot, so its drift report is empty. The worked example lives in
`docs/core/company-mapping.md` (which model the pin maps to).
