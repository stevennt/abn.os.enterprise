#!/usr/bin/env python3
"""Identity contract checker (issue #272, `tenant-identity@1`).

Validates the tenant account store against `schemas/tenant-identity.json` and the
binding rules a JSON schema cannot express:

  * ids are unique and path-safe (the schema checks the shape, this checks
    uniqueness);
  * one SSO subject per tenant — two accounts bound to one person is an
    impersonation waiting to happen;
  * an agent's `owner` is a person account in the same store, and that person is
    not disabled (a disabled owner means nobody is responsible);
  * an agent has no credential and no SSO binding (the schema forbids it; this
    keeps the check readable when the schema evolves).

Usage:
    python scripts/check_identity_spec.py [path]
    python scripts/check_identity_spec.py --self-test
    python scripts/check_identity_spec.py --json [path]

Exit 0 = green. `--self-test` mutates the fixture one rule at a time and proves
each refusal bites; it is what CI runs beside the plain check.
"""
import argparse
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "tenant-identity.json"
FIXTURE = ROOT / "tests" / "fixtures" / "identity" / "accounts.valid.json"


def schema_problems(doc):
    schema = json.loads(SCHEMA.read_text())
    try:
        jsonschema.validate(doc, schema)
    except jsonschema.exceptions.ValidationError as exc:
        where = "/".join(str(part) for part in exc.absolute_path) or "document"
        message = exc.message
        if "is not valid under any of the given schemas" in message:
            message = ("a person needs a credential or an sso binding — "
                       "one of the two, not neither")
        return [f"{where}: {message}"]
    return []


def semantic_problems(doc):
    problems = []
    accounts = [row for row in (doc.get("accounts") or [])
                if isinstance(row, dict)]
    by_id = {}
    for row in accounts:
        account_id = str(row.get("id") or "")
        if account_id in by_id:
            problems.append(f"duplicate account id {account_id!r}")
        by_id[account_id] = row

    subjects = {}
    for row in accounts:
        sso = row.get("sso") or {}
        subject = str(sso.get("subject") or "")
        if not subject:
            continue
        if subject in subjects:
            problems.append(f"subject {subject!r} is bound to both "
                            f"{subjects[subject]!r} and {row.get('id')!r} — one "
                            f"account per subject per tenant")
        subjects[subject] = row.get("id")

    for row in accounts:
        if row.get("kind") != "agent":
            continue
        account_id = row.get("id")
        if row.get("credential") or row.get("sso"):
            problems.append(f"agent {account_id!r} holds a login (credential or "
                            f"sso); an agent acts only through a signed pass")
        owner_id = str(row.get("owner") or "")
        owner = by_id.get(owner_id)
        if owner is None:
            problems.append(f"agent {account_id!r}: owner {owner_id!r} is not an "
                            f"account in this tenant")
            continue
        if owner.get("kind") == "agent":
            problems.append(f"agent {account_id!r}: owner {owner_id!r} is itself an "
                            f"agent; an agent must not own an agent")
        if str(owner.get("status") or "active") != "active":
            problems.append(f"agent {account_id!r}: owner {owner_id!r} is disabled — "
                            f"reassign the agent before offboarding the person")
    return problems


def problems(doc):
    # Semantic refusals first: "agent-kyc holds a login" is the sentence an
    # operator needs; the schema error that follows is the mechanical proof.
    return semantic_problems(doc) + schema_problems(doc)


def _mutations(valid):
    def copy():
        return json.loads(json.dumps(valid))

    def agent(doc):
        return next(row for row in doc["accounts"] if row.get("kind") == "agent")

    def person(doc):
        return next(row for row in doc["accounts"]
                    if row.get("id") == "binh.tran")

    cases = []

    doc = copy()
    agent(doc)["credential"] = {"algo": "x", "salt": "y", "hash": "z"}
    cases.append(("an agent with a password", doc))

    doc = copy()
    agent(doc)["sso"] = {"subject": "oneid:u_x"}
    cases.append(("an agent with an SSO binding", doc))

    doc = copy()
    person(doc).pop("credential")
    cases.append(("a person with no credential and no SSO", doc))

    doc = copy()
    person(doc)["role"] = "Credit Officer"
    cases.append(("a role that is not a portal role", doc))

    doc = copy()
    doc["accounts"].append(copy()["accounts"][1])
    cases.append(("a duplicate account id", doc))

    doc = copy()
    person(doc)["status"] = "active"
    person(doc)["sso"] = {"subject": "oneid:u_01HZX4M8Q3"}
    cases.append(("two accounts bound to one ONEID subject", doc))

    doc = copy()
    agent(doc)["owner"] = "ghost"
    cases.append(("an agent whose owner does not exist", doc))

    doc = copy()
    first = agent(doc)
    first["id"] = "agent-a"
    second = dict(first, id="agent-b", owner="agent-a")
    doc["accounts"].append(second)
    cases.append(("an agent owned by another agent", doc))

    doc = copy()
    owner = next(row for row in doc["accounts"]
                 if row.get("id") == agent(doc)["owner"])
    owner["status"] = "disabled"
    cases.append(("an agent whose owner is disabled", doc))

    return cases


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(FIXTURE))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    valid = json.loads(FIXTURE.read_text())
    base = problems(valid)
    if base:
        print("identity: the committed example does not validate:", file=sys.stderr)
        for problem in base:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.self_test:
        cases = _mutations(valid)
        missed = []
        for label, doc in cases:
            if not problems(doc):
                missed.append(label)
        if missed:
            print("identity --self-test RED: these mutations were accepted: "
                  + "; ".join(missed), file=sys.stderr)
            return 1
        print(f"identity --self-test: {len(cases)} mutations refused, the committed "
              f"example validates — OK")
        return 0

    doc = json.loads(Path(args.path).read_text())
    found = problems(doc)
    if found:
        print(f"identity: {args.path} FAIL", file=sys.stderr)
        for problem in found:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    accounts = doc.get("accounts") or []
    people = sum(1 for row in accounts if row.get("kind") != "agent")
    agents = len(accounts) - people
    if args.json:
        print(json.dumps({"path": str(args.path), "accounts": len(accounts),
                          "people": people, "agents": agents,
                          "contract": "tenant-identity@1"}, indent=1))
    else:
        print(f"identity: {len(accounts)} account(s) — {people} people, {agents} "
              f"agent(s) — validate against tenant-identity@1 — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
