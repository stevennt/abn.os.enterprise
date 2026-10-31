#!/usr/bin/env python3
"""Cross-industry consistency (issue #133): the seams of a multi-industry repo.

Checks, across every industries/<id>/:
  1. manifest complete + tier declared + id matches dir (delegated to schema, re-checked)
  2. rule ids, flow ids, event types GLOBALLY unique (a duplicate is a silent
     wrong-rule execution, not a cosmetic clash)
  3. no cross-industry references: an industry's rules/flows/pack must not point
     into a different industry's directory
  4. every declared path resolves inside its own industry
  5. every pack, if present, lints (schema + cross-file) and its stream is declared

Usage: python scripts/cross_industry.py [--json]
       python scripts/cross_industry.py --self-test     # duplicate-id fixture
"""
import argparse
import json
import re
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
INDUSTRIES = ROOT / "industries"


def load_manifests(root=INDUSTRIES):
    out = []
    for m in sorted(root.glob("*/industry.yaml")):
        out.append((m.parent.name, yaml.safe_load(m.read_text()), m.parent))
    return out


def rule_ids(indir):
    ids = {}
    for f in sorted((indir / "rules").glob("*.yaml")):
        try:
            pack = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        for r in (pack if isinstance(pack, list) else [pack]):
            if isinstance(r, dict) and r.get("id"):
                ids[str(r["id"])] = f.name
    return ids


def flow_ids(indir):
    out = {}
    for f in sorted((indir / "flows").glob("*.flow.yaml")):
        try:
            flow = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(flow, dict) and flow.get("id"):
            out[str(flow["id"])] = f.name
    return out


def event_types(indir):
    out = {}
    for f in sorted((indir / "flows").glob("*.flow.yaml")):
        try:
            flow = yaml.safe_load(f.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(flow, dict) and flow.get("event_type"):
            out[str(flow["event_type"])] = f.name
    return out


def check(root=INDUSTRIES, verbose=True):
    problems = []
    mans = load_manifests(root)
    if not mans:
        return ["no industries/*/industry.yaml found"]

    seen = {"rule": {}, "flow": {}, "event": {}}
    ids = [iid for iid, _, _ in mans]
    for iid, man, indir in mans:
        # 1. manifest basics
        for k in ("id", "version", "label", "tier", "jurisdiction", "owner",
                  "tag_stream", "rules", "flows"):
            if k not in man:
                problems.append(f"{iid}: manifest missing '{k}'")
        if man.get("id") != iid:
            problems.append(f"{iid}: manifest id '{man.get('id')}' != directory")
        ts = man.get("tag_stream") or {}
        for kind in ("policy", "pack"):
            p = ts.get(f"{kind}_prefix")
            if not p:
                problems.append(f"{iid}: tag_stream.{kind}_prefix missing")
            elif not p.startswith(iid):
                problems.append(f"{iid}: {kind}_prefix '{p}' must start with '{iid}-'")

        # 2. declared paths resolve INSIDE this industry
        for key in ("rules", "flows"):
            for rel in man.get(key) or []:
                target = (indir / rel) if not str(rel).startswith("industries/") else (ROOT / rel)
                if not target.exists():
                    problems.append(f"{iid}: {key} path missing: {rel}")
                try:
                    target.resolve().relative_to(indir.resolve())
                except ValueError:
                    problems.append(f"{iid}: {key} path escapes the industry: {rel}")

        # 3. ids globally unique
        for kind, mapping in (("rule", rule_ids(indir)), ("flow", flow_ids(indir)),
                              ("event", event_types(indir))):
            for ident, where in mapping.items():
                if ident in seen[kind] and seen[kind][ident][0] != iid:
                    problems.append(
                        f"duplicate {kind} id '{ident}': {seen[kind][ident][0]}/{seen[kind][ident][1]}"
                        f" and {iid}/{where}")
                else:
                    seen[kind][ident] = (iid, where)

        # 4. no cross-industry references inside content
        for f in list((indir / "rules").glob("*.yaml")) + list((indir / "flows").glob("*.flow.yaml")):
            text = f.read_text()
            for other in ids:
                if other == iid:
                    continue
                if re.search(rf"industries/{re.escape(other)}/", text):
                    problems.append(f"{iid}: {f.name} references another industry ({other})")

        # 5. pack lints
        pack = indir / "pack"
        if pack.is_dir():
            import subprocess
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "pack_lint.py"),
                                "--path", str(pack)], capture_output=True, text=True)
            if r.returncode != 0:
                problems.append(f"{iid}: pack_lint failed: {r.stdout.strip().splitlines()[-1][:120]}")

    if verbose:
        print(f"industries: {len(mans)} ({', '.join(ids)})")
        print(f"ids: {len(seen['rule'])} rules, {len(seen['flow'])} flows, "
              f"{len(seen['event'])} event types — globally unique"
              if not problems else "ids: see problems")
        for p in problems:
            print(f"  - {p}")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        fixture = ROOT / "tests" / "fixtures" / "multi-industry"
        problems = check(fixture, verbose=False)
        dupes = [p for p in problems if "duplicate" in p]
        escapes = [p for p in problems
                   if "references another industry" in p or "escapes the industry" in p]
        if not dupes:
            print("self-test FAILED: duplicate rule id across industries not detected")
            return 1
        if not escapes:
            print("self-test FAILED: cross-industry path escape not detected")
            return 1
        print(f"self-test: duplicate id + cross-industry escape both caught "
              f"({len(problems)} problems) — OK")
        return 0

    problems = check()
    if a.json:
        print(json.dumps(problems, indent=1))
    if problems:
        print(f"cross-industry: {len(problems)} problem(s)")
        return 1
    print("cross-industry: consistent — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
