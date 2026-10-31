#!/usr/bin/env python3
"""Durable-execution spike (issue #52): journaled loan-flow runner.
Each step journals (step, attempt, outcome) BEFORE reporting success; a rerun
after a kill resumes past completed steps — no step effect runs twice.
Usage:
  python engine/spike/durable_runner.py --journal /tmp/spike.journal --crash-after 2  # kill mid-flow
  python engine/spike/durable_runner.py --journal /tmp/spike.journal                   # resume -> finish
  python engine/spike/durable_runner.py --journal /tmp/spike.journal --trace engine/spike/demo-trace.json
"""
import argparse, json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent

def load_journal(p):
    p = Path(p)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

def run(args):
    flow = yaml.safe_load(open(ROOT / "examples" / "bank" / "loan-approval.flow.yaml"))
    done = {e["step"] for e in load_journal(args.journal) if e["outcome"] != "CRASHED"}
    attempts = {}
    for e in load_journal(args.journal):
        attempts[e["step"]] = attempts.get(e["step"], 0) + 1
    journal = open(args.journal, "a")
    trace = []
    for i, s in enumerate(flow["steps"], 1):
        if s["id"] in done:
            trace.append({"step": s["id"], "resumed": True})
            continue
        attempts[s["id"]] = attempts.get(s["id"], 0) + 1
        if args.crash_after and i == args.crash_after:
            journal.write(json.dumps({"step": s["id"], "attempt": attempts[s["id"]],
                                      "outcome": "CRASHED"}) + "\n")
            journal.flush()
            print(f"CRASH simulated after step {i} ({s['id']}) — rerun to resume")
            return 2
        outcome = {"workflow": "PASS", "ai": "FIELDS", "human": "APPROVE"}[s["kind"]]
        journal.write(json.dumps({"step": s["id"], "attempt": attempts[s["id"]],
                                  "outcome": outcome}) + "\n")
        journal.flush()
        trace.append({"step": s["id"], "attempt": attempts[s["id"]], "outcome": outcome})
    journal.close()
    if args.trace:
        Path(args.trace).write_text(json.dumps(
            {"flow": flow["id"], "version": flow["version"], "steps": trace,
             "effects_ran_once": sorted(done | {t["step"] for t in trace if "outcome" in t})},
            indent=1))
    n_new = sum(1 for t in trace if "outcome" in t)
    print(f"done: {n_new} new effects, {len(trace) - n_new} resumed; journal={args.journal}")
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--crash-after", type=int, default=0)
    ap.add_argument("--trace", default="")
    sys_exit = run(ap.parse_args())
    raise SystemExit(sys_exit)
