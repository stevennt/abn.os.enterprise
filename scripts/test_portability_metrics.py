#!/usr/bin/env python3
"""The portability measures: five rules, each fired and each quiet (issue #330).

Acceptance:
  * a metric/alert exists and it fired in a drill

Exit 0 = green.
"""
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import portable as P  # noqa: E402


def metrics_module():
    spec = importlib.util.spec_from_file_location(
        "portability_metrics", ROOT / "scripts" / "portability_metrics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = metrics_module()
TINY = ROOT / "tests" / "fixtures" / "portability" / "tiny"
PLATFORM = "contract-2026.11.3"
NOW = datetime.datetime(2026, 11, 1, 9, 0, tzinfo=datetime.timezone.utc)


def tree(tmp, tag=None):
    """A checkout whose contract pin resolves: the template names its own commit."""
    root = Path(tmp) / "repo"
    shutil.copytree(TINY, root)
    if tag:
        def git(*argv):
            subprocess.run(["git", *argv], cwd=root, check=True,
                           capture_output=True)
        git("init", "-q")
        git("add", "-A")
        git("-c", "user.email=t@example.com", "-c", "user.name=T", "commit",
            "-qm", "seed")
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                              capture_output=True, text=True).stdout.strip()
        template = root / "companies" / "acme" / "paperclip-company.json"
        doc = json.loads(template.read_text())
        doc["contract"]["sha"] = head
        template.write_text(json.dumps(doc, indent=2) + "\n")
        git("add", "-A")
        git("-c", "user.email=t@example.com", "-c", "user.name=T", "commit",
            "-qm", "pin")
        git("tag", tag)
    return root


def rules(root, now=NOW):
    counters, alerts = M.metrics(root, now=now)
    return counters, [alert["id"] for alert in alerts]


def main():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        # P5: a compiled template with no stored bundle
        root = tree(tmp)
        counters, fired = rules(root)
        if fired != ["P5"]:
            problems.append(f"an unrecorded company fired {fired}")
        if counters["unrecorded"] != 1:
            problems.append(f"unrecorded counter is {counters['unrecorded']}")

        # a clean checkout: recorded, pinned at the tag the repo holds
        clean = tree(Path(tmp) / "clean", tag="contract-2026.11.1")
        P.record(clean, "acme", platform=PLATFORM, now=NOW.isoformat())
        counters, fired = rules(clean)
        if fired:
            problems.append(f"a clean checkout fired {fired}")

        # P1: the repository moved past the recorded pin
        moved = tree(Path(tmp) / "moved", tag="contract-2026.11.1")
        P.record(moved, "acme", platform=PLATFORM, now=NOW.isoformat())
        subprocess.run(["git", "tag", "contract-2026.11.3"], cwd=moved, check=True)
        counters, fired = rules(moved)
        if fired != ["P1"]:
            problems.append(f"a stale pin fired {fired}")
        if counters["stalePins"] != 1:
            problems.append(f"stalePins is {counters['stalePins']}")

        # P3: the live template moved after the record
        drifted = tree(Path(tmp) / "drifted", tag="contract-2026.11.1")
        P.record(drifted, "acme", platform=PLATFORM, now=NOW.isoformat())
        template = drifted / "companies" / "acme" / "paperclip-company.json"
        doc = json.loads(template.read_text())
        doc["label"] = "ACME (edited after the bundle)"
        template.write_text(json.dumps(doc, indent=2) + "\n")
        counters, fired = rules(drifted)
        if fired != ["P3"]:
            problems.append(f"a drifted company fired {fired}")

        # P2: a carrier edited after it was stored
        broken = tree(Path(tmp) / "broken", tag="contract-2026.11.1")
        payload, _f = P.record(broken, "acme", platform=PLATFORM,
                               now=NOW.isoformat())
        carrier = broken / payload["path"] / "bundle.json"
        doc = json.loads(carrier.read_text())
        doc["artefacts"][0]["sha256"] = "0" * 64
        carrier.write_text(json.dumps(doc))
        counters, fired = rules(broken)
        if "P2" not in fired:
            problems.append(f"an edited carrier fired {fired}")

        # P4: the newest bundle is old
        old = tree(Path(tmp) / "old", tag="contract-2026.11.1")
        long_ago = (NOW - datetime.timedelta(days=M.STALE_DAYS + 5)).isoformat()
        P.record(old, "acme", platform=PLATFORM, now=long_ago)
        counters, fired = rules(old)
        if fired != ["P4"]:
            problems.append(f"an old bundle fired {fired}")
        if counters["oldestDays"] < M.STALE_DAYS:
            problems.append(f"oldestDays is {counters['oldestDays']}")

    # the drill, and its quiet control
    if M.drill() != 0:
        problems.append("the drill did not fire every rule")

    if problems:
        print("portability metrics RED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"portability metrics: P1–P5 each fired on a real checkout (and stayed "
          f"quiet when clean), and the drill fired all five — OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
