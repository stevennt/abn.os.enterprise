#!/usr/bin/env python3
"""Bundle determinism test (issue #130). Builds the banking pack twice into temp
dirs and asserts byte-identical archives + working verify; then tampers a copy and
asserts verify rejects it. Stdlib only.
Run: python scripts/test_bundle.py
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "bin" / "build-pack"
PY = sys.executable


def run(*args):
    return subprocess.run([PY, str(BUILD), *args], cwd=ROOT, capture_output=True, text=True)


def bundle_in(d):
    found = sorted(Path(d).glob("*.tar.gz"))
    return found[0] if found else None


def main():
    t1, t2 = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    try:
        for d in (t1, t2):
            r = run("banking", "--out", str(d))
            if r.returncode != 0:
                print(f"FAIL build: {r.stdout[-400:]}{r.stderr[-400:]}")
                return 1
        b1, b2 = bundle_in(t1), bundle_in(t2)
        if not b1 or not b2:
            print("FAIL: no bundle produced")
            return 1
        h1 = hashlib.sha256(b1.read_bytes()).hexdigest()
        h2 = hashlib.sha256(b2.read_bytes()).hexdigest()
        if h1 != h2:
            print(f"FAIL: not deterministic\n  {h1}\n  {h2}")
            return 1
        print(f"deterministic: {b1.name} sha256 {h1[:16]}… (two builds identical)")

        r = run("--verify", str(b1))
        if r.returncode != 0:
            print(f"FAIL verify on pristine bundle: {r.stdout[-300:]}")
            return 1
        print("verify: pristine bundle accepted")

        tampered = b1.with_name("tampered.tar.gz")
        shutil.copy2(b1, tampered)
        with open(tampered, "ab") as fh:
            fh.write(b"TAMPER")
        man = b1.with_name(b1.name.replace(".tar.gz", ".MANIFEST.sha256"))
        tampered_man = tampered.with_name(tampered.name.replace(".tar.gz", ".MANIFEST.sha256"))
        shutil.copy2(man, tampered_man)
        r = run("--verify", str(tampered))
        if r.returncode == 0:
            print("FAIL: tampered bundle was accepted")
            return 1
        print("verify: tampered bundle rejected")
        return 0
    finally:
        shutil.rmtree(t1, ignore_errors=True)
        shutil.rmtree(t2, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
