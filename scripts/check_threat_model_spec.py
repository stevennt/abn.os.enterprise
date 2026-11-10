#!/usr/bin/env python3
"""Threat-register checker (issue #462, `threat-model@2`).

The register is the machine form of `docs/core/threat-model.md`: one row per threat on an
agent surface — prompt injection, agent credentials, cross-tenant — with the control and
the evidence behind it. This checker is the gate that turns *"we have a threat model"* into
a question somebody can answer wrongly.

    E-TM-01  the register is not an object, or cannot be read
    E-TM-02  `version` is not 2
    E-TM-03  a row is not an object, or is missing a required field
    E-TM-04  two rows share an id
    E-TM-05  a `stride` letter that is not S, T, R, I, D or E
    E-TM-06  a `status` outside mitigated | planned | accepted | open
    E-TM-07  a surface with no row — a gap, not a quiet quarter
    E-TM-08  `evidence.path` that does not exist in the repository — a control nobody built
    E-TM-09  `accepted` with no justification (who accepted it, and why)
    E-TM-10  a row the document does not print (the register and the prose disagree)
    E-TM-11  an `open` row — a threat with no control at all (this one **fails the gate**)

A row that is `open` is the only condition that fails a review on its own: everything else
is a shape problem, and a shape problem is cheap to fix.

Usage:
    python scripts/check_threat_model_spec.py [register.json]
    python scripts/check_threat_model_spec.py --self-test
    python scripts/check_threat_model_spec.py --json

Exit 0 = green, 1 = findings (or an open row), 2 = the arguments were wrong.
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "threat-register.json"
REGISTER = ROOT / "tests" / "fixtures" / "security" / "threat-register.json"
DOC = ROOT / "docs" / "core" / "threat-model.md"

SURFACES = ("prompt-injection", "agent-credentials", "cross-tenant")
STATUSES = ("mitigated", "planned", "accepted", "open")
STRIDE = ("S", "T", "R", "I", "D", "E")
REQUIRED = ("id", "surface", "stride", "scenario", "control", "status", "owner")

FIX = {
    "E-TM-01": "point the check at a register, or write one: {version: 2, rows: [...]}",
    "E-TM-02": "a register is version 2 (`threat-model@2`); an old one is migrated, not read",
    "E-TM-03": "every row names its id, surface, stride, scenario, control, status and owner",
    "E-TM-04": "an id is a name: two rows with one id make every reference ambiguous",
    "E-TM-05": "one STRIDE letter: S, T, R, I, D or E",
    "E-TM-06": "status is mitigated, planned, accepted or open",
    "E-TM-07": "add the missing surface's rows, or say in the review why it has none",
    "E-TM-08": "point the evidence at a file that exists, or leave it null and mark the row planned",
    "E-TM-09": "say who accepted it and why — an acceptance nobody signed is an oversight",
    "E-TM-10": "print the row in the document: this register is the table's machine form",
    "E-TM-11": "give it a control, or accept it with a reason, or plan it against an issue",
}


def _problem(code, detail):
    return {"code": code, "detail": detail, "fix": FIX[code]}


def _documented(text):
    """The row ids the document prints, from its own tables (`| A3 | …`)."""
    return set(re.findall(r"^\|\s*(A\d+)\s*\|", text, re.M))


def check(register, root=ROOT, document=None):
    """Every finding, in code order. `open` rows are findings too, and the verdict."""
    if not isinstance(register, dict):
        return [_problem("E-TM-01", "the register is not an object")]
    findings = []
    try:
        jsonschema.validate(register, json.loads(SCHEMA.read_text()))
    except jsonschema.ValidationError as exc:
        # the schema says what; the codes say *which rule*, and the codes are what an
        # operator acts on, so a schema failure is mapped rather than printed raw
        path = "/".join(str(part) for part in exc.absolute_path)
        findings.append(_map(exc, path))
    if register.get("version") != 2:
        findings.append(_problem("E-TM-02", f"version is {register.get('version')!r}"))
        return findings

    rows = register.get("rows")
    if not isinstance(rows, list):
        findings.append(_problem("E-TM-03", "rows is not a list"))
        return findings
    seen = set()
    surfaces = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            findings.append(_problem("E-TM-03", f"row {index} is not an object"))
            continue
        missing = [field for field in REQUIRED
                   if not str(row.get(field) or "").strip()]
        if missing:
            findings.append(_problem("E-TM-03",
                                     f"row {index} is missing {', '.join(missing)}"))
            continue
        if row["id"] in seen:
            findings.append(_problem("E-TM-04", f"{row['id']} appears twice"))
        seen.add(row["id"])
        if row["stride"] not in STRIDE:
            findings.append(_problem("E-TM-05",
                                     f"{row['id']}: stride {row['stride']!r}"))
        if row["status"] not in STATUSES:
            findings.append(_problem("E-TM-06",
                                     f"{row['id']}: status {row['status']!r}"))
        surfaces[row["surface"]] = surfaces.get(row["surface"], 0) + 1
        evidence = row.get("evidence") or {}
        path = str((evidence or {}).get("path") or "")
        if path and not (Path(root) / path).is_file():
            findings.append(_problem("E-TM-08",
                                     f"{row['id']}: evidence {path!r} does not exist"))
        if row["status"] == "open":
            findings.append(_problem("E-TM-11", f"{row['id']}: {row['scenario'][:60]}"))
        if row["status"] == "planned" and not row.get("issue"):
            findings.append(_problem("E-TM-06",
                                     f"{row['id']}: planned with no issue to build it in"))
    for surface in SURFACES:
        if not surfaces.get(surface):
            findings.append(_problem("E-TM-07", f"no rows for surface {surface!r}"))

    accepted = {one.get("id") for one in register.get("accepted") or []
                if isinstance(one, dict)}
    for row in rows:
        if isinstance(row, dict) and row.get("status") == "accepted" \
                and row.get("id") not in accepted:
            findings.append(_problem("E-TM-09",
                                     f"{row.get('id')}: accepted with no justification"))

    if document is not None:
        printed = _documented(document)
        for row in rows:
            if isinstance(row, dict) and row.get("id") not in printed:
                findings.append(_problem("E-TM-10",
                                         f"{row.get('id')} is in the register and not in "
                                         f"the document"))
    return findings


def _map(exc, path):
    """A schema failure as the code that names the rule, not as a jsonschema trace."""
    if path.endswith("version") or "/version" in path:
        return _problem("E-TM-02", "version is not 2")
    if "stride" in path:
        return _problem("E-TM-05", f"stride {exc.instance!r}")
    if "status" in path:
        return _problem("E-TM-06", f"status {exc.instance!r}")
    if "evidence" in path:
        return _problem("E-TM-08", f"evidence {exc.instance!r}")
    return _problem("E-TM-03", f"{path or 'the register'}: {exc.message[:80]}")


def verdict(findings):
    """(ok, blocking) — an `open` row blocks on its own."""
    return not findings, [one for one in findings if one["code"] == "E-TM-11"]


def self_test():
    """Every code fires from a valid register, and a valid register stays quiet."""
    good = json.loads(REGISTER.read_text())
    document = DOC.read_text()
    if check(good, document=document):
        print(f"self-test RED: the committed register was refused: "
              f"{check(good, document=document)}", file=sys.stderr)
        return 1

    def mutate(**changes):
        return dict(copy.deepcopy(good), **changes)

    def replace(index, **fields):
        rows = copy.deepcopy(good["rows"])
        rows[index] = dict(rows[index], **fields)
        return mutate(rows=rows)

    rows = copy.deepcopy(good["rows"])
    mutations = {
        "E-TM-01": "not an object",
        "E-TM-02": mutate(version=1),
        "E-TM-03": mutate(rows=[{k: v for k, v in rows[0].items() if k != "control"}]),
        "E-TM-04": mutate(rows=rows + [rows[0]]),
        "E-TM-05": replace(0, stride="X"),
        "E-TM-06": replace(0, status="maybe"),
        "E-TM-07": mutate(rows=[row for row in rows
                                if row["surface"] != "cross-tenant"]),
        "E-TM-08": mutate(rows=[dict(row, evidence={"path": "docs/core/nope.md"})
                                for row in rows]),
        "E-TM-09": replace(0, status="accepted"),
        "E-TM-11": replace(0, status="open"),
    }
    seen = set()
    for expected, register in mutations.items():
        findings = check(register, document=None)
        codes = {one["code"] for one in findings}
        if expected not in codes:
            print(f"self-test RED: {expected} did not fire (fired "
                  f"{sorted(codes) or 'nothing'})", file=sys.stderr)
            return 1
        for finding in findings:
            if not finding["fix"].strip():
                print(f"self-test RED: {finding['code']} names no fix", file=sys.stderr)
                return 1
        print(f"self-test: {expected} fired — {findings[0]['detail'][:90]}")
        seen |= codes
    missing = set(mutations) - seen
    if missing:
        print(f"self-test RED: never fired {sorted(missing)}", file=sys.stderr)
        return 1

    # E-TM-10 is about the pair, so it needs the document
    drifted = mutate(rows=[dict(rows[0], id="A99")] + rows[1:])
    if "E-TM-10" not in {one["code"] for one in check(drifted, document=document)}:
        print("self-test RED: E-TM-10 did not fire on a row the document omits",
              file=sys.stderr)
        return 1
    print("self-test: E-TM-10 fired — A99 is in the register and not in the document")

    # an `open` row blocks; the rest is shape
    ok, blocking = verdict(check(mutations["E-TM-11"], document=None))
    if ok or not blocking:
        print("self-test RED: an open row did not block the gate", file=sys.stderr)
        return 1
    if verdict(check(mutations["E-TM-05"], document=None))[0]:
        print("self-test RED: a shape finding did not fail the gate", file=sys.stderr)
        return 1
    # the acceptance is not a way to avoid a control: a signed one passes
    accepted = replace(0, status="accepted")
    accepted["accepted"] = [{"id": rows[0]["id"], "why": "cost exceeds the loss",
                             "by": "CISO"}]
    if check(accepted, document=None):
        print(f"self-test RED: a signed acceptance was refused: "
              f"{check(accepted, document=None)}", file=sys.stderr)
        return 1
    print("self-test: E-TM-01…E-TM-11 fired, the register passed, an open row blocked, "
          "and a signed acceptance was allowed — OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="check_threat_model_spec")
    ap.add_argument("register", nargs="?", default=str(REGISTER))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])

    if args.self_test:
        return self_test()

    path = Path(args.register)
    try:
        register = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        findings = [_problem("E-TM-01", f"{path}: {exc}")]
        register = None
    else:
        findings = check(register, document=DOC.read_text() if DOC.is_file() else "")
    ok, blocking = verdict(findings)
    if args.json:
        print(json.dumps({"register": str(path), "ok": ok,
                          "blocking": [one["code"] for one in blocking],
                          "findings": findings}, indent=2, ensure_ascii=False))
    else:
        print(f"{path}: {'OK' if ok else str(len(findings)) + ' finding(s)'}"
              + (f" ({len(blocking)} blocking)" if blocking else ""))
        for finding in findings:
            print(f"  {finding['code']}: {finding['detail']}")
            print(f"    fix: {finding['fix']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
