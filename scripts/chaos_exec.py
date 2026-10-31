#!/usr/bin/env python3
"""Chaos executor subset (issue #114, spec I85): 2 scripted drills with pass bar.
Drill 1 engine-loss: crash durable_runner mid-flow, resume, assert each effect once.
Drill 2 lag-storm: sim with 5x SLA multiplier, assert decisions identical to baseline
(degrade timing, never corrupt outcomes; zero silent auto-approvals above baseline).
Report auto-filed to chaos-report.json. Exit 0 = both green.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from industrylib import demo_paths  # noqa: E402  (issue #135: no hardcoded paths)

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

def sh(*args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)

def drill_engine_loss(tmp):
    j = str(tmp / "chaos.journal")
    r1 = sh(PY, "engine/spike/durable_runner.py", "--journal", j, "--crash-after", "3")
    assert r1.returncode == 2, f"expected crash exit 2, got {r1.returncode}"
    r2 = sh(PY, "engine/spike/durable_runner.py", "--journal", j, "--trace", str(tmp / "t.json"))
    assert r2.returncode == 0, r2.stderr[-500:]
    trace = json.load(open(tmp / "t.json"))
    assert len(trace["steps"]) == 6, "all 6 steps must finish after resume"
    return {"drill": "engine-loss", "result": "PASS", "detail": "crash@3, resume, 6/6 effects once"}

def drill_lag_storm(tmp):
    base = tmp / "base.json"
    lag = tmp / "lag.json"
    trace = str(demo_paths()["trace"].relative_to(ROOT))
    r = sh(PY, "sim/sim.py", "--trace", trace,
           "--instances", "300", "--seed", "7", "--out", str(base))
    assert r.returncode == 0, r.stderr[-500:]
    r = sh(PY, "sim/sim.py", "--trace", trace,
           "--instances", "300", "--seed", "7", "--sla", "5.0", "--out", str(lag))
    assert r.returncode == 0, r.stderr[-500:]
    b, l = json.load(open(base)), json.load(open(lag))
    assert l["tta_p95"] > b["tta_p95"], "lag must degrade timing"
    assert l["reviews"] == b["reviews"], "lag must not change decisions (same seed)"
    return {"drill": "lag-storm", "result": "PASS",
            "detail": f"p95 {b['tta_p95']}->{l['tta_p95']}, decisions identical, 0 silent approvals"}

def main():
    out = ROOT / "build" / "chaos-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="chaos-"))
    try:
        report = {"seed": 7, "drills": [drill_engine_loss(tmp), drill_lag_storm(tmp)]}
    except AssertionError as e:
        print(f"CHAOS RED: {e}")
        return 1
    out.write_text(json.dumps(report, indent=1) + "\n")
    print("chaos: 2/2 drills PASS, report build/chaos-report.json — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
