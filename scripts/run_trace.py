#!/usr/bin/env python3
"""Dry-run a flow against a synthetic event -> trace + audit chain (issue #22).
Usage: python scripts/run_trace.py <flow.yaml> <event.json> <out.trace.json>
Exit 0 when the trace walks every step in order with a verifiable chain.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml
from audit_chain import append, verify

OUTCOMES = {"workflow": "PASS", "ai": "FIELDS", "human": "APPROVE"}

def main():
    flow = yaml.safe_load(open(sys.argv[1]))
    event = json.load(open(sys.argv[2]))
    chain, steps = [], []
    ts = event.get("ts", 0)
    for i, s in enumerate(flow["steps"], 1):
        rules = s.get("uses_rule") or []
        models = [f"model-for-{s['id']}@2026-10-20"] if s["kind"] == "ai" else [None]
        env = append(chain, s["id"], s["owner_role"], OUTCOMES[s["kind"]],
                     rules[0] if rules else None, models[0], ts + i)
        steps.append({"step_id": s["id"], "kind": s["kind"], "owner": s["owner_role"],
                      "level": s["level"], "sla_minutes": s["sla_minutes"],
                      "on_fail": s["on_fail"], "outcome": env["decision"]})
    ok, msg = verify(chain)
    assert ok, msg
    trace = {"instance_id": "trace-demo-1", "flow": flow["id"], "flow_version": flow["version"],
             "event_type": flow["event_type"], "event_idem": event["idempotency_key"],
             "steps": steps, "audit": chain}
    assert [s["step_id"] for s in steps] == [s["id"] for s in flow["steps"]]
    Path(sys.argv[3]).write_text(json.dumps(trace, ensure_ascii=False, indent=1))
    print(f"trace: {len(steps)} steps in order, chain {msg}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
