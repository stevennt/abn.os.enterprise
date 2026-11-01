#!/usr/bin/env python3
"""Approval-gate checker (issue #312, `approval-gates@1`).

Recomputes every decision in a case from its grid, its units/roles and its
requests, and fails if the committed decisions differ. It also validates the
records against `schemas/approval-gate.json`.

Usage:
    python scripts/check_approval_spec.py [path]
    python scripts/check_approval_spec.py --self-test
    python scripts/check_approval_spec.py --emit [path]

Exit 0 = green. `--self-test` mutates the case and proves each refusal code fires
for its own reason; it is what CI runs beside the plain check.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "approval-gate.json"
CASE = ROOT / "tests" / "fixtures" / "approval" / "case.valid.json"

KINDS = ("payment", "memo", "release", "exception")
CODES = ("E-GOV-01", "E-GOV-02", "E-GOV-03", "E-GOV-04", "E-GOV-05",
         "E-GOV-06", "E-GOV-07")
FIX = {
    "E-GOV-01": "fix the caller; the gate does not guess a default",
    "E-GOV-02": "write authority.json for the company; a currency mismatch is a "
                "control failure, not a conversion",
    "E-GOV-03": "route it to the named role",
    "E-GOV-04": "have a human who is not the requester click it",
    "E-GOV-05": "post the role at that unit, or route to one that holds it",
    "E-GOV-06": "read the record; a gate is decided once",
    "E-GOV-07": "raise a limit, or route to the group with an explicit grid",
}


def _limits(case):
    return {str(row["role"]): row["maxAmount"]
            for row in (case.get("grid") or {}).get("grid") or []}


def _currency(case):
    return str((case.get("grid") or {}).get("currency") or "")


def _roles_at(case, unit):
    return list((case.get("units") or {}).get(unit) or [])


def _refusal(code, reason):
    return {"code": code, "reason": reason, "fix": FIX[code]}


def _shape(request):
    if not isinstance(request, dict):
        return _refusal("E-GOV-01", "the request must be an object")
    if not str(request.get("id") or "").strip():
        return _refusal("E-GOV-01", "the request needs an id")
    if request.get("kind") not in KINDS:
        return _refusal("E-GOV-01", f"kind {request.get('kind')!r} is not one of "
                                    f"{', '.join(KINDS)}")
    amount = request.get("amount")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) \
            or amount < 0:
        return _refusal("E-GOV-01", f"amount {amount!r} must be a number ≥ 0")
    for field in ("currency", "requester", "unit"):
        if not str(request.get(field) or "").strip():
            return _refusal("E-GOV-01", f"the request needs a {field}")
    return None


def decide(case, request, approver_id, decided):
    """(record | refusal) for one click, by the contract's ordered procedure."""
    shape = _shape(request)
    if shape:
        return shape
    request_id = str(request["id"])
    if request_id in decided:
        previous = decided[request_id]
        if previous.get("approver") == approver_id:
            return dict(previous["record"], duplicate=True)
        return _refusal("E-GOV-06", f"request {request_id!r} was already decided "
                                    f"by {previous['approver']!r}")
    account = (case.get("accounts") or {}).get(approver_id)
    if not isinstance(account, dict):
        return _refusal("E-GOV-01", f"unknown approver {approver_id!r}")
    if str(account.get("kind") or "person") != "person":
        return _refusal("E-GOV-04", f"{approver_id!r} is an agent; the signer is "
                                    f"a human")
    if approver_id == str(request["requester"]):
        return _refusal("E-GOV-04", f"{approver_id!r} requested this and cannot "
                                    f"approve it (maker/checker)")
    role = str(account.get("role") or "")
    if role not in _roles_at(case, str(request["unit"])):
        return _refusal("E-GOV-05", f"role {role!r} is not held at unit "
                                    f"{request['unit']!r}")
    limits = _limits(case)
    currency = _currency(case)
    if not limits:
        return _refusal("E-GOV-02", f"company {case.get('company')!r} has no "
                                    f"authority grid")
    if currency and str(request["currency"]) != currency:
        return _refusal("E-GOV-02", f"currency {request['currency']!r} does not "
                                    f"match the grid ({currency!r})")
    amount = request["amount"]
    limit = limits.get(role)
    if limit is None or amount > limit:
        candidates = sorted(
            ((other, limits[other]) for other in _roles_at(case, request["unit"])
             if other in limits and limits[other] >= amount),
            key=lambda item: item[1])
        if candidates:
            target, target_limit = candidates[0]
            return {"record": _record(case, request, approver_id, role,
                                      limit if limit is not None else 0,
                                      "escalated",
                                      f"{approver_id} ({role}) may approve up to "
                                      f"{limit}; {amount} needs {target}",
                                      {"role": target, "limit": target_limit})}
        return _refusal("E-GOV-07", f"no role at unit {request['unit']!r} can "
                                    f"approve {amount} {currency}")
    return {"record": _record(case, request, approver_id, role, limit, "approved",
                              f"{approver_id} ({role}) may approve {amount} "
                              f"(limit {limit})", None)}


