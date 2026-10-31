#!/usr/bin/env python3
"""Pack→rule drift check (issue #140, closes the loop-4 motivation).

The retired cross-repo checker compared VERSION STRINGS. This one compares VALUES:
if pack prose states a numeric threshold next to a rule id, every such number must
appear in that rule's own table/effect. A policy change that forgets the prose now
fails CI instead of quietly teaching the model an old number.

Scope: lines that name a rule id (`AML-SCREEN-02@…`, or `rules/x.yaml` + id) and
carry numbers. Agent frontmatter (temperature/steps) is not policy and is excluded.
Versions, tag names and dates are scrubbed before comparison.

Usage: python scripts/pack_rule_drift.py [--industry banking] [--json]
       python scripts/pack_rule_drift.py --self-test
"""
import argparse
import json
import re
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
RULE_REF = re.compile(r"\b([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2})\b")
NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(%|x)?")
SCRUB = [
    re.compile(r"@\d[0-9A-Za-z.\-]*"),          # @version
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),        # dates
    re.compile(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2}\b"),  # rule ids themselves
    re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b"),  # tag names
    re.compile(r"v?\d+\.\d+\.\d+"),              # semver
]


def rule_numbers(row):
    """Policy values a rule declares: numbers from its table cells only.

    Deliberately NOT the whole row: authority/version text carries years, ids and
    tag numbers which would widen the allowed set and let real drift through.
    """
    nums = set()
    for cell in (row.get("table") or []):
        blob = yaml.safe_dump(cell, allow_unicode=True, sort_keys=True)
        nums |= {n for n in re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)", blob)}
    return nums


def load_rules(indir):
    out = {}
    for f in sorted((indir / "rules").glob("*.yaml")):
        try:
            pack = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        for r in (pack if isinstance(pack, list) else [pack]):
            if isinstance(r, dict) and r.get("id"):
                out[str(r["id"])] = (r, f.name)
    return out


def prose_lines(pack_dir):
    """Pack prose that may state policy: rules.md and each skill body."""
    files = [pack_dir / "rules.md"] + sorted(pack_dir.glob("skills/*/SKILL.md"))
    out = []
    for f in files:
        if not f.is_file():
            continue
        text = f.read_text()
        if f.name == "SKILL.md":                 # skip YAML frontmatter
            m = re.match(r"\A---\s*\n.*?\n---\s*\n", text, re.S)
            text = text[m.end():] if m else text
        for i, line in enumerate(text.splitlines(), 1):
            out.append((f, i, line))
    return out


def scrub(line):
    for pat in SCRUB:
        line = pat.sub(" ", line)
    return line


def check(indir, pack_dir):
    rules = load_rules(indir)
    problems, compared = [], 0
    for f, lineno, line in prose_lines(pack_dir):
        ids = [rid for rid in RULE_REF.findall(line) if rid in rules]
        if not ids:
            continue
        nums = [m.group(1) for m in NUM.finditer(scrub(line))]
        if not nums:
            continue
        allowed = set()
        for rid in ids:
            allowed |= rule_numbers(rules[rid][0])
        for n in nums:
            compared += 1
            if n not in allowed:
                problems.append(
                    f"{f.relative_to(pack_dir)}:{lineno}: prose says {n} but "
                    f"{'/'.join(ids)} declares {sorted(allowed)}")
    return problems, compared, len(rules)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--industry", default="banking")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        fix = ROOT / "tests" / "fixtures" / "drift-industry"
        problems, compared, _ = check(fix, fix / "pack")
        if not problems:
            print("self-test FAILED: drifted prose was accepted")
            return 1
        if "0.95" not in " ".join(problems):
            print(f"self-test FAILED: wrong diagnosis: {problems[:2]}")
            return 1
        print(f"self-test: drift caught ({len(problems)} mismatch, {compared} numbers compared) — OK")
        return 0

    indir = ROOT / "industries" / a.industry
    if not (indir / "pack").is_dir():
        print(f"drift-check: {a.industry} has no pack — OK")
        return 0
    problems, compared, nrules = check(indir, indir / "pack")
    if a.json:
        print(json.dumps({"industry": a.industry, "numbers_compared": compared,
                          "problems": problems}, indent=1))
    if problems:
        print("DRIFT RED:")
        for p in problems[:15]:
            print(f"  - {p}")
        print("  -> change the prose or the rule, but not silently one of them")
        return 1
    if compared == 0:
        print(f"drift-check: {a.industry} pack states no thresholds "
              f"(nothing to drift) — OK")
        return 0
    print(f"drift-check: {a.industry} {compared} threshold(s) in prose match "
          f"{nrules} rules — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
