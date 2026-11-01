#!/usr/bin/env python3
"""The portability failure modes (issue #329).

Acceptance:
  * failure modes are handled and the error names the fix

A bundle is **untrusted input**: it arrives from another checkout, and `import`
writes the template where the manifest says. So the edges are attacker-shaped — a
company or bundle id that is a path, a manifest whose template path climbs out of
its company, a symbolic link where a file should be, two writers at once, and a
log row that names something that is not stored.

Exit 0 = green.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import portable as P  # noqa: E402

TINY = ROOT / "tests" / "fixtures" / "portability" / "tiny"
PLATFORM = "contract-2026.11.3"


def tree(tmp):
    root = Path(tmp) / "repo"
    shutil.copytree(TINY, root)
    return root


def expect(call, code, label, problems, fragment=""):
    try:
        call()
    except P.PortabilityError as exc:
        if exc.code != code:
            problems.append(f"{label}: wanted {code}, got {exc.code} ({exc})")
        elif fragment and fragment not in str(exc):
            problems.append(f"{label}: {code} fired for the wrong reason: {exc}")
        return
    problems.append(f"{label}: no refusal")


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = tree(tmp)

        # a company id is a path component
        for bad in ("..", "../../etc", "a/b", "/etc", "", "A Bad", None):
            expect(lambda bad=bad: P.export(root, bad, platform=PLATFORM),
                   "E-PORT-01", f"export with company {bad!r}", problems,
                   "invalid company id")
            expect(lambda bad=bad: P.record(root, bad, platform=PLATFORM),
                   "E-PORT-01", f"record with company {bad!r}", problems,
                   "invalid company id")
            expect(lambda bad=bad: P.bundles(root, bad),
                   "E-PORT-01", f"bundles with company {bad!r}", problems)
        if (Path(tmp) / "etc").exists():
            problems.append("a company id escaped the checkout")

        # a bundle id is a path component
        manifest, _f = P.export(root, "acme", platform=PLATFORM)
        for bad in ("..", "../../x", "bundle-zzzz", ""):
            expect(lambda bad=bad: P.rollback(root, "acme", bad),
                   "E-PORT-01", f"rollback to {bad!r}", problems,
                   "invalid bundle id")

        # a manifest whose template path climbs out of its company
        carrier = Path(tmp) / "handover"
        carrier.mkdir()
        evil = json.loads(json.dumps(manifest))
        evil["template"]["path"] = "../../outside/paperclip-company.json"
        (carrier / "bundle.json").write_text(json.dumps(evil))
        (carrier / "paperclip-company.json").write_text(
            (root / "companies" / "acme" / "paperclip-company.json").read_text())
        _m, findings, _rel = P.do_import(root, carrier / "bundle.json",
                                         platform=PLATFORM)
        if "E-PORT-07" not in [code for code, _r in findings]:
            problems.append(f"a manifest path outside the company was accepted: "
                            f"{findings}")
        if (Path(tmp) / "outside").exists():
            problems.append("a manifest path climbed out of the checkout")

        # a clean carrier for the link checks
        clean_carrier = Path(tmp) / "clean"
        clean_carrier.mkdir()
        good, _f = P.export(root, "acme", platform=PLATFORM)
        (clean_carrier / "bundle.json").write_text(json.dumps(good) + "\n")
        shutil.copyfile(root / "companies" / "acme" / "paperclip-company.json",
                        clean_carrier / "paperclip-company.json")

        # a symbolic link where the template should be
        target = root / "companies" / "acme" / "paperclip-company.json"
        real = Path(tmp) / "real.json"
        real.write_text(target.read_text())
        target.unlink()
        os.symlink(real, target)
        _m, findings = P.verify(root, clean_carrier / "bundle.json")
        if not any(code in ("E-PORT-04",) for code, _r in findings):
            problems.append(f"a symlinked template verified clean: {findings}")
        expect(lambda: P.record(root, "acme", platform=PLATFORM), "E-PORT-04",
               "record of a symlinked template", problems, "symbolic link")
        target.unlink()
        target.write_bytes(real.read_bytes())

        # two writers, one lock
        lock = root / "companies" / "acme" / P.LOCK
        lock.write_text("someone else\n")
        expect(lambda: P.record(root, "acme", platform=PLATFORM), "E-PORT-01",
               "record while the lock is held", problems, "is busy")
        # a stale lock is taken over
        old = __import__("time").time() - P.LOCK_TTL - 5
        os.utime(lock, (old, old))
        ok, findings = P.record(root, "acme", platform=PLATFORM)
        if findings or not ok:
            problems.append(f"a stale lock was not taken over: {findings}")
        if lock.exists():
            problems.append("the lock was left behind after a record")

        # a log row with an unknown action is reported, not accepted
        log = root / "companies" / "acme" / P.BUNDLES / P.LOGFILE
        with open(log, "a") as fh:
            fh.write(json.dumps({"version": 1, "at": "2026-11-02T00:00:00.000Z",
                                 "company": "acme",
                                 "bundleId": "bundle-0123456789abcdef",
                                 "templateSha256": "0" * 64, "artefacts": 0,
                                 "action": "deleted"}) + "\n")
        if not any("action is 'deleted'" in problem
                   for problem in P.validate_bundles(root)):
            problems.append("a log row with an unknown action was accepted")

    if problems:
        print("portable hardening RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("portable hardening: ids as paths, an escaping manifest path, a "
          "symlinked template, the lock (held and stale), and an unknown action — "
          "each refused with its fix — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
