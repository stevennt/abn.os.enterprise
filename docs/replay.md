# Replay / backfill tool spec v1.0 (issue #39)

Re-emits historical events into stage for regression testing and twin seeding.
Needed for every L3→L4 promotion gate (I83) and every routing fix (A04).

## CLI spec

```
os-replay --source audit|dlq|topic --from 2026-09-01 --to 2026-09-30
           --filter event_type=transfer.domestic.requested
           --target stage --rate 100/s --dry-run --seed 42
```

| Flag | Meaning |
|---|---|
| `--source` | where history comes from: audit chain export, DLQ, or topic retention |
| `--from/--to` | time window (UTC); ranges >31d need risk sign-off |
| `--filter` | event_type and/or key prefix; default is everything (dangerous — confirm) |
| `--target` | `stage` only in v1 (prod replay is forbidden; twin seeding uses stage snapshots) |
| `--rate` | throttle so stage behaves like prod cadence, not a flood |
| `--dry-run` | classify + count only, emit nothing |
| `--seed` | deterministic sampling for reproducible regression sets |

## Idempotency note

Replayed events keep their ORIGINAL idempotency keys — that is the whole point:
handlers must recognize them as duplicates-or-new exactly as prod would. The tool
refuses to rewrite keys (`--rewrite-keys` does not exist and will not be added).
A replay that double-posts money fails the promotion gate on the spot (A07 drill).
DLQ replays additionally carry `replay_of` + `replay_reason` headers so triage can
tell history from live traffic.
