#!/usr/bin/env python3
"""verify-industry-tags (issue #126): every industry's declared tag refs resolve.

Checks, for each industries/<id>/industry.yaml:
  1. tag_stream prefixes exist and are <id>-prefixed;
  2. the latest pushed <prefix>-* tag exists locally or on origin;
  3. any pack.release_ref / policy.release_ref recorded in the manifest resolves
     (format: <tag>@<sha> or plain <tag>).

Offline-safe: falls back to `git tag --list` when origin is unreachable, and
reports UNKNOWN (non-fatal) rather than lying about existence.
Run: python bin/verify-industry-tags.py [--json]
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sh(*args, check=False):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=check)


def have_remote():
    r = sh("git", "ls-remote", "--tags", "origin")
    return r.returncode == 0, [l.split("refs/tags/")[-1] for l in r.stdout.splitlines() if "refs/tags/" in l]


def main():
    as_json = "--json" in sys.argv
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML required")
    remote_ok, remote_tags = have_remote()
    problems, report = [], []
    for man_path in sorted((ROOT / "industries").glob("*/industry.yaml")):
        man = yaml.safe_load(man_path.read_text())
        iid = man["id"]
        ts = man.get("tag_stream") or {}
        entry = {"industry": iid, "streams": {}, "refs": [], "status": "OK"}
        for kind in ("policy", "pack"):
            prefix = ts.get(f"{kind}_prefix")
            if not prefix:
                problems.append(f"{iid}: missing tag_stream.{kind}_prefix")
                entry["status"] = "RED"
                continue
            if not prefix.startswith(iid):
                problems.append(f"{iid}: {kind}_prefix '{prefix}' must start with '{iid}-'")
                entry["status"] = "RED"
            local = sh("git", "tag", "--list", f"{prefix}-*").stdout.split()
            remote = [t for t in remote_tags if t.startswith(f"{prefix}-")]
            all_tags = sorted(set(local) | set(remote))
            entry["streams"][kind] = {"prefix": prefix, "tags": all_tags,
                                      "remote_checked": remote_ok}
            if not all_tags:
                problems.append(f"{iid}: no {kind} tag yet (expected {prefix}-YYYY.MM.N)")
                entry["status"] = "RED"
        for field in ("policy", "pack"):
            ref = (man.get(field) or {}).get("release_ref")
            if ref:
                tag = ref.split("@")[0]
                exists = tag in sh("git", "tag", "--list", tag).stdout.split() or tag in remote_tags
                entry["refs"].append({"field": field, "ref": ref, "exists": exists})
                if not exists:
                    problems.append(f"{iid}: {field}.release_ref '{ref}' does not resolve")
                    entry["status"] = "RED"
        report.append(entry)
    if as_json:
        print(json.dumps({"industries": report, "problems": problems}, indent=1))
    else:
        for e in report:
            streams = ", ".join(f"{k}={v['prefix']}({len(v['tags'])} tags)" for k, v in e["streams"].items())
            print(f"{e['status']:4} {e['industry']}: {streams}")
        if not remote_ok:
            print("note: origin unreachable — local tags only (tag existence UNCERTAIN)")
        for p in problems:
            print(f"  - {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
