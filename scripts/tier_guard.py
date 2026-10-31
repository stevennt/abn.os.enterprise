#!/usr/bin/env python3
"""Classification guard (issue #134): this repo hosts public/commercial only.

Fails if any industries/<id>/industry.yaml declares restricted|classified, and
prints the repo-split path instead of a generic error. Also refuses a manifest whose
tier disagrees with a `tier_override`-style escape hatch (there is none by design).

Usage: python scripts/tier_guard.py [--json]
       python scripts/tier_guard.py --self-test
"""
import argparse
import json
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
HOSTED = ("public", "commercial")
SPLIT_NOTE = (
    "restricted/classified industries must live in their own repo with a vendored "
    "metamodel copy — see docs/core/confidentiality.md")


def scan(root=ROOT / "industries"):
    problems = []
    for m in sorted(root.glob("*/industry.yaml")):
        iid = m.parent.name
        man = yaml.safe_load(m.read_text()) or {}
        tier = man.get("tier")
        if tier not in HOSTED:
            problems.append(f"{iid}: tier '{tier}' not hosted here — {SPLIT_NOTE}")
        if "tier_override" in man or "tier_note" in man:
            problems.append(f"{iid}: tier overrides are not allowed (tier is the contract)")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        fix = ROOT / "tests" / "fixtures" / "tier-split"
        problems = scan(fix)
        if not problems:
            print("self-test FAILED: restricted/classified manifests were accepted")
            return 1
        if not any("not hosted here" in p for p in problems):
            print(f"self-test FAILED: wrong message: {problems[:1]}")
            return 1
        print(f"self-test: {len(problems)} manifest(s) refused with the split path — OK")
        return 0

    problems = scan()
    if a.json:
        print(json.dumps(problems, indent=1))
    if problems:
        print("TIER GUARD RED:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"tier-guard: all industries hosted here are {HOSTED} — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
