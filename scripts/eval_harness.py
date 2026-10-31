#!/usr/bin/env python3
"""Eval harness (issue #67): one runner over all AI-step suites.
Checks per contract: eval dir + README with Targets + any test_*.py green.
Run: python scripts/eval_harness.py [--strict]. Exit 0 = green.
"""
import re, subprocess, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent

def main():
    strict = "--strict" in sys.argv
    contracts = sorted((ROOT / "ai").glob("*.contract.yaml"))
    assert contracts, "no AI contracts found"
    failed = 0
    for c in contracts:
        ct = yaml.safe_load(open(c))
        suite = ROOT / ct["eval_suite"].rstrip("/")
        name = ct["step_id"]
        problems = []
        if not suite.is_dir():
            problems.append("eval dir missing")
        else:
            readme = suite / "README.md"
            if not readme.exists() or "Target" not in readme.read_text():
                problems.append("README without Targets")
            for t in sorted(suite.glob("test_*.py")):
                r = subprocess.run([sys.executable, str(t)], capture_output=True, text=True)
                if r.returncode != 0:
                    problems.append(f"{t.name} FAILED")
        if strict and "golden" not in (suite / "README.md").read_text().lower():
            problems.append("no golden-size claim")
        print(f"{'PASS' if not problems else 'FAIL'}: {name} ({c.name})"
              + (f" — {'; '.join(problems)}" if problems else ""))
        failed += bool(problems)
    print(f"harness: {len(contracts) - failed}/{len(contracts)} suites green")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