def _record(case, request, approver, role, limit, decision, reason, escalate_to):
    import hashlib
    ident = "ap-" + hashlib.sha256(
        f"{case['tenant']}|{case['company']}|{request['id']}".encode()).hexdigest()[:16]
    return {"version": 1, "contract": "approval-gates@1", "id": ident,
            "tenant": str(case["tenant"]), "company": str(case["company"]),
            "request": {key: request[key] for key in
                        ("id", "kind", "amount", "currency", "requester",
                         "unit")},
            "gate": {"approver": str(approver), "role": role, "limit": limit,
                     "currency": str(request["currency"])},
            "decision": decision, "reason": reason, "escalateTo": escalate_to,
            "at": str(case["at"])}


def run(case):
    """Every click in order, with the decided map carried between them."""
    decided = {}
    out = []
    for gate in case.get("gates") or []:
        outcome = decide(case, gate["request"], gate["approver"], decided)
        if "record" in outcome:
            decided[str(gate["request"]["id"])] = {
                "approver": gate["approver"], "record": outcome["record"]}
        out.append(outcome)
    return out


def problems(case):
    found = []
    schema = json.loads(SCHEMA.read_text())
    expected = case.get("expected")
    if not isinstance(expected, list):
        return ["the case has no `expected` list"]
    computed = run(case)
    if len(computed) != len(expected):
        found.append(f"{len(computed)} decision(s) computed, {len(expected)} "
                     f"committed")
        return found
    for index, (got, want) in enumerate(zip(computed, expected), 1):
        if want.get("code"):
            if got.get("code") != want["code"]:
                found.append(f"gate {index}: expected {want['code']}, got "
                             f"{got.get('code') or got.get('record', {}).get('decision')}")
            continue
        record = got.get("record")
        if record is None:
            found.append(f"gate {index}: expected a record, got {got}")
            continue
        try:
            jsonschema.validate(record, schema)
        except jsonschema.exceptions.ValidationError as exc:
            where = "/".join(str(part) for part in exc.absolute_path) or "record"
            found.append(f"gate {index} {where}: {exc.message}")
        for key in ("decision", "reason", "escalateTo", "id"):
            if record.get(key) != want.get(key):
                found.append(f"gate {index} {key}: committed "
                             f"{json.dumps(want.get(key))[:80]} != computed "
                             f"{json.dumps(record.get(key))[:80]}")
    return found


def _mutations(case):
    """Seven ways to be wrong; each must produce its code."""
    cases = []

    doc = copy.deepcopy(case)
    doc["gates"][0]["request"]["amount"] = "lots"
    cases.append(("E-GOV-01", "an amount that is a string", doc))

    doc = copy.deepcopy(case)
    doc["grid"]["currency"] = "USD"
    cases.append(("E-GOV-02", "a currency that does not match the grid", doc))

    doc = copy.deepcopy(case)
    doc["gates"][2]["approver"] = "credit-officer-1"
    doc["gates"][2]["request"]["amount"] = 800000000
    cases.append(("E-GOV-03", "an approver too small (escalated)", doc))

    doc = copy.deepcopy(case)
    doc["gates"][0]["approver"] = "agent-co"
    cases.append(("E-GOV-04", "an agent trying to approve", doc))

    doc = copy.deepcopy(case)
    doc["gates"][0]["approver"] = "support-1"
    cases.append(("E-GOV-05", "a role not held at the unit", doc))

    doc = copy.deepcopy(case)
    doc["gates"].append({"request": copy.deepcopy(doc["gates"][0]["request"]),
                         "approver": "ops-admin"})
    cases.append(("E-GOV-06", "a second decision on one request", doc))

    doc = copy.deepcopy(case)
    doc["gates"][3]["request"]["amount"] = 9000000000
    cases.append(("E-GOV-07", "nobody can approve the amount", doc))
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
        print(json.dumps([item.get("record") or item for item in run(case)],
                         indent=2, ensure_ascii=False))
        return 0

    found = problems(case)
    if found:
        print(f"approval: {args.path} FAIL", file=sys.stderr)
        for problem in found:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.self_test:
        missed = []
        for code, label, doc in _mutations(case):
            codes = {item.get("code") for item in run(doc)}
            if code == "E-GOV-03":
                escalated = {item["record"]["decision"] for item in run(doc)
                             if "record" in item}
                if "escalated" not in escalated:
                    missed.append(f"{label} (wanted escalated, got {escalated})")
                continue
            if code not in codes:
                missed.append(f"{label} (wanted {code}, got {sorted(c for c in codes if c)})")
        if missed:
            print("approval --self-test RED: " + "; ".join(missed), file=sys.stderr)
            return 1
        print(f"approval --self-test: {len(_mutations(case))} mutations refused, "
              f"the committed case decides — OK")
        return 0

    decisions = [item.get("record", {}).get("decision") or item.get("code")
                 for item in run(case)]
    if args.json:
        print(json.dumps({"case": str(args.path), "decisions": decisions},
                         indent=1))
        return 0
    print(f"approval: {case['tenant']} — {len(decisions)} gate(s): "
          f"{', '.join(decisions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
