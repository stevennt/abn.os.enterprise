#!/usr/bin/env python3
"""The bundle record: stored carriers, a log, and a rollback (issue #326).

Acceptance:
  * the record is written per run and validated by the repo's own
    sync/validators

A bundle id is content. Recording the same state twice is a silent no-op, a
different carrier at an existing id is refused, every stored carrier verifies
against its own manifest, and a rollback is an import of a stored id — deliberate,
so it needs `--force` when it overwrites.

Exit 0 = green.
"""
import json
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


def codes(findings):
    return [code for code, _reason in findings]


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = tree(tmp)
        payload, findings = P.record(root, "acme", platform=PLATFORM,
                                     now="2026-11-01T09:00:00.000Z")
        if findings:
            problems.append(f"record refused: {findings}")
        if not payload or not payload.get("recorded"):
            problems.append(f"record did not report a write: {payload}")
        carrier = root / payload["path"] if payload else None
        if carrier and not (carrier / "bundle.json").is_file():
            problems.append("the carrier has no bundle.json")
        if carrier and not (carrier / "paperclip-company.json").is_file():
            problems.append("the carrier has no template beside the manifest")

        again, _findings = P.record(root, "acme", platform=PLATFORM)
        if again and again.get("recorded") is not False:
            problems.append(f"a second identical record wrote again: {again}")
        rows = P.log_rows(root, "acme")
        if len(rows) != 1:
            problems.append(f"the log has {len(rows)} row(s) for one export")

        if P.validate_bundles(root):
            problems.append(f"a clean store does not validate: "
                            f"{P.validate_bundles(root)}")
        if P.bundles(root, "acme")[0]["bundleId"] != payload["bundleId"]:
            problems.append("the newest log row is not the bundle just recorded")

        # a carrier edited after it was stored is refused, by either code
        if carrier:
            stored = carrier / "bundle.json"
            doc = json.loads(stored.read_text())
            doc["artefacts"][0]["sha256"] = "0" * 64
            stored.write_text(json.dumps(doc))
            _payload, refused = P.record(root, "acme", platform=PLATFORM)
            if not ({"E-PORT-01", "E-PORT-04"} & set(codes(refused))):
                problems.append(f"an edited carrier was accepted: {refused}")
            if P.validate_bundles(root) == []:
                problems.append("an edited carrier passed validate_bundles")
            shutil.rmtree(carrier)  # restore for the rollback test

        # record again, then roll back over a stale template
        first, _f = P.record(root, "acme", platform=PLATFORM,
                             now="2026-11-01T09:30:00.000Z")
        template = root / "companies" / "acme" / "paperclip-company.json"
        doc = json.loads(template.read_text())
        doc["label"] = "ACME (edited after the bundle)"
        template.write_text(json.dumps(doc, indent=2) + "\n")

        _payload, refused = P.rollback(root, "acme", first["bundleId"])
        if "E-PORT-08" not in codes(refused):
            problems.append(f"a rollback overwrote without --force: {refused}")
        rolled, findings = P.rollback(root, "acme", first["bundleId"], force=True)
        if findings:
            problems.append(f"rollback with --force refused: {findings}")
        restored = json.loads(template.read_text())
        if restored.get("label") != "ACME":
            problems.append(f"the rollback did not restore the template: "
                            f"{restored.get('label')!r}")
        if P.log_rows(root, "acme")[-1].get("action") != "rollback":
            problems.append("the rollback left no log row")
        # the round trip still exports the same id
        manifest, _f = P.export(root, "acme", platform=PLATFORM)
        if manifest["bundleId"] != first["bundleId"]:
            problems.append(f"after a rollback the export is "
                            f"{manifest['bundleId']}, not {first['bundleId']}")

        # a log row naming an unstored bundle is refused
        with open(root / "companies" / "acme" / P.BUNDLES / P.LOGFILE, "a") as fh:
            fh.write(json.dumps({"version": 1, "at": "2026-11-02T00:00:00.000Z",
                                 "company": "acme",
                                 "bundleId": "bundle-ghost",
                                 "templateSha256": "0" * 64, "artefacts": 0,
                                 "action": "export"}) + "\n")
        ghost = [problem for problem in P.validate_bundles(root)
                 if "bundle-ghost" in problem]
        if not ghost:
            problems.append("a log row naming a missing carrier was accepted")

    if problems:
        print("portable record RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("portable record: stored carrier, silent re-record, changed carrier "
          "refused, rollback with --force and its log row, ghost row refused — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
