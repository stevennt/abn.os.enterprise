#!/usr/bin/env python3
"""Playbook/CI sync (issue #138): the onboarding playbook must mention every script
that CI actually runs, or it stops being a checklist and becomes decoration.

Usage: python scripts/playbook_sync.py [--json]
       python scripts/playbook_sync.py --self-test
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CI = ROOT / ".github" / "workflows" / "validate.yml"
DOC = ROOT / "docs" / "core" / "onboarding-industry.md"


def ci_scripts(text):
    """Every scripts/… or bin/… invocation in the workflow's run steps."""
    found = set()
    for m in re.finditer(r"(scripts/[a-z0-9_/]+\.py|bin/[a-z-]+(?:\.py)?)", text):
        found.add(m.group(1))
    return sorted(found)


def missing(ci_text, doc_text, ignore=()):
    return [s for s in ci_scripts(ci_text) if s not in doc_text and s not in ignore]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        ci_text = "run: python scripts/validate.py && python scripts/ghost_check.py"
        doc_text = "run python scripts/validate.py"
        gaps = missing(ci_text, doc_text)
        if gaps != ["scripts/ghost_check.py"]:
            print(f"self-test FAILED: expected the ghost script, got {gaps}")
            return 1
        print("self-test: an undocumented CI script is detected — OK")
        return 0

    ci_text, doc_text = CI.read_text(), DOC.read_text()
    gaps = missing(ci_text, doc_text)
    total = len(ci_scripts(ci_text))
    if a.json:
        print(json.dumps({"ci_scripts": total, "undocumented": gaps}, indent=1))
    if gaps:
        print("PLAYBOOK RED — CI runs scripts the playbook never mentions:")
        for g in gaps:
            print(f"  - {g}")
        print("  add them to docs/core/onboarding-industry.md (industry path or appendix)")
        return 1
    print(f"playbook: all {total} CI scripts are referenced — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
