#!/usr/bin/env python3
"""Metamodel v1.0.0 validator (issue #1).
Green path: schemas require `version`; loan-approval.flow.yaml validates.
Red path:  --self-test feeds an invalid flow (no version) and MUST fail.
Exit 0 = green, 1 = red. Used by .github/workflows/validate.yml.
"""
import sys
from pathlib import Path
import glob as _glob
import yaml
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = ["org", "process", "rule", "event", "touchpoint", "audit"]

def load(p):
    return yaml.safe_load((ROOT / p).read_text())

def main():
    self_test = "--self-test" in sys.argv
    schemas = {s: load(f"metamodel/{s}.schema.yaml") for s in SCHEMAS}
    # Acceptance #3: `version` mandatory in all 5 schemas
    for s, sc in schemas.items():
        assert "version" in sc.get("required", []), f"{s} schema lacks required version"
    print(f"meta: all {len(schemas)} schemas require `version` — OK")
    # Issue #3: every schema links glossary terms, and all linked terms exist
    import re
    gtext = (ROOT / "docs" / "glossary.md").read_text()
    terms = set(t.rstrip(":") for t in re.findall(r"^- \*\*(.+?)\*\*", gtext, re.M))
    assert terms, "no glossary terms parsed"
    for s, sc in schemas.items():
        linked = sc.get("x-glossary", [])
        assert linked, f"{s} schema has no x-glossary links"
        unknown = [t for t in linked if t not in terms]
        assert not unknown, f"{s} links unknown terms: {unknown}"
    print(f"glossary: {len(schemas)} schemas link {sum(len(sc.get('x-glossary', [])) for sc in schemas.values())} terms, all defined ({len(terms)} terms) — OK")
    # Acceptance #1: worked example validates green (+ every flow file, issue #21)
    for f in sorted(_glob.glob(str(ROOT / "examples" / "bank" / "*.flow.yaml"))):
        flow = load(str(Path(f).relative_to(ROOT)))
        jsonschema.validate(flow, schemas["process"])
        print(f"flow: {Path(f).name} validates against process v1.0.0 — OK")
    # Index hygiene (full RACI per unit is B11/B20, not this issue)
    catalog = load("examples/bank/process-catalog.yaml")
    n = sum(len(v) for v in catalog.values())
    assert n == 46, f"catalog has {n} processes, want 46"
    print(f"catalog: {n} processes indexed — OK")
    org = load("examples/bank/org-chart.yaml")
    assert all(all(k in u for k in ("id", "name", "headcount_plan")) for u in org), "org index rows incomplete"
    print(f"org-index: {len(org)} units (full RACI -> B11/B20) — OK")
    # Issue #11+: full unit files validate against the org schema
    for f in sorted(_glob.glob(str(ROOT / "examples" / "bank" / "org-*.yaml"))):
        if Path(f).name == "org-chart.yaml":
            continue  # index only; full RACI lives in org-<unit>.yaml (B11-B20)
        units = yaml.safe_load(open(f))
        units = units if isinstance(units, list) else [units]
        for u in units:
            jsonschema.validate(u, schemas["org"])
        print(f"org-full: {Path(f).name} ({len(units)} units) validates — OK")
    # Issue #20: index-vs-full reconciliation (closes track B)
    full_units = {}
    for f in sorted(_glob.glob(str(ROOT / "examples" / "bank" / "org-*.yaml"))):
        if Path(f).name == "org-chart.yaml":
            continue
        units = yaml.safe_load(open(f))
        for u in (units if isinstance(units, list) else [units]):
            assert u["id"] not in full_units, f"duplicate unit {u['id']}"
            full_units[u["id"]] = u
    idx_ids = {u["id"] for u in org}
    assert idx_ids == set(full_units), f"index/full mismatch: {idx_ids ^ set(full_units)}"
    bad_hc = [i for i in idx_ids
              if next(u for u in org if u["id"] == i)["headcount_plan"] != full_units[i]["headcount_plan"]]
    assert not bad_hc, f"headcount mismatch: {bad_hc}"
    total = sum(u["headcount_plan"] for u in org)
    print(f"org-reconcile: {len(idx_ids)} index units == full files, headcounts match (total plan {total}) — OK")
    # Issue #8: 5 reference payloads validate + are marked synthetic
    import json as _json
    evdir = ROOT / "examples" / "events"
    evfiles = sorted(evdir.glob("*.json"))
    assert len(evfiles) == 5, f"want 5 event examples, found {len(evfiles)}"
    semver = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
    for f in evfiles:
        ev = _json.loads(f.read_text())
        for k in ("event_type", "event_version", "producer", "idempotency_key", "payload"):
            assert k in ev, f"{f.name} missing {k}"
        assert semver.match(ev["event_version"]), f"{f.name} bad event_version"
        assert isinstance(ev["payload"], dict) and ev["payload"], f"{f.name} empty payload"
        assert ev.get("_synthetic_pii") is True, f"{f.name} not marked synthetic"
    print(f"events: {len(evfiles)} examples validate, all marked synthetic — OK")
    # Issue #18: capacity CSV per role parses with sane numbers
    import csv as _csv
    cap = list(_csv.DictReader(open(ROOT / "engine" / "capacity.csv")))
    assert len(cap) >= 15, f"want >=15 capacity rows, found {len(cap)}"
    for r in cap:
        assert int(r["headcount"]) > 0 and float(r["mins_per_task"]) > 0, f"bad row {r['role']}"
        assert 0 < float(r["utilization"]) <= 0.9, f"utilization out of range {r['role']}"
    print(f"capacity: {len(cap)} roles with throughput + assumptions — OK")
    # Issue #22: runnable-spec trace — 6 steps in order, chain verifies
    import json as _json2
    tr = _json2.loads((ROOT / "examples" / "bank" / "loan-approval.trace.json").read_text())
    loan = load("examples/bank/loan-approval.flow.yaml")
    assert [s["step_id"] for s in tr["steps"]] == [s["id"] for s in loan["steps"]], "trace/flow step mismatch"
    assert tr["flow_version"] == loan["version"], "trace pins stale flow version"
    for s in loan["steps"]:
        assert s.get("owner_role") and s.get("sla_minutes") and s.get("on_fail"), f"step {s['id']} incomplete"
        assert s.get("uses_rule"), f"step {s['id']} has no rule"
    prev = "GENESIS"
    import hashlib as _hl
    for i, env in enumerate(tr["audit"]):
        assert env["seq"] == i and env["hash_prev"] == prev, f"audit link broken at {i}"
        body = {k: v for k, v in env.items() if k != "hash"}
        assert env["hash"] == _hl.sha256(_json2.dumps(body, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False).encode()).hexdigest(), f"audit hash bad at {i}"
        prev = env["hash"]
    print(f"trace: {len(tr['steps'])} steps, audit chain verifies, all steps have owner/rule/SLA/fail-path — OK")
    readme = (ROOT / "README.md").read_text().splitlines()
    start = next(i for i, l in enumerate(readme) if l.startswith("## Repo map"))
    o = readme.index("```", start) + 1
    fence = readme[o:readme.index("```", o)]
    missing = [l.split()[0] for l in fence if l.strip() and not (ROOT / l.split()[0]).exists()]
    assert not missing, f"README map points at missing paths: {missing}"
    print(f"readme-map: {len(fence)} entries all exist — OK")
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
