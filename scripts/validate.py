#!/usr/bin/env python3
"""Metamodel v1.0.0 validator (issue #1).
Green path: schemas require `version`; loan-approval.flow.yaml validates.
Red path:  --self-test feeds an invalid flow (no version) and MUST fail.
Exit 0 = green, 1 = red. Used by .github/workflows/validate.yml.
"""
import sys
from pathlib import Path
import yaml
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ["org", "process", "rule", "event", "touchpoint"]

def load(p):
    return yaml.safe_load((ROOT / p).read_text())

def main():
    self_test = "--self-test" in sys.argv
    schemas = {s: load(f"metamodel/{s}.schema.yaml") for s in SCHEMAS}
    # Acceptance #3: `version` mandatory in all 5 schemas
    for s, sc in schemas.items():
        assert "version" in sc.get("required", []), f"{s} schema lacks required version"
    print("meta: all 5 schemas require `version` — OK")
    # Acceptance #1: worked example validates green
    flow = load("examples/bank/loan-approval.flow.yaml")
    jsonschema.validate(flow, schemas["process"])
    print("flow: loan-approval.flow.yaml validates against process v1.0.0 — OK")
    # Index hygiene (full RACI per unit is B11/B20, not this issue)
    catalog = load("examples/bank/process-catalog.yaml")
    n = sum(len(v) for v in catalog.values())
    assert n == 46, f"catalog has {n} processes, want 46"
    print(f"catalog: {n} processes indexed — OK")
    org = load("examples/bank/org-chart.yaml")
    assert all(all(k in u for k in ("id", "name", "headcount_plan")) for u in org), "org index rows incomplete"
    print(f"org-index: {len(org)} units (full RACI -> B11/B20) — OK")
    if self_test:
        # Acceptance #2 logic: an invalid flow MUST fail validation
        bad = dict(flow)
        bad.pop("version", None)
        try:
            jsonschema.validate(bad, schemas["process"])
        except jsonschema.ValidationError as e:
            print(f"self-test: invalid flow correctly REJECTED ({e.message[:80]}) — OK")
            return 0
        print("self-test FAILED: invalid flow was accepted")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
