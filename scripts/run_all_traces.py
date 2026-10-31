#!/usr/bin/env python3
"""Trace all flows (issue #111): dry-run every *.flow.yaml against a synthetic
event (existing example matched by event_type, else minimal synthesized payload),
verify each audit chain, write <flow>.trace.json next to the flow.
Usage: python scripts/run_all_traces.py. Exit 0 when all traces verify.
Gaps (flows without a curated example) are listed — file them as issues.
"""
import glob
import json
import sys
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_chain import append, verify

ROOT = Path(__file__).resolve().parent.parent
OUTCOMES = {"workflow": "PASS", "ai": "FIELDS", "human": "APPROVE"}

def synth_value(field):
    f = field.lower()
    if "amount" in f or "limit" in f:
        return 100000000
    if "term" in f or "tenor" in f or "month" in f or "days" in f or "cycle" in f:
        return 12
    if "score" in f or "rate" in f or "ltv" in f:
        return 0.5
    if field.endswith("_id") or field in ("cccd", "txn_id", "batch_id", "call_id"):
        return f"TEST-{field.upper()}-1"
    if "date" in f or "period" in f:
        return "2026-10-01"
    if field == "lines":
        return [{"payee": "TEST", "amount": 1000000}]
    if field.endswith("_docs") or field == "fields":
        return ["test.pdf"]
    return f"TEST-{field}"

def main():
    examples = {}
    for f in glob.glob(str(ROOT / "industries" / "*" / "event-examples" / "*.json")):
        ev = json.load(open(f))
        examples[ev["event_type"]] = ev
    gaps, n = [], 0
    for f in sorted(glob.glob(str(ROOT / "industries" / "*" / "flows" / "*.flow.yaml"))):
        flow = yaml.safe_load(open(f))
        ev = examples.get(flow["event_type"])
        if ev is None:
            gaps.append(flow["id"])
            fields = (flow.get("inputs") or {}).get("fields", [])
            ev = {"event_type": flow["event_type"], "event_version": "1.0.0",
                  "producer": "synth:run-all-traces", "idempotency_key": f"TEST-{flow['id']}",
                  "payload": {fld: synth_value(fld) for fld in fields},
                  "_synthetic_pii": True, "ts": 1793422800}
        chain, steps = [], []
        for i, s in enumerate(flow["steps"], 1):
            rules = s.get("uses_rule") or []
            env = append(chain, s["id"], s["owner_role"], OUTCOMES[s["kind"]],
                         rules[0] if rules else None,
                         f"model-for-{s['id']}@test" if s["kind"] == "ai" else None, i)
            steps.append({"step_id": s["id"], "kind": s["kind"], "outcome": env["decision"]})
        ok, msg = verify(chain)
        assert ok, f"{flow['id']}: {msg}"
        trace = {"instance_id": f"trace-{flow['id']}", "flow": flow["id"],
                 "flow_version": flow["version"], "event_type": flow["event_type"],
                 "event_idem": ev["idempotency_key"], "synthesized_event": flow["event_type"] not in examples,
                 "steps": steps, "audit": chain}
        Path(f.replace(".flow.yaml", ".trace.json")).write_text(json.dumps(trace, ensure_ascii=False, indent=1))
        n += 1
    print(f"traces: {n} flows, all chains verify")
    if gaps:
        print(f"GAPS (synthesized events — file curated examples): {', '.join(gaps)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
