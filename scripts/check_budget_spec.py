#!/usr/bin/env python3
"""Budget reconciliation checker (issue #302, `budget-reconciliation@1`).

The contract is not prose: this script recomputes the report from a case's
inputs (registry, subscription, budget store, spend) and fails if the committed
report differs by a byte. It also validates both documents against their schemas.

Usage:
    python scripts/check_budget_spec.py [path]
    python scripts/check_budget_spec.py --self-test
    python scripts/check_budget_spec.py --json [path]
    python scripts/check_budget_spec.py --emit [path]    # print the report

Exit 0 = green. `--self-test` mutates the case's inputs seven ways and proves
each expected code appears; it is what CI runs beside the plain check.

The arithmetic here is the specification. When the gateway implements it
(#303), this file is the oracle: same inputs, same report, or one of them is
wrong.
"""
import argparse
import copy
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
STORE_SCHEMA = ROOT / "schemas" / "budget-store.json"
REPORT_SCHEMA = ROOT / "schemas" / "budget-reconciliation.json"
CASE = ROOT / "tests" / "fixtures" / "budget" / "case.valid.json"

# the kinds the example uses, in the order an operator reads them; any other
# kind in the case is appended, because the budget store is keyed by metering
# kind and the contract must not lose one silently
PREFERRED = ("jobs", "documents", "storage")
COMPARABLE = ("jobs", "storage")
MB = 1024 * 1024
SEVERITY = {"E-BUD-01": "critical", "E-BUD-02": "critical",
            "E-BUD-03": "warning", "E-BUD-04": "warning", "E-BUD-05": "warning",
            "E-BUD-06": "warning", "E-BUD-07": "critical"}
ORDER = ("E-BUD-01", "E-BUD-02", "E-BUD-03", "E-BUD-05", "E-BUD-04",
         "E-BUD-06", "E-BUD-07")
FIX = {
    "E-BUD-01": "assign a plan (PUT /ops/tenants/:tenant/plan); until then the "
                "ceiling is unknown, not unlimited",
    "E-BUD-02": "fix customers/<t>/budgets.json; every problem is listed",
    "E-BUD-03": "remove the entry, or make the account an active agent",
    "E-BUD-04": "add the budget, or accept it explicitly with enforced: false",
    "E-BUD-05": "lower the budgets, or buy a plan that covers them",
    "E-BUD-06": "fix the budget or the runner: the throttle did not hold",
    "E-BUD-07": "upgrade the plan, and check the quota-alert history",
}


def _kinds(case):
    named = set(PREFERRED)
    for row in ((case.get("budgets") or {}).get("agents") or []):
        named.update((row.get("budget") or {}).keys())
    for row in (case.get("spend") or []):
        if isinstance(row, dict) and row.get("kind"):
            named.add(str(row["kind"]))
    ordered = [kind for kind in PREFERRED if kind in named]
    return tuple(ordered + sorted(named - set(ordered)))


def _zero(kinds):
    return {kind: 0 for kind in kinds}


def _limits(plan):
    return {key: int(plan[key]) for key in ("seats", "storageMb", "jobsPerMonth")}


def _budget_problems(store, tenant):
    """Shape problems in the store, as the report's `problems` list."""
    schema = json.loads(STORE_SCHEMA.read_text())
    problems = []
    try:
        jsonschema.validate(store, schema)
    except jsonschema.exceptions.ValidationError as exc:
        where = "/".join(str(part) for part in exc.absolute_path) or "document"
        problems.append(f"{where}: {exc.message}")
        return problems
    if str(store.get("tenant")) != tenant:
        problems.append(f"tenant is {store.get('tenant')!r}, the directory is "
                        f"{tenant!r}")
    seen = set()
    for index, row in enumerate(store.get("agents") or []):
        account = str(row.get("account") or "")
        if account in seen:
            problems.append(f"agents/{index}: duplicate account {account!r}")
        seen.add(account)
    return problems


def _finding(code, message, account=None, kind=None):
    return {"code": code, "severity": SEVERITY[code], "account": account,
            "kind": kind, "message": message, "fix": FIX[code]}


