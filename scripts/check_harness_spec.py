#!/usr/bin/env python3
"""Harness contract checker (issue #332, `program-harness@1`).

Builds the run record from a case's steps and observations, compares it with the
committed one, and reports the seven refusals in their contract order.

Usage:
    python scripts/check_harness_spec.py [path]
    python scripts/check_harness_spec.py --self-test
    python scripts/check_harness_spec.py --emit [path]

Exit 0 = green. `--self-test` mutates the case seven ways and proves each code
fires for its own reason; it is what CI runs beside the plain check.
"""
import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "harness-run.json"
CASE = ROOT / "tests" / "fixtures" / "harness" / "run.valid.json"

CODES = ("E-HRN-01", "E-HRN-02", "E-HRN-03", "E-HRN-04", "E-HRN-05",
         "E-HRN-06", "E-HRN-07")
FIX = {
    "E-HRN-01": "re-provision the fixture; a run against an edited fixture proves "
                "nothing",
    "E-HRN-02": "read the step: the contract changed, or the fixture is stale",
    "E-HRN-03": "the refusal fired for another rule — fix the fixture or the "
                "contract's checker",
    "E-HRN-04": "the harness must not mutate what it measures; add the change to "
                "the script or stop writing",
    "E-HRN-05": "rebuild one of them; a mixed pair proves nothing",
    "E-HRN-06": "the record must account for every step",
    "E-HRN-07": "non-determinism: a clock, a path, or an unsorted set leaked into "
                "a fixture",
}


def _refusal(code, reason):
    return {"code": code, "reason": reason, "fix": FIX[code]}


