# Synthetic sandbox dataset plan v1.0 (issue #40) — pilots never touch prod PII

## Generator plan (`scripts/gen_sandbox.py`, track J)

Stages, in order: persons (10k, VI names + test CCCD range) → accounts (1.6/customer)
→ loans (0.5/customer, requested→approved/declined mix) → transactions (30/account/month
× 3 months) → complaints (2% of customers) → AML hits (0.3%, marked). Every row carries
`_synthetic_pii: true` and test-only markers (TEST names, `999`/`000` id ranges) so a
leak is recognizable on sight. Outputs land in stage Postgres + `bank.ops.replay` (D39).

## Scale table

| Entity | Count | Notes |
|---|---|---|
| persons | 10,000 | ages 18–70, income lognormal |
| accounts | 16,000 | savings/current/term mix |
| loans | 5,000 | 70% approved, DSTI spread incl. breaches |
| transactions | ~1.4M | 3 months history |
| complaints | 200 | severity mix S1–S4 |
| aml hits | 30 | all REVIEW/FILED paths exercised |

## Seed determinism requirement

- One `--seed` (default 42) drives ALL randomness; same seed + same code = byte-identical
  dataset (verified by sha256 of the dump in CI, track J).
- No wall-clock, no uuid4, no network calls in the generator — counters and seeded RNG only.
- Dataset version (`sandbox-YYYYMMDD-seed42`) is stamped into every pilot report so
  results are comparable across runs.
