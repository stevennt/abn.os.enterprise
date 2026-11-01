#!/usr/bin/env python3
"""Validate a compiled Paperclip company template (issue #252).

The schema (`schemas/paperclip-company.json`) covers shape. This script covers
the rules a schema cannot state, and is the acceptance test the compiler
(PC1-02-02, #253) has to satisfy before Paperclip import is attempted:

  S1  the boundary version matches the contract page;
  S2  exactly one root agent (`reportsTo: null`), and every `reportsTo` resolves;
  S3  agents, projects, routines, skills and evals have unique ids;
  S4  every routine's project resolves, and a step is reasoned once per project;
  S5  `autonomy: autonomous` only at L3+ with `ruleStatus: signed` (a step backed
      by a `pending-*` rule may be supervised, never autonomous);
  S6  a routine carries at least one rule id (nothing compiles on vibes);
  S7  skills and evals name paths that exist in this repository;
  S8  every skill an agent references is declared in `skills`.

Usage:
  python scripts/check_paperclip_template.py --template <path>
  python scripts/check_paperclip_template.py --self-test
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "paperclip-company.json"
CONTRACT = ROOT / "docs" / "core" / "paperclip-integration.md"
FIXTURE = ROOT / "tests" / "fixtures" / "paperclip-company.example.json"
VERSION = re.compile(r"paperclip-boundary@\d+\.\d+")


def contract_version():
    text = CONTRACT.read_text() if CONTRACT.is_file() else ""
    found = VERSION.search(text)
    return found.group(0) if found else None


def _schema_problems(doc):
    import jsonschema

    schema = json.loads(SCHEMA.read_text())
    validator = jsonschema.Draft7Validator(schema)
    return [f"schema: {error.message} at {list(error.path)}"
            for error in sorted(validator.iter_errors(doc), key=str)]


def _semantic_problems(doc):
    import os

    problems = []
    want = contract_version()
    if want and doc.get("boundary") != want:
        problems.append(f"S1 boundary: template says {doc.get('boundary')!r}, "
                        f"contract says {want!r}")

    agents = doc.get("agents") or []
    ids = [a.get("id") for a in agents]
    roots = [a for a in agents if a.get("reportsTo") is None]
    if len(roots) != 1:
        problems.append(f"S2 org: expected exactly one root agent, found {len(roots)}")
    for agent in agents:
        parent = agent.get("reportsTo")
        if parent is not None and parent not in ids:
            problems.append(f"S2 org: agent {agent.get('id')!r} reports to "
                            f"{parent!r}, which is not an agent")
    if ids:
        seen, walk = set(), ids[0]
        while walk is not None and walk not in seen:
            seen.add(walk)
            walk = next((a.get("reportsTo") for a in agents if a.get("id") == walk), None)
        if walk is not None:
            problems.append(f"S2 org: reporting cycle through {walk!r}")

    for name, key in (("agent", "agents"), ("project", "projects"),
                      ("routine", "routines"), ("skill", "skills"),
                      ("eval", "evals")):
        values = [row.get("id") for row in doc.get(key) or []]
        dupes = sorted({v for v in values if values.count(v) > 1})
        if dupes:
            problems.append(f"S3 ids: duplicate {name} ids {dupes}")

    projects = {p.get("id") for p in doc.get("projects") or []}
    steps = {}
    for routine in doc.get("routines") or []:
        where = f"routine {routine.get('id')!r}"
        if routine.get("project") not in projects:
            problems.append(f"S4 {where}: project {routine.get('project')!r} is not "
                            f"in projects")
        key = (routine.get("project"), routine.get("step"))
        if key in steps:
            problems.append(f"S4 {where}: step {routine.get('step')!r} already has a "
                            f"routine in this project")
        steps[key] = True
        if routine.get("autonomy") == "autonomous" and \
                routine.get("ruleStatus") != "signed":
            problems.append(f"S5 {where}: autonomous routine depends on an unreviewed "
                            f"rule — it must be supervised")
        if not routine.get("usesRules"):
            problems.append(f"S6 {where}: no rule cited")

    declared = {row.get("id") for row in doc.get("skills") or []}
    for agent in agents:
        for skill in agent.get("skills") or []:
            if skill not in declared:
                problems.append(f"S8 skills: agent {agent.get('id')!r} references "
                                f"{skill!r}, which is not in skills")

    for kind in ("skills", "evals"):
        for row in doc.get(kind) or []:
            path = str(row.get("path") or "")
            if not path or not os.path.exists(ROOT / path):
                problems.append(f"S7 {kind}: {row.get('id')!r} names a path that does "
                                f"not exist: {path!r}")
    return problems


def check_template(doc):
    return _schema_problems(doc) + _semantic_problems(doc)


def self_test():
    import copy

    base = json.loads(FIXTURE.read_text())
    cases = [
        ("valid fixture", [], None),
        ("autonomous on a pending rule",
         lambda d: d["routines"][0].__setitem__("ruleStatus", "pending"), "S5"),
        ("two roots",
         lambda d: d["agents"][1].__setitem__("reportsTo", None), "S2"),
        ("unresolved manager",
         lambda d: d["agents"][1].__setitem__("reportsTo", "nobody"), "S2"),
        ("duplicate agent id",
         lambda d: d["agents"][1].__setitem__("id", d["agents"][0]["id"]), "S3"),
        ("routine without a rule",
         lambda d: d["routines"][0].__setitem__("usesRules", []), "S6"),
        ("boundary mismatch",
         lambda d: d.__setitem__("boundary", "paperclip-boundary@9.9"), "S1"),
        ("missing skill path",
         lambda d: d["skills"].append({"id": "ghost", "path": "industries/none"}), "S7"),
        ("schema: no projects",
         lambda d: d.pop("projects"), "schema"),
        ("schema: routine at L2",
         lambda d: d["routines"][0].__setitem__("level", "L2"), "schema"),
        ("undeclared agent skill",
         lambda d: d["agents"][1].__setitem__("skills", ["ghost"]), "S8"),
    ]
    failures = []
    for label, mutate, code in cases:
        doc = copy.deepcopy(base)
        if mutate:
            mutate(doc)
        problems = check_template(doc)
        if code is None:
            if problems:
                failures.append(f"{label}: expected clean, got {problems}")
        elif not any(code in problem for problem in problems):
            failures.append(f"{label}: expected {code}, got {problems}")
    return failures


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in argv:
        failures = self_test()
        if failures:
            print("paperclip-template --self-test RED:")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("paperclip-template --self-test: 11 cases (1 valid, 10 refused) — OK")
        return 0
    if "--template" not in argv:
        print("usage: check_paperclip_template.py --template <path> | --self-test",
              file=sys.stderr)
        return 2
    path = Path(argv[argv.index("--template") + 1])
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"paperclip-template: unreadable template ({exc})", file=sys.stderr)
        return 3
    problems = check_template(doc)
    if problems:
        print("TEMPLATE RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 3
    print(f"paperclip-template: {path.name} valid — {doc['company']} "
          f"({len(doc['agents'])} agents, {len(doc['routines'])} routines, "
          f"{doc['boundary']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
