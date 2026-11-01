#!/usr/bin/env python3
"""Tenant-crew contract checker (issue #362, `tenant-crew@1`).

The schema (`schemas/tenant-crew.json`) covers shape. This script covers the rules
a schema cannot state — the ones that decide whether an onboarding was performed
by a crew that was allowed to perform it:

  C1  the pack was `ready` before the crew started (a draft pack is not a handover)
  C2  the steps ran in the contract's order, each exactly once, none missing
  C3  every step was run by a member whose mandate names it
  C4  every member is an agent with an owner who is a person in `people`
  C5  every member's unit is one of the tenant's units
  C6  ids are unique across people, members and steps; every member runs ≥1 step
  C7  the go/no-go is signed by a person — never a member — and comes last
  C8  nothing in the record is an agent doing a person's act (signing the
      go/no-go, provisioning a person's credential, disabling an account)

Usage:
    python scripts/check_tenant_crew_spec.py [path]
    python scripts/check_tenant_crew_spec.py --self-test

Exit 0 = green. `--self-test` mutates the case eight ways and proves each code
fires for its own reason; it is what CI runs beside the plain check.
"""
import argparse
import copy
import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "tenant-crew.json"
CASE = ROOT / "tests" / "fixtures" / "tenant-crew" / "crew.valid.json"

CONTRACT = "tenant-crew@1"
ORDER = ("commercial", "company", "org", "accounts", "crew", "folders", "plans",
         "verify")
PERSON_ONLY = ("go", "sign", "approve", "credential", "disable")
CODES = {"E-CRW-01": "the record's shape, or its contract pin",
         "E-CRW-02": "the commercial pack was not `ready`",
         "E-CRW-03": "the steps are out of order, doubled, or missing",
         "E-CRW-04": "a step was run outside its member's mandate",
         "E-CRW-05": "a member is not an agent owned by a person",
         "E-CRW-06": "a unit is not on the tenant's chart",
         "E-CRW-07": "an id is used twice, or a member runs nothing",
         "E-CRW-08": "an agent performed a person's act, or the go/no-go is not a "
                     "person's, last"}
FIX = {
    "E-CRW-01": "fix the shape against schemas/tenant-crew.json, or the contract "
                "pin — a record from another contract is not evidence",
    "E-CRW-02": "finish the commercial pack first; onboarding a draft is how a "
                "tenant is provisioned with the wrong departments",
    "E-CRW-03": "run the steps in the contract's order, once each",
    "E-CRW-04": "widen the mandate deliberately, or give the step to the member "
                "that holds it",
    "E-CRW-05": "give the agent an owner who is a provisioned person",
    "E-CRW-06": "add the unit to the chart first, or move the member",
    "E-CRW-07": "ids are the join between the records; make them unique",
    "E-CRW-08": "a person signs the go/no-go; an agent may prepare, never sign",
}


def load(path=None):
    with open(path or CASE, encoding="utf-8") as fh:
        return json.load(fh)


def shape(case):
    schema = json.loads(SCHEMA.read_text())
    return [f"E-CRW-01: {error.message}"
            for error in jsonschema.Draft7Validator(schema).iter_errors(case)]


def contract(case):
    """C1."""
    if str(case.get("contract")) != CONTRACT:
        return [f"E-CRW-01: contract is {case.get('contract')!r}, not {CONTRACT!r}"]
    if str((case.get("pack") or {}).get("status")) != "ready":
        return [f"E-CRW-02: the pack is "
                f"{(case.get('pack') or {}).get('status')!r}, not 'ready'"]
    return []


def steps(case):
    """C2 + C3."""
    problems = []
    ran = [str(step.get("id")) for step in case.get("steps") or []]
    if ran != list(ORDER[:len(ran)]) or len(ran) != len(ORDER):
        problems.append(
            f"E-CRW-03: steps ran {', '.join(ran) or 'none'}; the contract's order "
            f"is {', '.join(ORDER)}")
    mandate = {}
    for member in case.get("members") or []:
        for step_id in member.get("steps") or []:
            mandate.setdefault(str(step_id), set()).add(str(member.get("id")))
    for step in case.get("steps") or []:
        runner = str(step.get("by"))
        allowed = mandate.get(str(step.get("id"))) or set()
        if runner not in allowed:
            problems.append(
                f"E-CRW-04: {step.get('id')!r} was run by {runner!r}, whose "
                f"mandate does not name it"
                f" (mandate: {', '.join(sorted(allowed)) or 'none'})")
    return problems


