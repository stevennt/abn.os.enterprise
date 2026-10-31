#!/usr/bin/env python3
"""Drift regression test (issue #140): prove pack_rule_drift actually catches a
policy change that forgot the prose, on a COPY of a real industry.

Why a copy: the earlier attempt to prove it by editing the real rule file only
changed one of two occurrences of 0.95, so the allowed set still contained it and
the check (correctly) passed. That was a bad proof, not a broken checker — so the
proof is now a reproducible test that mutates every occurrence.

Run: python scripts/test_drift.py
"""
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from pack_rule_drift import check  # noqa: E402


def mutate_all(path, old, new):
    text = path.read_text()
    hits = text.count(old)
    assert hits, f"{old} not found in {path.name}"
    path.write_text(text.replace(old, new))
    return hits


def main():
    src = ROOT / "industries" / "banking"
    tmp = Path(tempfile.mkdtemp(prefix="drift-"))
    try:
        dst = tmp / "banking"
        shutil.copytree(src, dst)

        ok, compared, _ = check(dst, dst / "pack")
        assert not ok, f"baseline copy should be clean, got {ok}"
        assert compared >= 2, f"expected >=2 compared thresholds, got {compared}"
        print(f"baseline: {compared} prose thresholds match the copied rules")

        # the real bug: rule threshold changes, prose does not
        n = mutate_all(dst / "rules" / "aml-pack.yaml", "0.95", "0.97")
        problems, compared2, _ = check(dst, dst / "pack")
        assert problems, "drift was NOT detected — the check is broken"
        assert any("0.95" in p for p in problems), problems
        print(f"drifted rule ({n} occurrences 0.95->0.97): caught — {problems[0][:90]}")

        # and the honest fix passes: prose follows the rule
        mutate_all(dst / "pack" / "skills" / "banking-kyc-screening" / "SKILL.md",
                   "0.95", "0.97")
        fixed, _, _ = check(dst, dst / "pack")
        assert not fixed, f"prose updated but still red: {fixed}"
        print("prose updated to 0.97: green again")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
