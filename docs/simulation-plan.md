# Simulation / digital-twin plan (v0.1)

1. Every instance emits audit events (step, actor, rule/model version, latency, decision).
2. Nightly: audit log → warehouse (append-only, PII-masked).
3. Simulator replays logs with altered params (staffing ×, SLA ×, fraud-rate ×) to predict TTA/approval/default.
4. What-if UI: sliders → p50/p95 TTA, queue depth, override load, cost/instance.
5. Monthly: twin output feeds risk-committee pack + L3→L4 promotion evidence.