def members(case):
    """C4 + C5 + C6."""
    problems = []
    people = {str(row.get("id")) for row in case.get("people") or []}
    units = {str(unit) for unit in case.get("units") or []}
    seen = set()
    for row in case.get("people") or []:
        if str(row.get("id")) in seen:
            problems.append(f"E-CRW-07: person id {row.get('id')!r} appears twice")
        seen.add(str(row.get("id")))
    for member in case.get("members") or []:
        member_id = str(member.get("id"))
        if member_id in seen:
            problems.append(f"E-CRW-07: id {member_id!r} appears twice")
        seen.add(member_id)
        if str(member.get("kind")) != "agent":
            problems.append(f"E-CRW-05: member {member_id!r} is not an agent")
        if str(member.get("owner")) not in people:
            problems.append(
                f"E-CRW-05: member {member_id!r} is owned by "
                f"{member.get('owner')!r}, who is not one of the tenant's people")
        if str(member.get("unit")) not in units:
            problems.append(
                f"E-CRW-06: member {member_id!r} sits at {member.get('unit')!r}, "
                f"which is not on the chart ({', '.join(sorted(units))})")
        if not member.get("steps"):
            problems.append(f"E-CRW-07: member {member_id!r} runs no step")
        for step_id in member.get("steps") or []:
            if str(step_id) in PERSON_ONLY:
                problems.append(
                    f"E-CRW-08: member {member_id!r} is mandated to "
                    f"{step_id!r}, which is a person's act")
    for step in case.get("steps") or []:
        if str(step.get("id")) in seen:
            problems.append(f"E-CRW-07: step id {step.get('id')!r} is reused")
    return problems


def gating(case):
    """C7 + C8 on the signature itself."""
    problems = []
    decision = case.get("goNoGo") or {}
    signed = str(decision.get("signedBy"))
    people = {str(row.get("id")) for row in case.get("people") or []}
    members = {str(row.get("id")) for row in case.get("members") or []}
    if signed not in people:
        problems.append(
            f"E-CRW-08: the go/no-go is signed by {signed!r}, who is not one of "
            f"the tenant's people")
    elif signed in members:
        problems.append(
            f"E-CRW-08: {signed!r} is a crew member; an agent may prepare a "
            f"handover, never sign it")
    ran = [str(step.get("at")) for step in case.get("steps") or []]
    if ran and str(decision.get("at")) < max(ran):
        problems.append(
            f"E-CRW-08: the go/no-go ({decision.get('at')}) precedes the last "
            f"step ({max(ran)}) — a handover signed before the work is a guess")
    if decision.get("decision") == "go" and any(
            str(step.get("result")) != "ok" for step in case.get("steps") or []):
        problems.append("E-CRW-08: a 'go' with a refused step in the record")
    return problems


def check(case):
    problems = shape(case)
    if problems:
        return problems
    return contract(case) + steps(case) + members(case) + gating(case)


def self_test():
    """Eight mutations, each refused for its own reason."""
    base = load()
    mutations = [
        ("E-CRW-01", lambda c: c.update({"contract": "tenant-crew@0"})),
        ("E-CRW-02", lambda c: c["pack"].update({"status": "draft"})),
        ("E-CRW-03", lambda c: c["steps"].pop(3)),
        ("E-CRW-04", lambda c: c["steps"][2].update({"by": "agent-intake"})),
        ("E-CRW-05", lambda c: c["members"][0].update({"owner": "ghost"})),
        ("E-CRW-06", lambda c: c["members"][0].update({"unit": "nowhere"})),
        ("E-CRW-07", lambda c: c["members"].append(copy.deepcopy(c["members"][0]))),
        ("E-CRW-08", lambda c: c["goNoGo"].update({"signedBy": "agent-verifier"})),
    ]
    failures = 0
    for code, mutate in mutations:
        case = copy.deepcopy(base)
        mutate(case)
        problems = check(case)
        if not any(problem.startswith(f"{code}:") for problem in problems):
            print(f"self-test RED: {code} did not fire: {problems or 'clean'}",
                  file=sys.stderr)
            failures += 1
        else:
            print(f"self-test: {code} — {FIX[code].split(';')[0]}")
    if failures:
        return 1
    clean = check(base)
    if clean:
        print(f"self-test RED: the committed fixture is not clean: {clean}",
              file=sys.stderr)
        return 1
    print(f"self-test: {len(mutations)} mutations refused, the fixture clean — OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="check_tenant_crew_spec.py")
    ap.add_argument("path", nargs="?", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    problems = check(load(args.path))
    if problems:
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(f"tenant crew: FAIL ({len(problems)} problem(s))", file=sys.stderr)
        return 1
    print("tenant crew: OK — the record describes a crew that was allowed to do "
          "the work")
    return 0


if __name__ == "__main__":
    sys.exit(main())
