# Release tags v1.0 (issue #126) — per industry, two streams

One global tag cannot express "legal at v3, banking at v7". Each industry declares
its own tag streams in `industries/<id>/industry.yaml`:

```yaml
tag_stream:
  policy_prefix: banking-policy
  pack_prefix: banking-pack
```

## The two streams

| Stream | Tag shape | Contains | Moves on |
|---|---|---|---|
| **policy** | `<industry>-policy-YYYY.MM.N` | rules, flows, org, events, industry docs, evals | business/risk/compliance review cadence (slow, deliberate) |
| **pack** | `<industry>-pack-YYYY.MM.N` | `industries/<id>/pack` (agents, skills, roles) | AI-team cadence (fast, iterative) |

Two streams exist because **a prompt wording change must not force a policy release,
and a threshold change must not wait for prompt tuning**. Both are versioned; neither
can move silently.

Serial `N` is per industry per month, starting at 1. Prefixes must start with the
industry id (enforced by `bin/verify-industry-tags.py`).

## Creating a tag

```
bin/tag-industry banking --kind policy --dry-run   # preview tag + commit + dirty state
bin/tag-industry banking --kind policy --push      # create annotated tag and push
```

The script refuses to tag a dirty tree (a tag that does not match a commit is worse
than no tag). Annotation records industry, tier, commit, stream, and rule/flow counts
(policy) or pack path/status (pack).

## Verifying refs

```
python bin/verify-industry-tags.py          # human-readable
python bin/verify-industry-tags.py --json   # machine
```

Checks: prefix sanity, at least one tag per stream, and every `release_ref`
recorded in a manifest resolves (locally or on origin). Runs in CI; offline-safe —
when origin is unreachable it says so instead of claiming existence.

## How consumers pin

A consumer (e.g. OpenGate) records `<tag>@<short-sha>` in its own pin file. Because
the tag is annotated, the sha is recoverable; because it is pushed, the pin is
verifiable by anyone. Never pin a branch.

## Superseded

`banking-2026-10-31.1` (created for the L3-01 OpenGate wiring) predates this scheme.
It stays valid for that pin; all new pins use the two-stream form.
