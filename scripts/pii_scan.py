#!/usr/bin/env python3
"""PII scanner (issue #109, policy D33): fail on bare CCCD-shaped runs.
Flags exactly-12-digit runs (CCCD shape) outside allowlisted contexts.
Amounts (9-11 digits, VND-marked lines) are excluded by design — documented
deviation from the D33 sketch, which named \\b\\d{9,12}\\b: amounts need 9-11
digits in docs, CCCD is exactly 12.
Usage: python scripts/pii_scan.py [--self-test]
  default: scan repo, exit 1 on findings. --self-test: fixture must go red.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAT = re.compile(r"\b\d{12}\b")
CTX_OK = re.compile(r"(?i)(vnd|amount|limit|budget|portfolio|txn|sha|hash|seed|port|version|phone-mask)")
FILE_OK = ("examples/events/", "golden.jsonl", "tests/fixtures/", "MANIFEST",
           "pii-violation", ".git/", "queue", "queue-loop2")

def scan(paths, force=False):
    hits = []
    for p in paths:
        rel = str(p.relative_to(ROOT)) if p.is_absolute() else str(p)
        if not force and any(k in rel for k in FILE_OK):
            continue
        try:
            text = (ROOT / rel).read_text(errors="replace").splitlines()
        except (IsADirectoryError, UnicodeDecodeError):
            continue
        for i, line in enumerate(text, 1):
            if PAT.search(line) and not CTX_OK.search(line):
                hits.append(f"{rel}:{i}: {line.strip()[:90]}")
    return hits

def tracked():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    return [ROOT / l for l in out.stdout.splitlines()
            if l.split(".")[-1] in ("md", "yaml", "yml", "json", "py", "js", "txt", "sql", "fga", "csv")]

def main():
    if "--self-test" in sys.argv:
        hits = scan([ROOT / "tests" / "fixtures" / "pii-violation.txt"], force=True)
        print(f"self-test: fixture flagged ({len(hits)} hits) — OK" if hits else "self-test FAILED: clean")
        return 0 if hits else 1
    hits = scan(tracked())
    if hits:
        print("PII SCAN RED:")
        print("\n".join(hits[:20]))
        return 1
    print("pii-scan: clean — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
