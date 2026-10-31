#!/usr/bin/env python3
"""OS Task logic tests (issue #106). Run: python frappe/test_os_task.py."""
import sys
sys.path.insert(0, "frappe")
from os_task import check_claim, escalation_due, delegate

def main():
    t = {"maker": "rm.a", "maker_role": "rm_officer"}
    assert check_claim(t, "rm.a", "credit_manager") == (False, "self-approval denied (B19 universal ban)")
    ok, why = check_claim(t, "mgr.b", "credit_manager")
    assert not ok and "SoD conflict" in why, (ok, why)
    ok, _ = check_claim({"maker": "x", "maker_role": "cs_agent"}, "mgr.b", "credit_manager")
    assert ok
    d = escalation_due(1000, "escalate:risk", 240)
    assert d == {"lane": "escalate:risk", "due_epoch": 1000 + 14400}, d
    assert delegate({}, "x", 15)[0] is False
    assert delegate({}, "x", 7)[0] is True
    print("os_task: SoD deny + escalation + delegation bounds — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
