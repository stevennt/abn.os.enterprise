#!/usr/bin/env python3
"""DLQ replay drill (issue #112, specs A04/D39): inject NO_ROUTE dead letter,
triage under SLO, fix routing, replay with original keys, assert single handling.
Run: python scripts/dlq_drill.py. Exit 0 = drill green.
"""
import sys
import time

ROUTING = {"loan.application.submitted": "loan.retail.unsecured v1.3.0"}
HANDLED = {}

def route(ev):
    return ROUTING.get(ev["event_type"])

def handle(ev):
    key = ev["idempotency_key"]
    if key in HANDLED:
        return "duplicate-suppressed"
    HANDLED[key] = ev["event_type"]
    return "handled"

def main():
    t0 = time.monotonic()
    ghost = {"event_type": "loan.topup.requested", "event_version": "1.0.0",
             "idempotency_key": "C-1+TOPUP-9", "payload": {"amount": 50000000}}
    dlq = []
    if route(ghost) is None:
        dlq.append({"event": ghost, "reason": "NO_ROUTE", "at": t0})
        print(f"injected: {ghost['event_type']} -> DLQ (NO_ROUTE)")
    triage_s = time.monotonic() - t0
    assert triage_s < 24 * 3600, "triage SLO breached (1 business day)"
    print(f"triage in {triage_s:.3f}s (SLO: 1 business day) — OK")
    ROUTING["loan.topup.requested"] = "loan.retail.unsecured v1.3.0"
    print("fix: routing row added (E46 fast path)")
    for item in dlq:
        ev = dict(item["event"], replay_of=item["event"]["idempotency_key"],
                  replay_reason="NO_ROUTE-fixed")
        assert ev["idempotency_key"] == ghost["idempotency_key"], "key must survive"
        r1 = handle(ev)
        r2 = handle(ev)
        assert (r1, r2) == ("handled", "duplicate-suppressed"), (r1, r2)
        print(f"replayed {ev['event_type']}: first={r1}, redelivery={r2} (key {ev['idempotency_key']})")
    print("drill: triage->fix->replay green, keys survive — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
