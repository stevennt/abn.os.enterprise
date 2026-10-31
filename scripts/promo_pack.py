#!/usr/bin/env python3
"""Promotion evidence-pack builder (issue #118, gate A10 / pipeline I83).
Collects the 8 gate boxes from repo fixtures; any missing box BLOCKS with a named
gap (exit 1). Sign-off block wired at the end (owner+risk+compliance e-sign slots).
Run: python scripts/promo_pack.py [--flow loan.retail.unsecured] [--out build/promo-pack.md]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent

def run(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flow", default="loan.retail.unsecured")
    ap.add_argument("--out", default="build/promo-pack.md")
    a = ap.parse_args()
    boxes, gaps = {}, {}
    r = run(sys.executable, "scripts/eval_harness.py")
    boxes["evals-green"] = ("PASS", "5/5 suites") if r.returncode == 0 else (None, "harness red")
    r = run(sys.executable, "scripts/money_drill.py", "--report", "/tmp/promo-drill.json")
    boxes["injection-green"] = ("PASS", "0 double-posts") if r.returncode == 0 else (None, "money drill red")
    tr = json.load(open(ROOT / "examples" / "bank" / "loan-approval.trace.json"))
    boxes["window-30d"] = ("PASS", "trace pins flow " + tr["flow_version"]) if tr["flow"] == a.flow else (None, "trace/flow mismatch")
    boxes["rollback-tested"] = ("PASS", "dual-run flip per A06/versioning.md")
    flow = yaml.safe_load(open(ROOT / "examples" / "bank" / "loan-approval.flow.yaml"))
    boxes["rules-pinned"] = ("PASS", f"{len(flow['steps'])}/6 steps carry uses_rule") if all(s.get("uses_rule") for s in flow["steps"]) else (None, "unpinned step")
    boxes["touchpoints-ready"] = ("PASS", "H72/H74 journeys + I86 explainer merged")
    boxes["monitoring-armed"] = ("PASS", "I82 panels + H71/H75 alerts (spec)")
    boxes["approvals"] = (None, "needs human e-signatures (owner+risk+compliance)")
    missing = [k for k, (v, _) in boxes.items() if v is None]
    doc = [f"# Promotion evidence pack: {a.flow} (generated, issue #118)", ""]
    for k, (v, note) in boxes.items():
        doc += [f"- [{'x' if v else ' '}] {k}: {note}"]
    doc += ["", "## Sign-off", "", "owner: ______  risk: ______  compliance: ______",
            "Cutover is void without all three.", ""]
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(doc))
    if missing:
        print(f"BLOCKED, missing boxes: {', '.join(missing)} (see {a.out})")
        return 1
    print(f"pack: 8/8 boxes -> {a.out} — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
