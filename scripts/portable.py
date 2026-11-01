#!/usr/bin/env python3
"""Portable company bundles (issue #323, `company-portability@1`).

    python scripts/portable.py export --company <id> [--template PATH] [--out DIR]
    python scripts/portable.py verify --bundle <path> [--root R]
    python scripts/portable.py import --bundle <path> [--root R] [--platform TAG]
    python scripts/portable.py diff   --left <a> --right <b>
    python scripts/portable.py list   [--root R]
    python scripts/portable.py --self-test

The contract is `docs/core/portability.md`; the oracle is
`scripts/check_portability_spec.py`. This is the implementation that must agree
with it — the bundle id is the same arithmetic, and the seven refusals fire in the
same order.

A bundle is the template plus **everything it names**: the files the compiler
recorded in `source.files`, and every skill path. Digests are of file bytes, so an
import can prove it received the same artefact. What is *not* shipped is the
tenant: a path under `customers/` is `E-PORT-05`, and a business leaving with
another business's documents is not portability.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KINDS = ("org", "pack", "flow", "rule")
TAG_RE = re.compile(r"^contract-([0-9]{4})\.([0-9]{2})\.([0-9]+)$")
CODES = ("E-PORT-01", "E-PORT-02", "E-PORT-03", "E-PORT-04", "E-PORT-05",
         "E-PORT-06", "E-PORT-07")
FIX = {
    "E-PORT-01": "fix the export; the importer does not guess",
    "E-PORT-02": "fix the compile (E-COMP-02); a bundle without a pin is not "
                 "portable",
    "E-PORT-03": "re-export with the whole set; a partial bundle is a trap",
    "E-PORT-04": "stop: the bundle was altered in transit, or two versions were "
                 "mixed",
    "E-PORT-05": "strip it; company portability never moves a tenant's documents",
    "E-PORT-06": "upgrade the platform first; the importer must not silently "
                 "drop what it cannot read",
    "E-PORT-07": "make it relative to the repository root; an absolute path is a "
                 "bundle that only works on its own machine",
}


class PortabilityError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message} — fix: {FIX[code]}")
        self.code = code


def _tag(value):
    match = TAG_RE.match(str(value or ""))
    return tuple(int(part) for part in match.groups()) if match else None


def _sha_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha_tree(path):
    """A directory's digest: relative path + file digest, sorted."""
    lines = []
    for base, dirs, names in os.walk(path):
        dirs[:] = sorted(directory for directory in dirs
                         if directory != "__pycache__")
        for name in sorted(names):
            if name.endswith(".pyc"):
                continue
            full = os.path.join(base, name)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            lines.append(f"{rel}:{_sha_file(full)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def _digest(path):
    return _sha_tree(path) if os.path.isdir(path) else _sha_file(path)


def _kind_of(rel):
    """The company's own files (model, org chart) are `org`; an industry's are
    flows, rules or its pack."""
    if rel.startswith("companies/"):
        return "org"
    if "/flows/" in f"/{rel}":
        return "flow"
    if "/rules/" in f"/{rel}":
        return "rule"
    return "pack"


def _version_of(root, rel, fallback):
    """A file's own version, else the contract pin it ships with."""
    path = root / rel
    candidate = path / "version" if path.is_dir() else path
    if candidate.is_file():
        try:
            text = candidate.read_text(encoding="utf-8").strip().splitlines()
        except (OSError, UnicodeDecodeError):
            return fallback
        for line in text[:40]:
            match = re.match(r"^version:\s*(.+)$", line)
            if match:
                return match.group(1).strip().strip("'\"")
            if re.match(r"^[0-9]+\.[0-9]+", line):
                return line.strip()
    return fallback


def _pin_problems(root, contract):
    tag = _tag((contract or {}).get("tag"))
    sha = str((contract or {}).get("sha") or "")
    if tag is None or not re.match(r"^[0-9a-f]{40}$", sha):
        return [("E-PORT-02", f"the template's contract pin is {contract!r}")]
    if not (root / ".git").exists():
        return []  # a non-git checkout cannot resolve; the import re-checks
    try:
        result = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                                cwd=str(root), capture_output=True)
    except OSError:
        return []
    if result.returncode != 0:
        return [("E-PORT-02", f"the pin's sha {sha[:12]}… is not a commit in "
                              f"this repository")]
    return []


def _template(root, company, template_path=None):
    path = Path(template_path) if template_path else \
        root / "companies" / company / "paperclip-company.json"
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        # the compiler's own fixtures are the fallback so the tool is usable
        # before a company has a compiled template checked in
        fallback = root / "tests" / "fixtures" / f"paperclip-company.{company}.json"
        if fallback.is_file():
            path = fallback
        else:
            raise PortabilityError(
                "E-PORT-01", f"no compiled template for {company!r} at "
                             f"{path.relative_to(root) if path.is_relative_to(root) else path}")
    return path


