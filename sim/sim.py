#!/usr/bin/env python3
"""Minimal simulator (issue #105, contract I81): replay the loan trace fixture
with what-if multipliers. Seeded only (--seed); stdlib only.
Usage: python sim/sim.py --trace examples/bank/loan-approval.trace.json
  --instances 1000 --staffing 1.0 --sla 1.0 --fraud 1.0 --seed 42 --out /tmp/sim.json
Outputs: TTA p50/p95, per-step totals, review load, byte-identical per seed.
"""
import argparse, json, random
from pathlib import Path

def pct(v, p):
    v = sorted(v)
    return v[min(int(p * len(v)), len(v) - 1)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--instances", type=int, default=1000)
    ap.add_argument("--staffing", type=float, default=1.0)
    ap.add_argument("--sla", type=float, default=1.0)
    ap.add_argument("--fraud", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    steps = json.load(open(a.trace))["steps"]
    base = {"workflow": 2.0, "ai": 8.0, "human": 60.0}
    ttas, per_step, reviews = [], {}, 0
    for _ in range(a.instances):
        t = 0.0
        for s in steps:
            m = base[s["kind"]] * a.sla
            if s["kind"] == "human":
                m /= a.staffing
            dt = rng.lognormvariate(0.0, 0.4) * m
            t += dt
            per_step[s["step_id"]] = per_step.get(s["step_id"], 0.0) + dt
        if rng.random() < 0.15 * a.fraud:
            reviews += 1
            t += rng.lognormvariate(0.0, 0.4) * 30.0 * a.sla
        ttas.append(round(t, 3))
    out = {"seed": a.seed, "instances": a.instances,
           "params": {"staffing": a.staffing, "sla": a.sla, "fraud": a.fraud},
           "tta_p50": pct(ttas, 0.5), "tta_p95": pct(ttas, 0.95),
           "per_step_min": {k: round(v, 1) for k, v in sorted(per_step.items())},
           "reviews": reviews}
    Path(a.out).write_text(json.dumps(out, sort_keys=True, indent=1) + "\n")
    print(f"sim: n={a.instances} p50={out['tta_p50']} p95={out['tta_p95']} reviews={reviews}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
