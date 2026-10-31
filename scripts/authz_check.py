#!/usr/bin/env python3
"""Sample authorization checks for engine/authz.fga (issue #17).
viewer = owner|assignee|auditor; approver/writer/resolver = assignee only.
Run: python scripts/authz_check.py. Exit 0 = all checks pass.
"""
import sys
import yaml

RULES = {
    ("loan_application", "viewer"): ("owner", "assigned_officer", "auditor"),
    ("loan_application", "approver"): ("assigned_officer",),
    ("loan_application", "writer"): ("assigned_officer",),
    ("complaint", "viewer"): ("owner", "assigned_agent", "auditor"),
    ("complaint", "resolver"): ("assigned_agent",),
}
ASSIGNEE = {"loan_application": "assigned_officer", "complaint": "assigned_agent"}

def load_tuples(p):
    out = set()
    for u, r, o in yaml.safe_load(open(p)):
        otype = o.split(":")[0]
        base = {"loan": "loan_application", "complaint": "complaint"}.get(otype, otype)
        out.add((u, r, base, o))
    return out

def can(tuples, user, relation, obj):
    otype = {"loan": "loan_application", "complaint": "complaint"}.get(obj.split(":")[0], obj)
    return any((user, r, otype, obj) in tuples for r in RULES[(otype, relation)])

def main():
    t = load_tuples("engine/authz-tuples.yaml")
    checks = [
        ("owner sees own case", can(t, "user:ownerA", "viewer", "loan:APP-1"), True),
        ("stranger denied", can(t, "user:strangerX", "viewer", "loan:APP-1"), False),
        ("auditor read-only: view ok", can(t, "user:auditor1", "viewer", "loan:APP-1"), True),
        ("auditor read-only: approve denied", can(t, "user:auditor1", "approver", "loan:APP-1"), False),
        ("officer approves", can(t, "user:officer1", "approver", "loan:APP-1"), True),
    ]
    failed = 0
    for name, got, want in checks:
        ok = got == want
        failed += not ok
        print(f"{'PASS' if ok else 'FAIL'}: {name} (got={got}, want={want})")
    print(f"authz: {len(checks) - failed}/{len(checks)} checks pass")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