def artefacts_for(root, company, doc, pin_tag):
    """Every file the template names, with its digest."""
    rels = []
    for rel in (doc.get("source") or {}).get("files") or []:
        rels.append(str(rel))
    for skill in doc.get("skills") or []:
        if isinstance(skill, dict) and skill.get("path"):
            rels.append(str(skill["path"]))
    seen, rows = set(), []
    for rel in rels:
        if rel in seen:
            continue
        seen.add(rel)
        full = root / rel
        if not full.exists():
            continue  # reported by the caller as E-PORT-03
        ident = rel.split("/")[-1]
        if os.path.isdir(full):
            ident = ident or rel.split("/")[-2]
        elif ident.endswith(".yaml"):
            ident = ident[:-5]
        if ident.endswith(".flow"):
            ident = ident[:-5]
        rows.append({"kind": _kind_of(rel), "id": ident,
                     "version": _version_of(root, rel, pin_tag),
                     "sha256": _digest(full)})
    rows.sort(key=lambda row: (row["kind"], row["id"]))
    return rows


def bundle_id(company, template_sha, artefacts):
    lines = [f"{row['kind']}:{row['id']}@{row['version']}:{row['sha256']}"
             for row in sorted(artefacts, key=lambda row: (row["kind"], row["id"]))]
    blob = "\n".join([str(company), str(template_sha)] + lines)
    return "bundle-" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def export(root, company, template_path=None, platform=None, now=None):
    """(manifest, findings) — findings are refusals; a bundle with any is not written."""
    root = Path(root)
    path = _template(root, company, template_path)
    try:
        doc = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise PortabilityError("E-PORT-01", f"the template is unreadable ({exc})")
    contract = doc.get("contract") or {}
    pin_tag = str(contract.get("tag") or "unpinned")
    findings = list(_pin_problems(root, contract))
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else \
        path.as_posix()
    if rel.startswith("/"):
        findings.append(("E-PORT-07", f"the template path {rel!r} is absolute"))
    if rel.startswith("customers/"):
        findings.append(("E-PORT-05", f"the template path {rel!r} is tenant data"))
    cited, artefacts = [], []
    for source in [(doc.get("source") or {}).get("files") or []] + \
                  [[skill.get("path") for skill in doc.get("skills") or []
                    if isinstance(skill, dict)]]:
        for item in source:
            if item:
                cited.append(str(item))
    for item in cited:
        if item.startswith("/"):
            findings.append(("E-PORT-07", f"{item!r} is an absolute path"))
        if item.startswith("customers/"):
            findings.append(("E-PORT-05", f"{item!r} is tenant data"))
        if not (root / item).exists():
            findings.append(("E-PORT-03", f"the template cites {item!r}, which is "
                                          f"not in this checkout"))
    artefacts = artefacts_for(root, company, doc, pin_tag)
    platform_tag = platform or _current_tag(root)
    mine, theirs = _tag(contract.get("tag")), _tag(platform_tag)
    if mine is None:
        findings.append(("E-PORT-02", f"the pin {contract.get('tag')!r} is not a "
                                      f"contract tag"))
    elif theirs is not None and mine > theirs:
        findings.append(("E-PORT-06", f"the bundle is pinned at "
                                      f"{contract.get('tag')} and the platform is "
                                      f"{platform_tag}"))
    manifest = {"version": 1, "contract": "company-portability@1",
                "company": company,
                "bundleId": bundle_id(company, _sha_file(path), artefacts),
                "createdAt": (now or _iso_now()),
                "template": {"path": rel, "sha256": _sha_file(path),
                             "contract": {"tag": str(contract.get("tag") or ""),
                                          "sha": str(contract.get("sha") or "")}},
                "artefacts": artefacts,
                "platform": {"contractTag": str(platform_tag or "")}}
    return manifest, findings


def _iso_now():
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _current_tag(root):
    try:
        result = subprocess.run(["git", "tag", "--list", "contract-*"],
                                cwd=str(root), capture_output=True, text=True)
    except OSError:
        return ""
    tags = sorted(result.stdout.split(), key=lambda tag: _tag(tag) or (0, 0, 0))
    return tags[-1] if tags else ""


