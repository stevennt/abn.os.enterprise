#!/usr/bin/env python3
"""Audit hash chain (issue #5): append + verify.
hash[i] = sha256(canonical(envelope without `hash`)), chaining hash_prev.
Run: python scripts/audit_chain.py --demo
"""
import hashlib, json, sys

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest(env):
    return hashlib.sha256(canon({k: v for k, v in env.items() if k != "hash"}).encode()).hexdigest()

def append(chain, step_id, actor, decision=None, rule_version=None, model_version=None, ts=0):
    env = {"id": f"ae-{len(chain):04d}", "version": "1.0.0",
           "instance_id": "demo-1", "seq": len(chain), "step_id": step_id, "actor": actor,
           "decision": decision, "rule_version": rule_version, "model_version": model_version,
           "inputs_hash": None, "payload_ref": None, "ts": ts,
           "hash_prev": chain[-1]["hash"] if chain else "GENESIS"}
    env["hash"] = digest(env)
    chain.append(env)
    return env

def verify(chain):
    prev = "GENESIS"
    for i, env in enumerate(chain):
        if env.get("seq") != i or env.get("hash_prev") != prev:
            return False, f"link broken at seq {i}"
        if env.get("hash") != digest(env):
            return False, f"hash mismatch at seq {i}"
        prev = env["hash"]
    return True, f"{len(chain)} events chained OK"

def main():
    chain = []
    append(chain, "s1-verify", "system", "PASS", "KYC-01@2026-10-01", None, 1)
    append(chain, "s2-extract", "ai:doc-extract@2026-10-20", "FIELDS", None, "doc-extract@2026-10-20", 2)
    append(chain, "s5-decide", "credit_manager", "APPROVE", "CREDIT-GRID-11@2026-09-01", None, 3)
    ok, msg = verify(chain)
    print("verify clean chain:", ok, "-", msg)
    assert ok
    chain[1]["decision"] = "TAMPERED"
    ok2, msg2 = verify(chain)
    print("verify tampered chain:", ok2, "-", msg2)
    assert not ok2, "tamper must be detected"
    print("demo: tamper detected — OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