def _digest(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def run_id(case, assertions):
    lines = [str((case.get("pin") or {}).get("tag") or "")]
    lines += [f"{row['id']}:{row['sha256']}"
              for row in sorted(case.get("fixtures") or [],
                                key=lambda row: row["id"])]
    lines += [f"{row['step']}:{row['expect']}:{row.get('code') or ''}:"
              f"{row['observed']}:{row.get('observedCode') or ''}"
              for row in sorted(assertions, key=lambda row: row["step"])]
    return "hrn-" + _digest("\n".join(lines))[:16]


def check(case):
    """(run record | None, [refusal…]) by the contract's ordered procedure."""
    findings = []
    pin = case.get("pin") or {}
    fixtures = {row["id"]: row["sha256"] for row in case.get("fixtures") or []
                if isinstance(row, dict) and "id" in row}
    for needed in ("fake-paperclip", "fake-tenant"):
        if needed not in fixtures:
            findings.append(_refusal("E-HRN-01", f"the fixture {needed!r} is "
                                                  f"missing from the run"))
        elif not re.match(r"^[0-9a-f]{64}$", str(fixtures[needed])):
            findings.append(_refusal("E-HRN-01", f"the fixture {needed!r} has no "
                                                  f"digest"))
    pins = case.get("fixturePins") or {}
    if len(set(pins.values())) > 1:
        findings.append(_refusal(
            "E-HRN-05", "the fixtures were built for different contract pins: "
                        + ", ".join(f"{key}={value}" for key, value
                                    in sorted(pins.items()))))
    if not pin.get("tag") or not re.match(r"^[0-9a-f]{40}$",
                                          str(pin.get("sha") or "")):
        findings.append(_refusal("E-HRN-01", f"the run's pin is {pin!r}"))

    steps = {str(row["id"]): row for row in case.get("steps") or []}
    observed = {str(row["id"]): row for row in case.get("observed") or []}
    for step_id in sorted(set(steps) - set(observed)):
        findings.append(_refusal("E-HRN-06", f"step {step_id!r} has no "
                                              f"observation"))
    for step_id in sorted(set(observed) - set(steps)):
        findings.append(_refusal("E-HRN-06", f"observation {step_id!r} has no "
                                              f"step"))

    assertions = []
    for step_id in sorted(set(steps) & set(observed)):
        step, seen = steps[step_id], observed[step_id]
        expect = str(step.get("expect") or "allowed")
        got = str(seen.get("observed") or "allowed")
        ok = expect == got
        code_ok = True
        if ok and expect == "refused" and step.get("code"):
            code_ok = str(seen.get("observedCode") or "") == str(step["code"])
        assertions.append({"step": step_id, "expect": expect,
                           "code": step.get("code"),
                           "observed": got,
                           "observedCode": seen.get("observedCode"),
                           "ok": ok and code_ok})
        if not ok:
            findings.append(_refusal(
                "E-HRN-02", f"step {step_id}: expected {expect}, the platform "
                            f"did {got}"))
        elif not code_ok:
            findings.append(_refusal(
                "E-HRN-03", f"step {step_id}: refused for "
                            f"{seen.get('observedCode')!r}, the contract says "
                            f"{step['code']!r}"))
    if case.get("dirty"):
        findings.append(_refusal("E-HRN-04", "the run changed "
                                              + ", ".join(case["dirty"])))
    record = {"version": 1, "contract": "program-harness@1",
              "runId": run_id(case, assertions), "at": str(case.get("at")),
              "pin": {"tag": str(pin.get("tag") or ""),
                      "sha": str(pin.get("sha") or "")},
              "fixtures": [{"id": key, "sha256": fixtures[key]}
                           for key in sorted(fixtures)],
              "assertions": assertions, "dirty": list(case.get("dirty") or []),
              "verdict": "fail" if any(not row["ok"] for row in assertions) or
                                  case.get("dirty") else "pass"}
    repeat = case.get("repeatRunId")
    if repeat:
        record["repeatRunId"] = str(repeat)
        if str(repeat) != record["runId"]:
            findings.append(_refusal(
                "E-HRN-07", f"an immediate second run of the same fixtures and "
                            f"script produced {repeat}, not {record['runId']}"))
    return record, findings


def problems(case):
    found = []
    record, findings = check(case)
    expected = case.get("expected") or {}
    if [row["code"] for row in findings] != [row["code"] for row in
                                            expected.get("findings") or []]:
        found.append("findings: committed "
                     f"{[row['code'] for row in expected.get('findings') or []]} "
                     f"!= computed {[row['code'] for row in findings]}")
    for want, got in zip(expected.get("findings") or [], findings):
        if want.get("reason") != got.get("reason"):
            found.append(f"{got['code']} reason: committed {want.get('reason')!r} "
                         f"!= computed {got.get('reason')!r}")
    if record and record.get("verdict") != expected.get("verdict"):
        found.append(f"verdict: committed {expected.get('verdict')!r} != computed "
                     f"{record.get('verdict')!r}")
    schema = json.loads(SCHEMA.read_text())
    try:
        jsonschema.validate(record, schema)
    except jsonschema.exceptions.ValidationError as exc:
        where = "/".join(str(part) for part in exc.absolute_path) or "record"
        found.append(f"run {where}: {exc.message}")
    for key, value in (expected.get("run") or {}).items():
        if record.get(key) != value:
            found.append(f"run {key}: committed {json.dumps(value)[:60]} != "
                         f"computed {json.dumps(record.get(key))[:60]}")
    return found


def _mutations(case):
    """Seven ways to be wrong; each must produce its code."""
    cases = []

    doc = copy.deepcopy(case)
    doc["fixtures"] = [row for row in doc["fixtures"] if row["id"] != "fake-tenant"]
    cases.append(("E-HRN-01", "a fixture missing from the run", doc))

    doc = copy.deepcopy(case)
    doc["observed"][0]["observed"] = "refused"
    doc["observed"][0]["observedCode"] = "E-ACL-02"
    cases.append(("E-HRN-02", "a step the platform did differently", doc))

    doc = copy.deepcopy(case)
    doc["observed"][1]["observedCode"] = "E-ACL-01"
    cases.append(("E-HRN-03", "refused for the wrong reason", doc))

    doc = copy.deepcopy(case)
    doc["dirty"] = ["customers/acme/runs/PC-1-1.json"]
    cases.append(("E-HRN-04", "a run that left the tenant dirty", doc))

    doc = copy.deepcopy(case)
    doc["fixturePins"] = {"fake-paperclip": "contract-2026.11.1",
                          "fake-tenant": "contract-2026.09.0"}
    cases.append(("E-HRN-05", "a pair built for two pins", doc))

    doc = copy.deepcopy(case)
    doc["steps"].append({"id": "S7", "action": "read", "target": "x",
                         "expect": "allowed"})
    cases.append(("E-HRN-06", "a step with no observation", doc))

    doc = copy.deepcopy(case)
    doc["repeatRunId"] = "hrn-ffffffffffffffff"
    cases.append(("E-HRN-07", "a run that is not repeatable", doc))
    return cases


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(CASE))
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args(argv)

    case = json.loads(Path(args.path).read_text())
    if args.emit:
        record, findings = check(case)
        print(json.dumps({"run": record, "findings": findings}, indent=2,
                         ensure_ascii=False))
        return 0

    found = problems(case)
    if found:
        print(f"harness: {args.path} FAIL", file=sys.stderr)
        for problem in found:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.self_test:
        missed = []
        for code, label, doc in _mutations(case):
            _record, findings = check(doc)
            codes = {row["code"] for row in findings}
            if code not in codes:
                missed.append(f"{label} (wanted {code}, got {sorted(codes)})")
        if missed:
            print("harness --self-test RED: " + "; ".join(missed), file=sys.stderr)
            return 1
        print(f"harness --self-test: {len(_mutations(case))} mutations refused, "
              f"the committed run passes — OK")
        return 0

    record, findings = check(case)
    if args.json:
        print(json.dumps({"runId": record["runId"], "verdict": record["verdict"],
                          "assertions": len(record["assertions"]),
                          "findings": [row["code"] for row in findings]},
                         indent=1))
        return 0
    print(f"harness: {case['tenant']} {record['runId']} — "
          f"{len(record['assertions'])} assertion(s), verdict {record['verdict']}, "
          f"{len(findings)} finding(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