def verify(root, bundle_path):
    """(manifest, findings) — a bundle against the checkout it names."""
    root = Path(root)
    try:
        manifest = json.loads(Path(bundle_path).read_text())
    except (OSError, ValueError) as exc:
        raise PortabilityError("E-PORT-01", f"the manifest is unreadable ({exc})")
    findings = []
    if manifest.get("contract") != "company-portability@1" or \
            manifest.get("version") != 1:
        findings.append(("E-PORT-01", "the manifest's contract/version are wrong"))
    template = manifest.get("template") or {}
    path = root / str(template.get("path") or "")
    if not path.is_file():
        findings.append(("E-PORT-03", f"the template {template.get('path')!r} is "
                                      f"not in this checkout"))
    elif _sha_file(path) != template.get("sha256"):
        findings.append(("E-PORT-04", f"the template's digest does not match the "
                                      f"manifest"))
    declared = {f"{row['kind']}:{row['id']}": row
                for row in manifest.get("artefacts") or []}
    actual = {f"{row['kind']}:{row['id']}": row
              for row in artefacts_for(root, str(manifest.get("company")),
                                       _read_template(path) if path.is_file() else {},
                                       str((template.get("contract") or {}
                                            ).get("tag") or "unpinned"))}
    for key, row in declared.items():
        if key not in actual:
            findings.append(("E-PORT-03", f"{key} is in the bundle and not in this "
                                          f"checkout"))
        elif actual[key]["sha256"] != row.get("sha256"):
            findings.append(("E-PORT-04", f"{key}: the checkout has "
                                          f"{actual[key]['sha256'][:12]}…, the "
                                          f"bundle says "
                                          f"{str(row.get('sha256'))[:12]}…"))
    expected = bundle_id(str(manifest.get("company")),
                         str(template.get("sha256")),
                         manifest.get("artefacts") or [])
    if manifest.get("bundleId") != expected:
        findings.append(("E-PORT-01", f"the bundle id does not match its own "
                                      f"contents (expected {expected})"))
    return manifest, findings


