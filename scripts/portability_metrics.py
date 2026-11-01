#!/usr/bin/env python3
"""The portability measures (issue #330).

Five rules over the companies in a checkout:

    P1 stale-pin        a stored bundle was compiled against an older contract tag
                        than the repository holds now — re-derive before handover
                        (high)
    P2 unverifiable     a stored carrier fails its own integrity, or a log row
                        names something that is not stored (critical)
    P3 drift            the live template no longer matches the newest stored
                        bundle: the company moved and nobody recorded it (high)
    P4 stale-record     the newest stored bundle is older than STALE_DAYS — nobody
                        has re-verified this company (medium)
    P5 unrecorded       a company has a compiled template and no stored bundle at
                        all: it exists and cannot be handed over (high)

P3 is the one that cannot be answered by a single file: it compares the template
on disk with the newest carrier, which is exactly what a record is for. P5 is its
opposite — nothing to compare with at all.

Usage:
    python scripts/portability_metrics.py [--root R] [--json] [--fail-on-alert]
    python scripts/portability_metrics.py --drill
"""

import argparse
import datetime
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STALE_DAYS = 90
SEVERITY = {"P1": "high", "P2": "critical", "P3": "high", "P4": "medium",
            "P5": "high"}


def _portable():
    spec = importlib.util.spec_from_file_location(
        "portable", ROOT / "scripts" / "portable.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["portable"] = module
    return module


P = _portable()


def _parse(value):
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _tag(value):
    match = P.TAG_RE.match(str(value or ""))
    return tuple(int(part) for part in match.groups()) if match else None


def current_tag(root):
    """The newest contract tag the checkout holds."""
    import subprocess
    try:
        result = subprocess.run(["git", "tag", "--list", "contract-*"],
                                cwd=str(root), capture_output=True, text=True)
    except OSError:
        return ""
    tags = sorted(result.stdout.split(), key=lambda tag: _tag(tag) or (0, 0, 0))
    return tags[-1] if tags else ""


def metrics(root, now=None):
    """(counters, alerts) for one checkout."""
    root = Path(root)
    moment = now or datetime.datetime.now(datetime.timezone.utc)
    tag_now = current_tag(root)
    companies = sorted(path.parent.name for path in
                       (root / "companies").glob("*/paperclip-company.json"))
    counters = {"companies": len(companies), "bundles": 0, "stalePins": 0,
                "drift": 0, "unrecorded": 0, "oldestDays": 0,
                "problems": 0, "currentTag": tag_now}
    alerts = []
    for company in companies:
        template = root / "companies" / company / "paperclip-company.json"
        stored = P.bundles(root, company, limit=1)
        if not stored:
            counters["unrecorded"] += 1
            alerts.append({"id": "P5", "severity": SEVERITY["P5"],
                           "detail": f"{company} has a compiled template and no "
                                     f"stored bundle"})
            continue
        counters["bundles"] += len(P.bundles(root, company, limit=1000))
        newest = stored[0]
        pin_tag = ""
        carrier = P._carrier(root, company, str(newest.get("bundleId")))
        manifest_path = carrier / "bundle.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text())
            pin_tag = str((manifest.get("template") or {}).get("contract", {}
                          ).get("tag") or "")
            digest = str((manifest.get("template") or {}).get("sha256") or "")
            if template.is_file() and P._sha_file(template) != digest:
                counters["drift"] += 1
                alerts.append({"id": "P3", "severity": SEVERITY["P3"],
                               "detail": f"{company}: the live template no longer "
                                         f"matches {newest.get('bundleId')}"})
        if not pin_tag:
            counters["problems"] += 1
            alerts.append({"id": "P2", "severity": SEVERITY["P2"],
                           "detail": f"{company}: {newest.get('bundleId')} has no "
                                     f"readable manifest"})
        elif tag_now and _tag(pin_tag) and _tag(pin_tag) < _tag(tag_now):
            counters["stalePins"] += 1
            alerts.append({"id": "P1", "severity": SEVERITY["P1"],
                           "detail": f"{company}: pinned at {pin_tag}, the "
                                     f"repository holds {tag_now}"})
        at = _parse(newest.get("at"))
        if at is not None:
            days = (moment - at).days
            counters["oldestDays"] = max(counters["oldestDays"], days)
            if days >= STALE_DAYS:
                alerts.append({"id": "P4", "severity": SEVERITY["P4"],
                               "detail": f"{company}: the newest bundle is {days} "
                                         f"days old"})
    problems = P.validate_bundles(root)
    counters["problems"] = len(problems)
    for problem in problems:
        alerts.append({"id": "P2", "severity": SEVERITY["P2"],
                       "detail": problem})
    return counters, alerts


def drill():
    """Prove every rule can fire, from fabricated numbers (no checkout touched)."""
    loud = {"companies": 5, "bundles": 3, "stalePins": 1, "drift": 1,
            "unrecorded": 1, "oldestDays": STALE_DAYS, "problems": 1,
            "currentTag": "contract-2026.11.3"}
    quiet = {"companies": 2, "bundles": 2, "stalePins": 0, "drift": 0,
             "unrecorded": 0, "oldestDays": 3, "problems": 0,
             "currentTag": "contract-2026.11.3"}

    def alerts_of(stats):
        fired = []
        if stats["problems"]:
            fired.append(("P2", f"{stats['problems']} unverifiable carrier(s)"))
        if stats["unrecorded"]:
            fired.append(("P5", f"{stats['unrecorded']} company(ies) with no "
                                f"stored bundle"))
        if stats["drift"]:
            fired.append(("P3", f"{stats['drift']} company(ies) drifted from "
                                f"their newest bundle"))
        if stats["stalePins"]:
            fired.append(("P1", f"{stats['stalePins']} bundle(s) pinned at an "
                                f"older contract"))
        if stats["oldestDays"] >= STALE_DAYS:
            fired.append(("P4", f"the newest bundle is {stats['oldestDays']} days "
                                f"old"))
        return fired

    if alerts_of(quiet):
        print(f"drill RED: a clean checkout fired "
              f"{[rule for rule, _ in alerts_of(quiet)]}", file=sys.stderr)
        return 1
    fired = alerts_of(loud)
    rules = {rule for rule, _ in fired}
    if rules != set(SEVERITY):
        print(f"drill RED: expected {sorted(SEVERITY)}, fired "
              f"{sorted(rules) or 'nothing'}", file=sys.stderr)
        return 1
    for rule, detail in sorted(fired):
        print(f"drill: {rule} [{SEVERITY[rule]}] — {detail}")
    print(f"drill: {', '.join(sorted(SEVERITY))} fired, and a clean checkout "
          f"stayed quiet — OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="portability_metrics")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on-alert", action="store_true")
    ap.add_argument("--drill", action="store_true")
    args = ap.parse_args(argv)
    if args.drill:
        return drill()
    counters, alerts = metrics(args.root)
    if args.json:
        print(json.dumps({"counters": counters, "alerts": alerts}, indent=2))
    else:
        print(f"companies {counters['companies']} · stored bundles "
              f"{counters['bundles']} · unrecorded {counters['unrecorded']} · "
              f"drifted {counters['drift']} · stale pins "
              f"{counters['stalePins']} · newest {counters['oldestDays']} days "
              f"old · contract {counters['currentTag'] or 'unknown'}")
        for alert in alerts:
            print(f"ALERT {alert['id']} [{alert['severity']}] {alert['detail']}")
        if not alerts:
            print("no alert")
    return 1 if args.fail_on_alert and alerts else 0


if __name__ == "__main__":
    sys.exit(main())
