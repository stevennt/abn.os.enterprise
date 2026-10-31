#!/usr/bin/env python3
"""Path-independence guard (issue #135): executable tooling must not hardcode an
industry. Fails CI if a script, bin tool or workflow names `industries/<id>/`,
`examples/bank` or `examples/events`.

Allowed: historical record scripts (seed/queue generators, which describe past
loops) and fixtures. Everything that runs in CI must discover industries at runtime.

Usage: python scripts/no_hardcoded_paths.py [--self-test]
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ["scripts", "bin", "sim", "engine", "frappe"]
SCAN_FILES = [".github/workflows/validate.yml"]
# record-of-the-past generators: their job is to describe what happened, not to run
ALLOW = {"seed-issues.py", "seed-loop4.py", "make-queue.py", "queue-loop4.py",
         "no_hardcoded_paths.py"}  # the guard defines the patterns
PATTERNS = [
    (re.compile(r"industries/[a-z][a-z0-9-]*/"), "hardcoded industry path"),
    (re.compile(r"examples/bank\b|examples/events\b"), "legacy examples/ path"),
]


def offenders():
    hits = []
    files = []
    for d in SCAN_DIRS:
        files += [p for p in (ROOT / d).rglob("*")
                  if p.is_file() and p.suffix in {".py", ".js"} and "__pycache__" not in p.parts]
    files += [ROOT / f for f in SCAN_FILES if (ROOT / f).exists()]
    for f in files:
        if f.name in ALLOW:
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#") and "industries/" not in line:
                continue
            for pat, why in PATTERNS:
                if pat.search(line):
                    hits.append((f.relative_to(ROOT), i, why, line.strip()[:110]))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        if not offenders():
            print("self-test FAILED: expected zero offenders in the clean tree first")
            return 1
        print(f"self-test: {len(offenders())} offender(s) found by the same scanner — OK")
        return 0
    hits = offenders()
    if hits:
        print("PATH GUARD RED:")
        for f, i, why, line in hits[:25]:
            print(f"  {f}:{i}  {why}\n      {line}")
        print("  -> use scripts/industrylib.py (industries(), flows(), demo_paths())")
        return 1
    print("path-guard: no hardcoded industry paths in executable tooling — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
