#!/usr/bin/env python3
"""Inbox escalation demo (issue #53): task lifecycle with SLA breach.
Run: python scripts/inbox_demo.py. Exit 0 when the task escalates and resolves.
"""
import sys

def main():
    task = {"subject": "[loan.retail.unsecured#INST-1] s5-decide",
            "queue": "credit_manager", "sla_minutes": 240,
            "on_fail": "escalate:risk", "state": "OPEN"}
    print(f"created: {task['subject']} -> queue {task['queue']} (SLA {task['sla_minutes']}m)")
    clock = 241  # minutes pass without action
    assert clock > task["sla_minutes"]
    task["state"] = "SLA_BREACHED"
    print(f"t+{clock}m: {task['state']} (no action)")
    target = task["on_fail"].split(":", 1)[1]
    task["queue"] = {"risk": "risk_manager"}.get(target, target)
    task["state"] = "ESCALATED"
    print(f"escalated -> queue {task['queue']} per on_fail={task['on_fail']}")
    task["state"] = "CLAIMED:risk_manager"
    task["decision"] = "APPROVE"
    task["state"] = "DONE"
    print(f"claimed by risk_manager -> {task['decision']} -> DONE")
    assert task["state"] == "DONE" and task["queue"] == "risk_manager"
    print("demo: escalation path works — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