def reconcile(case):
    """The report, computed from the case's inputs (the contract's arithmetic)."""
    kinds = _kinds(case)
    tenant = str(case["tenant"])
    registry = {str(key): _limits(value)
                for key, value in (case.get("registry") or {}).items()}
    subscription = case.get("subscription") or {}
    plan_id = str(subscription.get("plan") or "")
    plan = None if plan_id not in registry else {"id": plan_id,
                                                "limits": registry[plan_id]}

    store = case.get("budgets") or {}
    problems = _budget_problems(store, tenant)
    agents = [str(item) for item in (case.get("agents") or [])]
    entries = {}
    for row in (store.get("agents") or []):
        if not isinstance(row, dict):
            continue
        entries[str(row.get("account") or "")] = row

    spent = {}
    for row in (case.get("spend") or []):
        if not isinstance(row, dict):
            continue
        account = row.get("account")
        kind = str(row.get("kind") or "")
        if kind not in kinds:
            continue
        bucket = spent.setdefault(account, _zero(kinds))
        bucket[kind] += int(row.get("quantity") or 0)

    findings = []
    if plan is None:
        why = (f"plan {plan_id!r} is not in the registry" if plan_id
               else "the tenant has no assigned plan")
        findings.append(_finding("E-BUD-01", f"the ceiling is unknown — {why}",
                                 kind="plan"))
    if problems:
        findings.append(_finding(
            "E-BUD-02", f"{len(problems)} problem(s) in the budget store — the "
                        f"throttle cannot be read", kind="plan"))
    for account in sorted(entries):
        if account not in agents:
            findings.append(_finding(
                "E-BUD-03", f"budget for {account!r}, which is not an active "
                            f"agent in this tenant", account=account, kind="plan"))

    totals = {"budget": _zero(kinds), "spent": _zero(kinds),
              "unbudgeted": _zero(kinds),
              "unlimited": {kind: [] for kind in kinds}}
    for account, row in entries.items():
        budget = row.get("budget") or {}
        for kind in kinds:
            value = budget.get(kind)
            if value is None:
                continue
            if int(value) < 0:
                totals["unlimited"][kind].append(account)
            else:
                totals["budget"][kind] += int(value)
    for account, bucket in spent.items():
        for kind in kinds:
            totals["spent"][kind] += bucket[kind]
            budget = (entries.get(account) or {}).get("budget") or {}
            if account is None or budget.get(kind) is None:
                totals["unbudgeted"][kind] += bucket[kind]
    for kind in kinds:
        totals["unlimited"][kind].sort()

    if plan is not None:
        for kind in COMPARABLE:
            limit = (plan["limits"]["jobsPerMonth"] if kind == "jobs"
                     else plan["limits"]["storageMb"] * MB)
            if limit < 0:
                continue
            if totals["budget"][kind] > limit:
                findings.append(_finding(
                    "E-BUD-05",
                    f"agent budgets promise {totals['budget'][kind]} {kind} but "
                    f"the plan allows {limit} — the promise does not fit the "
                    f"purchase", kind=kind))
    if totals["unbudgeted"] != _zero(kinds):
        for kind in kinds:
            if totals["unbudgeted"][kind]:
                named = sorted(str(account) for account, bucket in spent.items()
                               if bucket[kind] and
                               ((entries.get(account) or {}).get("budget") or {}
                                ).get(kind) is None)
                findings.append(_finding(
                    "E-BUD-04",
                    f"{totals['unbudgeted'][kind]} {kind} spent with no budget "
                    f"behind it ({', '.join(named)})", kind=kind))
    for account in sorted(entries):
        budget = entries[account].get("budget") or {}
        bucket = spent.get(account) or _zero(kinds)
        for kind in kinds:
            value = budget.get(kind)
            if value is None or int(value) < 0:
                continue
            if bucket[kind] > int(value):
                findings.append(_finding(
                    "E-BUD-06",
                    f"{account}: {kind} {bucket[kind]} > {int(value)} — the "
                    f"throttle did not hold", account=account, kind=kind))
    if plan is not None:
        for kind in COMPARABLE:
            limit = (plan["limits"]["jobsPerMonth"] if kind == "jobs"
                     else plan["limits"]["storageMb"] * MB)
            if limit < 0:
                continue
            if totals["spent"][kind] > limit:
                findings.append(_finding(
                    "E-BUD-07",
                    f"the tenant spent {totals['spent'][kind]} {kind}, past the "
                    f"plan's {limit}", kind=kind))

    quota = []
    if plan is not None:
        for kind in COMPARABLE:
            limit = (plan["limits"]["jobsPerMonth"] if kind == "jobs"
                     else plan["limits"]["storageMb"] * MB)
            if limit < 0:
                continue
            quota.append({"kind": kind, "limit": limit,
                          "budget": totals["budget"][kind],
                          "spent": totals["spent"][kind],
                          "state": "over" if totals["spent"][kind] > limit
                                   else "within"})

    rows = []
    for account in sorted(set(entries) | set(spent)):
        if account is None:
            continue
        budget = (entries.get(account) or {}).get("budget")
        bucket = spent.get(account) or _zero(kinds)
        state = "within"
        if budget is not None:
            over = any(budget.get(kind) is not None and int(budget[kind]) >= 0
                       and bucket[kind] > int(budget[kind]) for kind in kinds)
            missing = any(budget.get(kind) is None and bucket[kind]
                          for kind in kinds)
            unlimited = budget and all(
                budget.get(kind) == -1 for kind in kinds
                if budget.get(kind) is not None) and not missing
            state = ("over" if over else "unbudgeted" if missing
                     else "unlimited" if unlimited else "within")
        else:
            state = "unbudgeted"
        row = {"account": account,
               "budget": {kind: int(budget.get(kind, 0)) if budget else 0
                          for kind in kinds} if budget else None,
               "spent": dict(bucket), "state": state}
        unit = (entries.get(account) or {}).get("unit")
        if unit:
            row["unit"] = str(unit)
        rows.append(row)

    findings.sort(key=lambda item: (ORDER.index(item["code"]),
                                    str(item["account"] or ""),
                                    str(item["kind"] or "")))
    return {"version": 1, "contract": "budget-reconciliation@1",
            "tenant": tenant, "period": str(case["period"]),
            "at": str(case["at"]), "plan": plan, "agents": rows,
            "totals": totals, "quota": quota, "findings": findings,
            "problems": problems}


