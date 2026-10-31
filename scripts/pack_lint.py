#!/usr/bin/env python3
"""pack_lint (issue #127): validate an agent pack against metamodel/pack.schema.yaml.

A pack = roles.yaml + skills/<name>/SKILL.md frontmatter + agents/<role>.md frontmatter.
This is the contract OpenGate consumes, now owned here.

Usage:
  python scripts/pack_lint.py [--path DIR] [--allow-missing] [--json]
  python scripts/pack_lint.py --self-test

Default: every industries/*/pack that exists (none => "no packs yet", exit 0
unless --strict-packs). --path validates any directory (used to prove the schema
accepts OpenGate's real banking pack before it is imported).
"""
import argparse
import json
import re
import sys
from pathlib import Path
import yaml
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "metamodel" / "pack.schema.yaml"
FM = re.compile(r"\A---\s*\n(.*?)\n---\s*(\n|$)", re.S)


def frontmatter(path):
    m = FM.match(path.read_text())
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter block")
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"{path}: invalid YAML frontmatter ({str(e).splitlines()[0]})")


def collect(pack_dir):
    """Read a pack dir into the shape pack.schema.yaml describes."""
    roles_file = pack_dir / "roles.yaml"
    if not roles_file.exists():
        raise ValueError(f"{pack_dir}: roles.yaml missing")
    try:
        doc = yaml.safe_load(roles_file.read_text())
    except yaml.YAMLError as e:
        raise ValueError(f"{roles_file}: invalid YAML ({str(e).splitlines()[0]})")
    if not isinstance(doc, dict) or not isinstance(doc.get("roles"), dict):
        raise ValueError(f"{roles_file}: missing 'roles' map")
    skills, agents = [], []
    for sdir in sorted((pack_dir / "skills").glob("*/SKILL.md")):
        fm = frontmatter(sdir)
        fm.setdefault("description", "")
        skills.append(fm)
    for adir in sorted((pack_dir / "agents").glob("*.md")):
        fm = frontmatter(adir)
        agents.append(fm)
    return {"version": doc.get("version", "1.0.0"),
            "roles": {"roles": doc["roles"]}, "skills": skills, "agents": agents}


def lint(pack_dir, schema):
    try:
        doc = collect(pack_dir)
    except ValueError as e:
        return [str(e)], None
    errors = []
    validator = jsonschema.Draft202012Validator(schema)
    for e in sorted(validator.iter_errors(doc), key=lambda x: list(map(str, x.absolute_path))):
        loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
        errors.append(f"{loc}: {e.message[:160]}")
    # cross-file checks the schema cannot express
    roles = doc["roles"]["roles"]
    known_skills = {s.get("name") for s in doc["skills"]}
    for rid, r in roles.items():
        for s in (r.get("skills_required") or []) + ([r["rubric"]] if r.get("rubric") else []):
            if s not in known_skills and not s.startswith("base-"):
                errors.append(f"role {rid}: skill '{s}' not present in pack (or base-*)")
        tpl = pack_dir / (r.get("template") or "")
        if not tpl.is_file():
            errors.append(f"role {rid}: template missing {r.get('template')}")
        if r.get("position") == "checker" and r.get("may_invoke"):
            errors.append(f"role {rid}: checker must not invoke other roles (may_invoke non-empty)")
    return errors, doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path")
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    schema = yaml.safe_load(SCHEMA_PATH.read_text())

    if a.self_test:
        good_d, _ = lint(ROOT / "tests" / "fixtures" / "pack-sample", schema)
        bad_d, _ = lint(ROOT / "tests" / "fixtures" / "pack-broken", schema)
        if good_d:
            print(f"self-test FAILED: sample pack should be green, got {good_d}")
            return 1
        if not bad_d:
            print("self-test FAILED: broken pack should be red")
            return 1
        print(f"self-test: sample green, broken red ({len(bad_d)} errors) — OK")
        return 0

    if a.path:
        targets = [Path(a.path)]
    else:
        targets = sorted((ROOT / "industries").glob("*/pack"))
        if not targets:
            print("pack-lint: no industries/*/pack yet (imported in L4-06) — OK")
            return 0

    report, failures = {}, 0
    for t in targets:
        if not t.is_dir():
            if a.allow_missing:
                print(f"pack-lint: {t} absent (allowed)")
                continue
            print(f"pack-lint RED: {t} does not exist")
            failures += 1
            continue
        errs, doc = lint(t, schema)
        report[str(t)] = errs
        status = "OK" if not errs else "RED"
        nroles = len((doc or {}).get("roles", {}).get("roles", {}))
        nskills = len((doc or {}).get("skills", []))
        print(f"{status:3} {t} (roles={nroles}, skills={nskills})")
        for e in errs[:12]:
            print(f"    - {e}")
        failures += bool(errs)
    if a.json:
        print(json.dumps(report, indent=1))
    print(f"pack-lint: {len(targets) - failures}/{len(targets)} packs green")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
