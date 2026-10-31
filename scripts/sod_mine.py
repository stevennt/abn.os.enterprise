#!/usr/bin/env python3
"""SoD mining runner (issue #117): load sql/sod-mining.sql against sqlite,
run on a violating fixture (expect all 6 patterns) and a clean export (expect none).
Incident issue template printed per hit.
Run: python scripts/sod_mine.py. Exit 0 = fixture caught + clean green.
"""
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUERIES = (ROOT / "sql" / "sod-mining.sql").read_text().split(";")
QUERIES = [q.strip() for q in QUERIES if q.strip().startswith("-- Q") or q.strip().upper().startswith("SELECT")]
# split file into the 6 SELECT statements (comments carry the Q labels)
blocks, cur = [], ""
for line in (ROOT / "sql" / "sod-mining.sql").read_text().splitlines():
    if line.startswith("-- Q"):
        if cur.strip():
            blocks.append(cur)
        cur = line + "\n"
    else:
        cur += line + "\n"
blocks.append(cur)

SCHEMA = """CREATE TABLE audit_actions(instance_id TEXT, actor TEXT, actor_role TEXT,
action TEXT, target_role TEXT, decided_at TEXT, over_band INT DEFAULT 0,
hours_valid INT DEFAULT 0, reviewed_next_day INT DEFAULT 1)"""

VIOLATIONS = [
    ("I-1", "rm.a", "rm_officer", "MAKER_SUBMIT", None, "2026-10-01", 0, 0, 1),
    ("I-1", "rm.a", "credit_manager", "CHECKER_APPROVE", None, "2026-10-01", 0, 0, 1),
    ("I-2", "an.b", "aml_analyst", "MAKER_SUBMIT", None, "2026-10-01", 0, 0, 1),
    ("I-2", "an.b", "aml_analyst", "FILING_SUBMIT", None, "2026-10-01", 0, 0, 1),
    ("I-3", "op.c", "payments_operator", "MAKER_SUBMIT", None, "2026-10-01", 0, 0, 1),
    ("I-3", "op.d", "payments_manager", "CHECKER_APPROVE", None, "2026-10-01", 0, 0, 1),
    ("I-3", "op.c", "payments_operator", "DELEGATE_GRANT", "payments_manager", "2026-10-01", 0, 0, 1),
    ("I-4", "mg.e", "credit_manager", "CHECKER_APPROVE", None, "2026-10-01", 1, 0, 1),
    ("I-5", "ml.f", "compliance_manager", "FILING_SUBMIT", None, "2026-10-01", 0, 0, 1),
    ("I-6", "em.g", "ops_engineer", "DELEGATE_GRANT", "ops_engineer", "2026-10-01", 0, 72, 0),
]
CLEAN = [
    ("C-1", "rm.a", "rm_officer", "MAKER_SUBMIT", None, "2026-10-01", 0, 0, 1),
    ("C-1", "mg.b", "credit_manager", "CHECKER_APPROVE", None, "2026-10-01", 0, 0, 1),
    ("C-2", "ml.m", "mlro", "FILING_SUBMIT", None, "2026-10-01", 0, 0, 1),
]

TEMPLATE = ("incident: [SoD] {q} hit on {inst} by {actor} — "
            "open type:grc issue with actor/instance/pair (I88).")

def run_case(rows):
    con = sqlite3.connect(":memory:")
    con.execute(SCHEMA)
    con.executemany("INSERT INTO audit_actions(instance_id,actor,actor_role,action,target_role,decided_at,over_band,hours_valid,reviewed_next_day) VALUES (?,?,?,?,?,?,?,?,?)", rows)
    hits = []
    for b in blocks:
        label = b.splitlines()[0]
        sql = "\n".join(l for l in b.splitlines() if not l.startswith("--"))
        try:
            for inst, actor in con.execute(sql):
                hits.append((label, inst, actor))
        except Exception as e:
            print(f"QUERY ERROR {label}: {e}")
            return None
    return hits

def main():
    bad = run_case(VIOLATIONS)
    assert bad is not None and len({h[0] for h in bad}) == 6, f"want all 6 patterns, got {bad}"
    for label, inst, actor in bad:
        print(TEMPLATE.format(q=label.strip("- ").split(":")[0], inst=inst, actor=actor))
    good = run_case(CLEAN)
    assert good == [], f"clean export must be green, got {good}"
    print("sod-mine: 6/6 patterns caught on fixture, clean green — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
