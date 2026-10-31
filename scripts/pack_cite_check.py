#!/usr/bin/env python3
"""Pack cite check (issue #129): every rule/flow citation inside an industry pack
must resolve to a real file in the SAME industry, and any @version must match the
version declared in that file.

Replaces the cross-repo `check_enterprise_cites.py`: with content co-located, the
question is no longer "does this tag exist" but "does this id exist here, at this
version". Verified strings used to pass while the prose could still quote a stale
threshold; that class is caught by scripts/pack_rule_drift.py, and this script
catches the simpler "cited thing is gone" class.

Usage:
  python scripts/pack_cite_check.py [--industry banking] [--json]
  python scripts/pack_cite_check.py --self-test
"""
import argparse
import json
import re
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
# RULE-01@1.0.0-2026-10-01  |  RULE-01 (bare, version optional)
CITE = re.compile(r"\b([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2})@([0-9][0-9A-Za-z.\-]*)")
FLOW_CITE = re.compile(r"`(flows/[a-z0-9-]+\.flow\.yaml)`")
FILE_CITE = re.compile(r"`((?:rules|flows|org|events)/[A-Za-z0-9._-]+)`")


def load_rules(indir):
    """id -> version for every rule row in the industry."""
    out = {}
    for f in sorted((indir / "rules").glob("*.yaml")):
        try:
            pack = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        for r in (pack if isinstance(pack, list) else [pack]):
            if isinstance(r, dict) and r.get("id"):
                out[str(r["id"])] = str(r.get("version", ""))
    return out


def load_flows(indir):
    return {p.name: p for p in sorted((indir / "flows").glob("*.flow.yaml"))}


def content_files(pack_dir):
    files = [pack_dir / "rules.md"]
    files += sorted((pack_dir / "skills").glob("*/SKILL.md"))
    files += sorted((pack_dir / "agents").glob("*.md"))
    return [f for f in files if f.is_file()]


def check(indir, pack_dir):
    rules, flows = load_rules(indir), load_flows(indir)
    errors, checked = [], 0
    for f in content_files(pack_dir):
        rel = f.relative_to(pack_dir)
        text = f.read_text()
        for rid, ver in CITE.findall(text):
            checked += 1
            if rid not in rules:
                errors.append(f"{rel}: cites unknown rule {rid} (not in {indir.name}/rules/)")
                continue
            want = rules[rid]
            if ver != want:
                errors.append(f"{rel}: {rid}@{ver} but rules declare {want}")
        for name in FLOW_CITE.findall(text):
            checked += 1
            if Path(name).name not in flows:
                errors.append(f"{rel}: cites unknown flow {name}")
        for ref in FILE_CITE.findall(text):
            checked += 1
            if not (indir / ref).exists():
                errors.append(f"{rel}: cites missing file {ref}")
    return errors, checked, len(rules), len(flows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--industry")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        fix = ROOT / "tests" / "fixtures" / "cite-industry"
        errs, n, nr, nf = check(fix, fix / "pack")
        if not errs:
            print("self-test FAILED: stale fixture should be red")
            return 1
        kinds = {("stale-version" if "but rules declare" in e else
                  "unknown-rule" if "unknown rule" in e else
                  "unknown-flow" if "unknown flow" in e else "missing-file")
                 for e in errs}
        want = {"stale-version", "unknown-rule", "unknown-flow", "missing-file"}
        if not want <= kinds:
            print(f"self-test FAILED: expected {sorted(want)}, got {sorted(kinds)}")
            return 1
        print(f"self-test: {len(errs)} errors, all 4 classes caught — OK")
        return 0

    inds = ([ROOT / "industries" / a.industry] if a.industry
            else sorted(p for p in (ROOT / "industries").iterdir() if p.is_dir()))
    report, failures = {}, 0
    for indir in inds:
        pack = indir / "pack"
        if not pack.is_dir():
            print(f"skip {indir.name}: no pack (status not active)")
            continue
        errs, n, nr, nf = check(indir, pack)
        report[indir.name] = errs
        print(f"{'OK' if not errs else 'RED':3} {indir.name}: {n} cites, "
              f"{nr} rules, {nf} flows")
        for e in errs[:10]:
            print(f"    - {e}")
        failures += bool(errs)
    if a.json:
        print(json.dumps(report, indent=1))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
