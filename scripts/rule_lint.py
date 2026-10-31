#!/usr/bin/env python3
"""Rule lint (issue #110, ADR E41): every pack row needs when+then, no duplicate
`when` within a rule (overlap proxy), tables non-empty, wildcard coverage row present.
Usage: python scripts/rule_lint.py [--self-test]
  default: lint rules/*.yaml (skip fixtures), exit 1 on problems.
  --self-test: lint tests/fixtures/rule-overlap.yaml, expect RED (exit 0 if red).
"""
import glob
import sys
import yaml

def lint_file(path):
    pack = yaml.safe_load(open(path))
    problems = []
    for r in (pack if isinstance(pack, list) else [pack]):
        rid = r.get("id", "?")
        table = r.get("table") or []
        if not table:
            problems.append(f"{rid}: empty table")
            continue
        whens = [row.get("when") for row in table]
        if any(not w for w in whens) or any("then" not in row for row in table):
            problems.append(f"{rid}: row missing when/then")
        dupes = {w for w in whens if whens.count(w) > 1}
        if dupes:
            problems.append(f"{rid}: overlapping when-rows: {sorted(dupes)}")
        if not any("*" in (w or "") for w in whens):
            problems.append(f"{rid}: no wildcard (*) coverage row (gap risk)")
    return problems

def main():
    if "--self-test" in sys.argv:
        bad = lint_file("tests/fixtures/rule-overlap.yaml")
        print(f"self-test: fixture flagged ({bad}) — OK" if bad else "self-test FAILED: clean")
        return 0 if bad else 1
    problems = []
    for f in sorted(glob.glob("rules/*.yaml")):
        problems += [f"{f}: {p}" for p in lint_file(f)]
    if problems:
        print("RULE LINT RED:")
        print("\n".join(problems[:20]))
        return 1
    print("rule-lint: packs covered, no overlaps — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
