# Simulation / digital-twin plan (v0.1)

1. Every instance emits audit events (step, actor, rule/model version, latency, decision).
2. Nightly: audit log → warehouse (append-only, PII-masked).
3. Simulator replays logs with altered params (staffing ×, SLA ×, fraud-rate ×) to predict TTA/approval/default.
4. What-if UI: sliders → p50/p95 TTA, queue depth, override load, cost/instance.
5. Monthly: twin output feeds risk-committee pack + L3→L4 promotion evidence.

## Capacity assumptions (issue #18, source: engine/capacity.csv)

- `tasks_per_day` assumes a 8h day minus 1h overhead (meetings, breaks); utilization
  caps at 0.80 (0.60-0.70 for approvers who also cover clients/committees).
- `mins_per_task` blends handle time + wrap-up, from branch time-studies (2025) and
  pilot shadowing; re-calibrate after each pilot wave (J95) with real measurements.
- Headcounts mirror the org files' role rows; unit totals may exceed listed roles
  (leads, QA, trainees not modelled individually).
- 24/7 desks (payments, fraud, P1) divide daily capacity across 3 shifts.
- Simulator draws task times from a lognormal around `mins_per_task` (σ=0.4);
  arrivals are Poisson per process volume (D40 sandbox provides the rates).

## Simulator I/O + determinism (issue #81) — the twin core

Inputs: audit-log export (traces), capacity.csv, what-if params
(`staffing×`, `sla×`, `fraud_rate×`, `volume×`), `--seed` (required).
Outputs: p50/p95 TTA per process, queue depth over time, override load,
cost/instance, bottleneck ranking — all stamped with seed + code version.
Determinism: same inputs + seed = byte-identical outputs (asserted in CI on the
loan trace fixture); RNG streams split per process so adding a process never
reshuffles others. Simulator code lives in `sim/` (track-I build); this doc is
the contract it implements.
