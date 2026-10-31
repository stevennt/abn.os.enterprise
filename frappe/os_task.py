"""OS Task controller (issue #106): SoD-at-claim + escalation timers.
Pure logic (no frappe import) so CI can test it; wire into a Frappe app's
os_task.py hooks at pilot time (bench: frappe-bench-new, app os_inbox).
SoD pairs mirror docs/core/sod.md forbidden list by (maker_role, checker_role).
"""
from datetime import datetime, timedelta

SOD_PAIRS = {
    ("rm_officer", "credit_manager"), ("aml_analyst", "mlro"),
    ("analyst", "manager"), ("payments_operator", "payments_manager"),
    ("ops_engineer", "itops_manager"), ("accountant", "finance_manager"),
    ("trade_specialist", "trade_manager"), ("fraud_analyst", "cards_manager"),
}
ESCALATE_AFTER_MIN = {"review": 60, "default": 240}

def check_claim(task, claimer, claimer_role):
    """Return (ok, reason). Deny self-approval and forbidden maker/checker pairs."""
    maker = task.get("maker")
    if maker and maker == claimer:
        return False, "self-approval denied (B19 universal ban)"
    pair = (task.get("maker_role"), claimer_role)
    if pair[0] and pair in SOD_PAIRS:
        return False, f"SoD conflict: {pair[0]} may not check as {pair[1]}"
    return True, "ok"

def escalation_due(created_min_epoch, on_fail, sla_minutes=240):
    """Next action + due epoch from on_fail lane (F58 forms)."""
    return {"lane": on_fail or "escalate:role-queue",
            "due_epoch": created_min_epoch + sla_minutes * 60}

def delegate(task, to, until_days=14):
    if until_days > 14:
        return False, "delegation max 14 days (B19)"
    task["delegate_to"] = to
    return True, "ok"
