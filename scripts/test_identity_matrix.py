#!/usr/bin/env python3
"""Identity conformance matrix (issue #275, `tenant-identity@1`).

`check_identity_spec.py --self-test` proves each rule *bites* (a mutation is
refused at all). This proves the verdict is the sentence it should be, case by
case, and that the clean cases stay clean — a negative test that accepts the
wrong reason is a test that hides a regression.

    python scripts/test_identity_matrix.py
    python scripts/test_identity_matrix.py --json

Exit 0 = every case got its expected verdict. CI runs it beside the checker.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_identity_spec as C  # noqa: E402


def cases(valid):
    def copy():
        return json.loads(json.dumps(valid))

    def account(doc, account_id):
        return next(row for row in doc["accounts"] if row.get("id") == account_id)

    def agent(doc):
        return account(doc, "agent-kyc")

    out = [("the committed example", None, None)]

    doc = copy()
    doc["accounts"].append(copy()["accounts"][1])
    out.append(("duplicate account id", doc, "duplicate account id"))

    doc = copy()
    account(doc, "binh.tran")["sso"] = {"subject": "oneid:u_01HZX4M8Q3"}
    out.append(("two accounts on one ONEID subject", doc, "is bound to both"))

    doc = copy()
    agent(doc)["credential"] = {"algo": "x", "salt": "y", "hash": "z"}
    out.append(("an agent with a password", doc, "holds a login"))

    doc = copy()
    agent(doc)["sso"] = {"subject": "oneid:u_x"}
    out.append(("an agent with an SSO binding", doc, "holds a login"))

    doc = copy()
    account(doc, "binh.tran").pop("credential")
    out.append(("a person with no login", doc, "needs a credential"))

    doc = copy()
    agent(doc)["owner"] = "ghost"
    out.append(("an agent whose owner does not exist", doc,
                "owner 'ghost' is not an account"))

    doc = copy()
    first = agent(doc)
    first["id"] = "agent-a"
    doc["accounts"].append(dict(first, id="agent-b", owner="agent-a"))
    out.append(("an agent owned by an agent", doc, "is itself an agent"))

    doc = copy()
    account(doc, "an.nguyen")["status"] = "disabled"
    out.append(("an agent whose owner is disabled", doc, "owner 'an.nguyen' is disabled"))

    doc = copy()
    account(doc, "binh.tran")["role"] = "Credit Officer"
    out.append(("a role that is not a portal role", doc, "does not match"))

    doc = copy()
    account(doc, "binh.tran")["status"] = "gone"
    out.append(("an unknown status", doc, "is not one of"))

    doc = copy()
    agent(doc).pop("purpose")
    out.append(("an agent with no purpose", doc, "'purpose' is a required property"))

    doc = copy()
    account(doc, "binh.tran")["kind"] = "robot"
    out.append(("an unknown kind", doc, "is not one of"))

    doc = copy()
    account(doc, "binh.tran")["status"] = "disabled"
    out.append(("a disabled person with a login (valid)", doc, None))

    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    valid = json.loads(C.FIXTURE.read_text())
    rows = []
    failures = []
    for label, doc, expected in cases(valid):
        problems = C.problems(doc if doc is not None else valid)
        joined = "; ".join(problems)
        if expected is None:
            ok = not problems
        else:
            ok = any(expected in problem for problem in problems)
        rows.append({"case": label, "expected": expected or "clean",
                     "problems": problems, "ok": ok})
        if not ok:
            failures.append(f"{label}: expected {expected or 'clean'}, got "
                            f"{problems or 'clean'}")
    if args.json:
        print(json.dumps({"cases": rows}, indent=1))
    else:
        for row in rows:
            mark = "ok" if row["ok"] else "RED"
            print(f"  {mark:>3}  {row['case']}")
    if failures:
        print("identity matrix RED:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    clean = sum(1 for row in rows if not row["problems"])
    print(f"identity matrix: {len(rows)} cases — {len(rows) - clean} refusals with "
          f"their expected sentence, {clean} clean — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
