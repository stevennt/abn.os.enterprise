# Environments + secrets v1.0 (issue #59) — parity, vault-only secrets, no prod PII in stage

## Env matrix

|  | dev | stage | prod |
|---|---|---|---|
| purpose | unit shuffle, spike work | promotion gates, drills, twin seeding | live money |
| data | synthetic only (D40 seed) | synthetic + replayed history (D39) | real, sealed |
| engine | local runner / 1-node Zeebe | HA pair, prod-sized topics at 10% | HA, full partitions (D36) |
| deploys | any commit | release tags only | release tags + 4-eyes |
| PII | synthetic | synthetic | sealed, gated (D33) |
| break-glass | n/a | stage password, logged | dual-control, ticketed, 2h max |

Parity rule: stage mirrors prod topology (same services, smaller sizes); a gate that
passes in dev but never ran in stage counts for nothing (A10).

## Vault paths (SOPS + age, house `abn.secrets.encrypted` repo)

```
vault/os/dev.enc.yaml    — non-prod provider keys, sandbox tokens
vault/os/stage.enc.yaml  — stage provider keys, replay credentials
vault/os/prod.enc.yaml   — prod JWT secret, service tokens, provider keys (MLRO-gated read)
```

Rules: plaintext secrets never enter chat, logs, commits, or shell history; rotation =
edit env file + recreate container (house Supabase lesson); after any incident, rotate
stage + prod provider keys and re-run the A07 money drill before re-promoting.
