#!/usr/bin/env python3
"""Classify a process-version diff as PATCH/MINOR/MAJOR (issue #6).
Usage: python scripts/migrate_check.py <old.yaml> <new.yaml>
Exit 0 + prints classification and required action.
"""
import sys
import yaml

def load(p):
    return yaml.safe_load(open(p))

TOP_REQUIRED = ["id", "version", "event_type", "inputs", "steps", "outputs", "kpis", "automation_target"]

def classify(old, new):
    assert old["id"] == new["id"], "process id changed: treat as NEW process, not a version"
    for k in TOP_REQUIRED:
        if k not in new:
            return "MAJOR", f"required key removed: {k}"
    old_steps = {s["id"]: s for s in old["steps"]}
    new_steps = {s["id"]: s for s in new["steps"]}
    for sid, s in old_steps.items():
        if sid not in new_steps:
            return "MAJOR", f"step removed: {sid}"
        for f in ("kind",):
            if s.get(f) != new_steps[sid].get(f):
                return "MAJOR", f"step {sid}: {f} changed"
    if set(new_steps) - set(old_steps):
        return "MINOR", f"new steps: {sorted(set(new_steps) - set(old_steps))} (dual-run window)"
    old_in = set((old.get("inputs") or {}).get("fields", []))
    new_in = set((new.get("inputs") or {}).get("fields", []))
    if new_in - old_in:
        return "MINOR", f"new optional inputs: {sorted(new_in - old_in)} (dual-run window)"
    if old_in - new_in:
        return "MAJOR", f"inputs removed: {sorted(old_in - new_in)}"
    return "PATCH", "auto-roll safe"

def main():
    old, new = load(sys.argv[1]), load(sys.argv[2])
    bump, reason = classify(old, new)
    action = {"PATCH": "auto-roll, no action",
              "MINOR": "open dual-run window per docs/core/versioning.md",
              "MAJOR": "migration + sunset date per docs/core/versioning.md"}[bump]
    print(f"{bump}: {reason} -> {action}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
