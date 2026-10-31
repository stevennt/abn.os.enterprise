#!/usr/bin/env python3
"""Deterministic sandbox generator (issue #102, plan D40).
One --seed drives ALL randomness; counters only — no clock/uuid/network.
Usage: python scripts/gen_sandbox.py --seed 42 --scale full|small --out /tmp/sbx
Outputs persons/accounts/loans/txns/complaints/aml_hits.jsonl + MANIFEST.sha256.
"""
import argparse, hashlib, json, random
from pathlib import Path

FIRST = ["An", "Binh", "Chi", "Dung", "Giang", "Hieu", "Lan", "Minh", "Ngoc", "Phuc"]
LAST = ["Nguyen Van", "Tran Thi", "Le Van", "Pham Thi", "Hoang Van", "Vu Thi"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--scale", choices=["full", "small"], default="small")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    n_persons = 10000 if a.scale == "full" else 100
    files = {}
    persons = [{"customer_id": f"C-{90000 + i}", "name": f"{rng.choice(LAST)} TEST{rng.choice(FIRST)}",
                "cccd": f"001099{i:06d}", "_synthetic_pii": True} for i in range(n_persons)]
    files["persons"] = persons
    accounts, loans, txns, complaints, hits = [], [], [], [], []
    ai = li = ti = 0
    for i, p in enumerate(persons):
        for _ in range(rng.choice([1, 1, 2, 2, 3])):
            ai += 1
            accounts.append({"account_id": f"A-{ai:06d}", "customer_id": p["customer_id"],
                             "product": rng.choice(["savings-flex", "current", "term-12m"]),
                             "_synthetic_pii": True})
        if rng.random() < 0.5:
            li += 1
            loans.append({"facility_id": f"APP-T{i:05d}", "customer_id": p["customer_id"],
                          "amount": rng.choice([100000000, 300000000, 500000000]),
                          "decision": "APPROVE" if rng.random() < 0.7 else "DECLINE",
                          "_synthetic_pii": True})
        for acc in [x for x in accounts if x["customer_id"] == p["customer_id"]]:
            for m in range(3 if a.scale == "full" else 1):
                for _ in range(rng.randint(25, 35) if a.scale == "full" else 2):
                    ti += 1
                    txns.append({"txn_id": f"T-{ti:07d}", "account_id": acc["account_id"],
                                 "month": m, "amount": rng.randint(100000, 50000000),
                                 "_synthetic_pii": True})
        if rng.random() < 0.02:
            complaints.append({"ticket": f"TKT-T{i:05d}", "customer_id": p["customer_id"],
                               "severity": rng.choice(["S3", "S3", "S4", "S2"]),
                               "_synthetic_pii": True})
        if rng.random() < 0.003:
            hits.append({"case": f"AML-T{i:05d}", "customer_id": p["customer_id"],
                         "_synthetic_pii": True})
    files.update({"accounts": accounts, "loans": loans, "txns": txns,
                  "complaints": complaints, "aml_hits": hits})
    manifest = []
    for name, rows in files.items():
        blob = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows) + "\n"
        (out / f"{name}.jsonl").write_text(blob)
        manifest.append(f"{hashlib.sha256(blob.encode()).hexdigest()}  {name}.jsonl")
    (out / "MANIFEST.sha256").write_text("\n".join(manifest) + "\n")
    counts = {k: len(v) for k, v in files.items()}
    print(f"seed={a.seed} scale={a.scale} counts={counts} out={out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
