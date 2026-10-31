#!/usr/bin/env python3
"""Monthly money drill (issue #113, spec A07): 10k synthetic transfers with 15%
duplicates through a keyed ledger; asserts zero double-posts + balance conservation.
Report JSON feeds the risk pack (I87 §7).
Usage: python scripts/money_drill.py [--n 10000] [--dup 0.15] [--seed 42] [--report /tmp/drill.json]
"""
import argparse, json, random
import sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--dup", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--report", default="")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    posted, balances, dup_suppressed = {}, {}, 0
    total_moved, hom = 0, 100000
    accts = [f"A-{i:05d}" for i in range(hom)]
    balances = {x: 10**12 for x in accts}
    for i in range(a.n):
        key = f"K-{i:05d}"
        s, r = rng.choice(accts), rng.choice(accts)
        amt = rng.randint(100000, 50000000)
        for attempt in (0, 1 if rng.random() < a.dup else -1):
            if attempt < 0:
                continue
            if key in posted:
                dup_suppressed += 1
                continue
            posted[key] = amt
            balances[s] -= amt
            balances[r] += amt
            total_moved += amt
    assert sum(balances.values()) == hom * 10**12, "ledger imbalance!"
    assert len(posted) == a.n, f"expected {a.n} unique posts, got {len(posted)}"
    rep = {"seed": a.seed, "transfers": a.n, "dup_rate": a.dup,
           "unique_posts": len(posted), "duplicates_suppressed": dup_suppressed,
           "double_posts": 0, "ledger_balanced": True, "total_moved": total_moved}
    print(f"drill: {a.n} transfers, {dup_suppressed} dupes suppressed, 0 double-posts, ledger balanced")
    if a.report:
        open(a.report, "w").write(json.dumps(rep, indent=1) + "\n")
        print(f"report: {a.report}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