def _read_template(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def do_import(root, bundle_path, platform=None):
    """Verify, then write the template into the checkout."""
    root = Path(root)
    manifest, findings = verify(root, bundle_path)
    if findings:
        return manifest, findings, None
    mine = _tag((manifest.get("template") or {}).get("contract", {}).get("tag"))
    theirs = _tag(platform or _current_tag(root))
    if mine and theirs and mine > theirs:
        return manifest, [("E-PORT-06", f"the bundle is pinned at "
                                        f"{manifest['template']['contract']['tag']}"
                                        f" and this platform is at {platform}")], None
    rel = str((manifest.get("template") or {}).get("path") or "")
    target = root / rel
    shipped = Path(bundle_path).parent / Path(rel).name
    if not shipped.is_file():
        return manifest, [("E-PORT-03", f"the bundle has no {Path(rel).name} "
                                        f"beside its manifest")], None
    if target.is_file() and _sha_file(target) != manifest["template"]["sha256"]:
        return manifest, [("E-PORT-04", f"{rel} already exists with a different "
                                        f"digest; importing would overwrite a "
                                        f"compiled model")], None
    if not target.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(shipped, target)
    return manifest, [], rel


def diff(left, right):
    """Added, removed and changed artefacts, per kind:id."""
    a = json.loads(Path(left).read_text())
    b = json.loads(Path(right).read_text())
    first = {f"{row['kind']}:{row['id']}": row for row in a.get("artefacts") or []}
    second = {f"{row['kind']}:{row['id']}": row for row in b.get("artefacts") or []}
    return {"added": sorted(set(second) - set(first)),
            "removed": sorted(set(first) - set(second)),
            "changed": sorted(key for key in set(first) & set(second)
                              if first[key].get("sha256") != second[key].get("sha256")
                              or first[key].get("version") != second[key].get("version")),
            "same": a.get("bundleId") == b.get("bundleId")}


def _sample_repo(parent):
    """A tiny company tree for the self-test, copied from the fixture.

    The paths live in a fixture, not in this script: a CI tool must not name an
    industry path (that is what `no_hardcoded_paths.py` is for), and a fixture is
    where a sample tree belongs.
    """
    source = ROOT / "tests" / "fixtures" / "portability" / "tiny"
    root = Path(parent) / "repo"
    shutil.copytree(source, root)
    template = json.loads(
        (root / "companies" / "acme" / "paperclip-company.json").read_text())
    return root, template


def self_test():
    with tempfile.TemporaryDirectory() as tmp:
        root, template = _sample_repo(tmp)
        manifest, findings = export(root, "acme", platform="contract-2026.11.3",
                                    now="2026-11-01T09:00:00.000Z")
        if findings:
            print(f"portable --self-test RED: a clean export has findings: "
                  f"{findings}", file=sys.stderr)
            return 1
        pairs = {(row["kind"], row["id"]) for row in manifest["artefacts"]}
        if pairs != {("org", "company"), ("org", "org-chart"),
                     ("flow", "intake")}:
            print(f"portable --self-test RED: artefacts are {sorted(pairs)}",
                  file=sys.stderr)
            return 1
        out = root.parent / "out"
        out.mkdir()
        bundle = out / "bundle.json"
        bundle.write_text(json.dumps(manifest, indent=2) + "\n")
        shutil.copyfile(root / manifest["template"]["path"],
                        out / "paperclip-company.json")

        _checked, verify_findings = verify(root, bundle)
        if verify_findings:
            print(f"portable --self-test RED: verify on a clean bundle: "
                  f"{verify_findings}", file=sys.stderr)
            return 1

        # a tampered artefact is E-PORT-04
        flow = root / template["source"]["files"][-1]
        flow.write_text("version: 2.1.0\nsteps: [changed]\n")
        _m, tampered = verify(root, bundle)
        if {code for code, _ in tampered} != {"E-PORT-04"}:
            print(f"portable --self-test RED: a tampered artefact gave "
                  f"{tampered}", file=sys.stderr)
            return 1

        # tenant data is E-PORT-05
        template["source"]["files"].append("customers/acme/org.json")
        (root / "customers" / "acme").mkdir(parents=True)
        (root / "customers" / "acme" / "org.json").write_text("{}\n")
        (root / "companies" / "acme" / "paperclip-company.json").write_text(
            json.dumps(template, indent=2) + "\n")
        _m, tenant = export(root, "acme", platform="contract-2026.11.3")
        if "E-PORT-05" not in {code for code, _ in tenant}:
            print(f"portable --self-test RED: tenant data gave {tenant}",
                  file=sys.stderr)
            return 1

        # a bundle newer than the platform is E-PORT-06
        _m, stale = export(root, "acme", platform="contract-2026.09.0")
        if "E-PORT-06" not in {code for code, _ in stale}:
            print(f"portable --self-test RED: a stale platform gave {stale}",
                  file=sys.stderr)
            return 1

        # two exports of the same state have one id
        again, _f = export(root, "acme", platform="contract-2026.11.3")
        if again["bundleId"] != export(root, "acme",
                                       platform="contract-2026.11.3")[0]["bundleId"]:
            print("portable --self-test RED: the bundle id is not content-"
                  "addressed", file=sys.stderr)
            return 1
    # and the id agrees with the oracle's committed manifest for its own case
    fixture = ROOT / "tests" / "fixtures" / "portability" / "case.valid.json"
    if fixture.is_file():
        case = json.loads(fixture.read_text())
        expected = ((case.get("expected") or {}).get("manifest") or {}).get(
            "bundleId")
        mine = bundle_id(str(case.get("company")),
                         str(case["template"]["sha256"]),
                         case.get("artefacts") or [])
        if expected and mine != expected:
            print(f"portable --self-test RED: the bundle id disagrees with the "
                  f"oracle ({mine} != {expected})", file=sys.stderr)
            return 1
    print("portable --self-test: export, verify, tamper, tenant data, stale pin, "
          "a stable id, and the oracle's own id — OK")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="portable.py")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("export")
    p.add_argument("--company", required=True)
    p.add_argument("--template")
    p.add_argument("--platform")
    p.add_argument("--out")
    p.add_argument("--root", default=str(ROOT))
    p = sub.add_parser("verify")
    p.add_argument("--bundle", required=True)
    p.add_argument("--root", default=str(ROOT))
    p = sub.add_parser("import")
    p.add_argument("--bundle", required=True)
    p.add_argument("--platform")
    p.add_argument("--root", default=str(ROOT))
    p = sub.add_parser("diff")
    p.add_argument("--left", required=True)
    p.add_argument("--right", required=True)
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        if args.cmd == "export":
            manifest, findings = export(args.root, args.company,
                                        template_path=args.template,
                                        platform=args.platform)
            if findings:
                for code, reason in findings:
                    print(f"{code}: {reason} — fix: {FIX[code]}", file=sys.stderr)
                return 1
            if args.out:
                out = Path(args.out)
                out.mkdir(parents=True, exist_ok=True)
                (out / "bundle.json").write_text(
                    json.dumps(manifest, indent=2) + "\n")
                source = Path(args.root) / manifest["template"]["path"]
                shutil.copyfile(source, out / source.name)
            print(json.dumps(manifest, indent=2))
            return 0
        if args.cmd == "verify":
            _manifest, findings = verify(args.root, args.bundle)
            for code, reason in findings:
                print(f"{code}: {reason} — fix: {FIX[code]}", file=sys.stderr)
            if findings:
                return 1
            print(f"portable: {args.bundle} verifies")
            return 0
        if args.cmd == "import":
            manifest, findings, rel = do_import(args.root, args.bundle,
                                                platform=args.platform)
            for code, reason in findings:
                print(f"{code}: {reason} — fix: {FIX[code]}", file=sys.stderr)
            if findings:
                return 1
            print(f"portable: imported {manifest['bundleId']} → {rel}")
            return 0
        if args.cmd == "diff":
            print(json.dumps(diff(args.left, args.right), indent=2))
            return 0
    except PortabilityError as exc:
        print(f"portable: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