def problems(case):
    """Everything wrong with a case: its store, its report, and the arithmetic."""
    found = []
    schema = json.loads(REPORT_SCHEMA.read_text())
    expected = case.get("expected")
    if not isinstance(expected, dict):
        return ["the case has no `expected` report"]
    try:
        jsonschema.validate(expected, schema)
    except jsonschema.exceptions.ValidationError as exc:
        where = "/".join(str(part) for part in exc.absolute_path) or "document"
        found.append(f"report {where}: {exc.message}")
    computed = reconcile(case)
    if computed != expected:
        for key in expected:
            if computed.get(key) != expected.get(key):
                found.append(f"report {key}: committed {json.dumps(expected[key], sort_keys=True)[:160]} "
                             f"!= computed {json.dumps(computed.get(key), sort_keys=True)[:160]}")
    return found


def _mutations(case):
    """Seven ways to be wrong; each must produce its code."""
    cases = []

    doc = copy.deepcopy(case)
    doc["subscription"] = {"plan": "ghost"}
    cases.append(("E-BUD-01", "an unknown plan", doc))

    doc = copy.deepcopy(case)
    doc["budgets"]["agents"][0]["budget"]["jobs"] = -2
    cases.append(("E-BUD-02", "a negative budget", doc))

    doc = copy.deepcopy(case)
    doc["budgets"]["agents"].append({"account": "admin-1",
                                     "budget": {"jobs": 10}})
    cases.append(("E-BUD-03", "a budget on a person", doc))

    doc = copy.deepcopy(case)
    doc["spend"].append({"account": "agent-co", "kind": "jobs", "quantity": 40})
    doc["budgets"]["agents"][0]["budget"].pop("jobs")
    cases.append(("E-BUD-04", "spend with no budget", doc))

    doc = copy.deepcopy(case)
    doc["budgets"]["agents"][0]["budget"]["jobs"] = 5000
    cases.append(("E-BUD-05", "budgets above the plan", doc))

    doc = copy.deepcopy(case)
    doc["spend"].append({"account": "agent-co", "kind": "documents",
                         "quantity": 500})
    cases.append(("E-BUD-06", "an agent past its budget", doc))

    doc = copy.deepcopy(case)
    doc["registry"]["team"]["jobsPerMonth"] = 100
    cases.append(("E-BUD-07", "the tenant past its plan", doc))
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
        print(json.dumps(reconcile(case), indent=2, ensure_ascii=False))
        return 0

    found = problems(case)
    if found:
        print(f"budget: {args.path} FAIL", file=sys.stderr)
        for problem in found:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.self_test:
        missed = []
        for code, label, doc in _mutations(case):
            codes = {item["code"] for item in reconcile(doc)["findings"]}
            if code not in codes:
                missed.append(f"{label} (wanted {code}, got {sorted(codes)})")
        if missed:
            print("budget --self-test RED: " + "; ".join(missed), file=sys.stderr)
            return 1
        print(f"budget --self-test: {len(_mutations(case))} mutations refused, the "
              f"committed case reconciles — OK")
        return 0

    report = reconcile(case)
    if args.json:
        print(json.dumps({"case": str(args.path), "contract": report["contract"],
                          "agents": len(report["agents"]),
                          "findings": [item["code"] for item in
                                       report["findings"]]}, indent=1))
        return 0
    print(f"budget: {report['tenant']} {report['period']} — "
          f"{len(report['agents'])} agent(s), plan "
          f"{(report['plan'] or {}).get('id', 'none')}, "
          f"{len(report['findings'])} finding(s): "
          f"{', '.join(item['code'] for item in report['findings']) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
