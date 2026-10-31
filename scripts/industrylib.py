#!/usr/bin/env python3
"""Industry discovery helpers (issue #135) — one place that knows the layout.

Every tool asked "which industry?" here instead of hardcoding a path, so industry
#3 is picked up by globbing, not by editing thirteen scripts.

CLI:
  python scripts/industrylib.py --list                 # id, tier, counts
  python scripts/industrylib.py --demo-paths [--shell] # canonical demo assets
  python scripts/industrylib.py --flows [--industry X] # flow ids and paths
"""
import argparse
import json
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
IND = ROOT / "industries"

# The one flow used for demos (chaos, sim determinism, migration fixtures). Named by
# ID, never by path, so moving or renaming the file cannot silently break CI.
DEMO_FLOW_ID = "loan.retail.unsecured"


def industries():
    """[(id, manifest, indir)] sorted by id."""
    out = []
    for m in sorted(IND.glob("*/industry.yaml")):
        out.append((m.parent.name, yaml.safe_load(m.read_text()) or {}, m.parent))
    return out


def industry(id_):
    for iid, man, indir in industries():
        if iid == id_:
            return iid, man, indir
    raise KeyError(f"unknown industry '{id_}' (known: {[i for i, _, _ in industries()]})")


def flows(id_=None):
    """[(industry_id, flow_id, path)] across one or all industries."""
    out = []
    for iid, _, indir in (industries() if id_ is None else [industry(id_)]):
        for f in sorted((indir / "flows").glob("*.flow.yaml")):
            try:
                flow = yaml.safe_load(f.read_text()) or {}
            except yaml.YAMLError:
                continue
            out.append((iid, str(flow.get("id") or f.stem), f))
    return out


def rules(id_=None):
    out = []
    for iid, _, indir in (industries() if id_ is None else [industry(id_)]):
        out += [(iid, f) for f in sorted((indir / "rules").glob("*.yaml"))]
    return out


def event_examples(id_=None):
    out = []
    for iid, _, indir in (industries() if id_ is None else [industry(id_)]):
        out += [(iid, f) for f in sorted((indir / "event-examples").glob("*.json"))]
    return out


def traces(id_=None):
    out = []
    for iid, _, indir in (industries() if id_ is None else [industry(id_)]):
        out += [(iid, f) for f in sorted((indir / "flows").glob("*.trace.json"))]
    return out


def evals(id_=None):
    out = []
    for iid, _, indir in (industries() if id_ is None else [industry(id_)]):
        out += [(iid, f) for f in sorted((indir / "evals").glob("*/README.md"))]
    return out


def demo_paths():
    """Canonical demo assets: the DEMO_FLOW_ID flow, its trace and its event example."""
    match = [(iid, fid, p) for iid, fid, p in flows() if fid == DEMO_FLOW_ID]
    if not match:
        # fall back to the flow with the most steps, so a fresh repo still demos
        best = None
        for iid, fid, p in flows():
            n = len((yaml.safe_load(p.read_text()) or {}).get("steps") or [])
            if not best or n > best[0]:
                best = (n, iid, fid, p)
        if not best:
            raise SystemExit("no flows found")
        match = [(best[1], best[2], best[3])]
    iid, fid, flow_path = match[0]
    trace = flow_path.with_name(flow_path.name.replace(".flow.yaml", ".trace.json"))
    flow = yaml.safe_load(flow_path.read_text()) or {}
    ref = (flow.get("inputs") or {}).get("schema_ref")
    event = None
    if ref:
        cand = flow_path.parent.parent / ref
        if cand.exists():
            event = cand
    if event is None:
        ev = event_examples(iid)
        event = ev[0][1] if ev else None
    return {"industry": iid, "flow_id": fid, "flow": flow_path,
            "trace": trace, "event": event}


def _rel(p):
    try:
        return str(Path(p).relative_to(ROOT))
    except (ValueError, TypeError):
        return str(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--demo-paths", action="store_true")
    ap.add_argument("--flows", action="store_true")
    ap.add_argument("--shell", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--industry")
    a = ap.parse_args()

    if a.demo_paths:
        d = demo_paths()
        if a.shell:
            print(f"DEMO_INDUSTRY={d['industry']}")
            print(f"DEMO_FLOW={_rel(d['flow'])}")
            print(f"DEMO_TRACE={_rel(d['trace'])}")
            print(f"DEMO_EVENT={_rel(d['event']) if d['event'] else ''}")
            return 0
        print(json.dumps({k: _rel(v) if v else None for k, v in d.items()}, indent=1))
        return 0

    if a.flows:
        rows = [{"industry": i, "flow_id": f, "path": _rel(p)}
                for i, f, p in flows(a.industry)]
        print(json.dumps(rows, indent=1) if a.json else
              "\n".join(f"{r['industry']:9} {r['flow_id']:32} {r['path']}" for r in rows))
        return 0

    # default: inventory
    rows = []
    for iid, man, indir in industries():
        rows.append({"industry": iid, "tier": man.get("tier"),
                     "flows": len(list((indir / "flows").glob("*.flow.yaml"))),
                     "rules": len(list((indir / "rules").glob("*.yaml"))),
                     "pack": (man.get("pack") or {}).get("status", "absent")})
    if a.json:
        print(json.dumps(rows, indent=1))
    else:
        for r in rows:
            print(f"{r['industry']:9} tier={r['tier']:10} flows={r['flows']:2} "
                  f"rules={r['rules']:2} pack={r['pack']}")
        print(f"{len(rows)} industries, {sum(r['flows'] for r in rows)} flows, "
              f"{sum(r['rules'] for r in rows)} rule files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
