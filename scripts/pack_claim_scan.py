#!/usr/bin/env python3
"""Substantive-claim scanner (issue #132): a legal pack must not assert Vietnamese
law it has not verified. Every substantive-looking line needs either a same-repo
cite (`rules/...`, `flows/...`) or an explicit `placeholder:` marker.

Flags: article/clause numbers, named instruments, percentage thresholds, prison
terms with numbers, monetary penalties with numbers. Version strings, QC ids and
file paths are excluded so metadata does not trip the scanner.

Usage:  python scripts/pack_claim_scan.py [--industry legal] [--json]
        python scripts/pack_claim_scan.py --self-test
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLAIM = [
    re.compile(r"\bĐiều\s+\d+"),
    re.compile(r"\bkhoản\s+\d+"),
    re.compile(r"\bBLHS\b|\bVBHN\b|\bBộ luật\b"),
    re.compile(r"\bNghị định\s+\d+|\bThông tư\s+\d+|\bQuyết định\s+\d+"),
    re.compile(r"\b\d+\s*%"),                      # injury/interest thresholds
    re.compile(r"\b\d+\s*(?:năm|tháng)\s+tù"),     # prison term with a number
    re.compile(r"\bphạt\s+(?:tù|cải tạo)\s+\d+"),
    re.compile(r"\b\d[\d.,]*\s*(?:đồng|VND)\b"),   # monetary penalty
]
ALLOW = ("placeholder:", "rules/", "flows/", "org/", "event-examples/",
         "industries/legal/docs/")
SKIP_LINE = (
    re.compile(r"^\s*version:"), re.compile(r"qc_id"), re.compile(r"^\s*#"),
    re.compile(r"https?://"),
)


def scan_file(path):
    hits, in_fence = [], False
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or any(p.search(line) for p in SKIP_LINE):
            continue
        if any(p.search(line) for p in CLAIM) and not any(a in line for a in ALLOW):
            hits.append((i, line.strip()[:140]))
    return hits


def pack_files(indir):
    pack = indir / "pack"
    if not pack.is_dir():
        return []
    files = [pack / "rules.md"]
    files += sorted(pack.glob("skills/*/SKILL.md"))
    files += sorted(pack.glob("agents/*.md"))
    return [f for f in files if f.is_file()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--industry", default="legal")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        fixture = ROOT / "tests" / "fixtures" / "claim-industry"
        indir = fixture
        bad = []
        for f in pack_files(indir):
            bad += [(f.name, i, l) for i, l in scan_file(f)]
        classes = set()
        for name, _, line in bad:
            classes.add(("article" if "Điều" in line or "khoản" in line else
                         "instrument" if ("Bộ luật" in line or "Nghị định" in line) else
                         "percent" if "%" in line else
                         "prison" if "tù" in line else
                         "money" if ("đồng" in line or "VND" in line) else "other"))
        want = {"article", "instrument", "percent", "prison", "money"}
        if not want <= classes:
            print(f"self-test FAILED: missing classes {sorted(want - classes)}")
            return 1
        # the good file must stay clean
        good = pack_files(indir)
        clean = [f for f in good if "clean" in f.name]
        if clean and scan_file(clean[0]):
            print(f"self-test FAILED: clean file flagged: {scan_file(clean[0])}")
            return 1
        print(f"self-test: flagged {len(bad)} claims across {len(classes)} classes, clean file untouched — OK")
        return 0

    indir = ROOT / "industries" / a.industry
    if not (indir / "pack").is_dir():
        print(f"claim-scan: {a.industry} has no pack — OK")
        return 0
    report, total = {}, 0
    for f in pack_files(indir):
        hits = scan_file(f)
        if hits:
            report[str(f.relative_to(indir))] = hits
            total += len(hits)
            print(f"RED {f.relative_to(indir)}: {len(hits)} uncited substantive claim(s)")
            for i, line in hits[:8]:
                print(f"    {i}: {line}")
    if a.json:
        print(json.dumps(report, indent=1))
    if total:
        print(f"claim-scan: {total} uncited claim(s) — add a same-repo cite or a placeholder: marker")
        return 1
    print(f"claim-scan: {a.industry} pack clean (no uncited substantive claims) — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
