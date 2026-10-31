#!/usr/bin/env python3
"""Create loop-4 issues (multi-industry restructure + L2-content import). Idempotent."""
import json
import subprocess

REPO = "stevennt/abn.os.enterprise"

ISSUES = [
("L4-01 — Industry manifest schema + registry",
 "type:metamodel",
 "Define industries/<id>/industry.yaml (id, label, tier, jurisdiction, owner, rule packs, flows, pack ref, tag stream) + JSON schema + validator check. This is the contract that makes the repo multi-industry.",
 "Without a manifest, 'multi-industry' is just folders. Tier field is required (see L4-12).",
 ["industries/*/industry.yaml required fields enforced", "poison fixture (missing tier) goes red", "validator prints industry inventory"]),

("L4-02 — Restructure: move banking content into industries/banking/",
 "type:metamodel",
 "git mv org/, rules/, events/, examples/bank/*.flow.yaml+trace, ai/, evals/<industry>, templates/ into industries/banking/. Shared stays top-level: metamodel/, scripts/, engine/, sim/, frappe/, db/, sql/, tests/, docs/core/.",
 "Banking is the reference implementation; it must become the first industry folder without breaking a single check.",
 ["git mv only (history preserved)", "validator + every CI script still green", "no content edits beyond path fields"]),

("L4-03 — Split docs: docs/core vs industries/<id>/docs",
 "type:metamodel",
 "Shared docs (metamodel, gates, engine, glossary, security) stay in docs/core/; banking-specific (sod? no — sod is core; pilot-*, cost-loan, rollout-*, fraud drills) move to industries/banking/docs/.",
 "65 docs today with no ownership boundary; that is how shared knowledge rots into one industry's assumptions.",
 ["each doc assigned exactly one home", "README map + link check updated", "no cross-industry links"]),

("L4-04 — Per-industry release tags + bin/tag-industry",
 "type:engine",
 "Tags become per industry: <industry>-policy-YYYY.MM.N (rules/processes) and <industry>-pack-YYYY.MM.N (agent content). Script creates both annotations; CI verifies referenced tags exist.",
 "One global tag cannot express 'legal at v3, banking at v7'.",
 ["bin/tag-industry <id> --kind policy|pack", "CI check: every pack ref resolves to a pushed tag", "docs/core/release.md explains the scheme"]),

("L4-05 — Pack schema: adopt OpenGate's agent contract here",
 "type:metamodel",
 "Define metamodel/pack.schema.yaml mirroring OpenGate roles.yaml + SKILL.md frontmatter (position maker/checker, template, skills_required, tools_allow, may_invoke, rubric, temperature, steps). We own the contract; OpenGate consumes it.",
 "L2-content is moving in, so its schema must be defined where the content lives - otherwise OpenGate keeps the master.",
 ["schema covers every field resolver.py reads", "banking pack validates against it", "field-by-field mapping table in docs"]),

("L4-06 — Import banking pack content (L2-content)",
 "type:touchpoint",
 "Move domains/banking/{agents,skills,roles.yaml,rules.md} from abn.platform.opengate into industries/banking/pack/. Citations to enterprise become same-repo relative refs (rules/aml-pack.yaml#AML-SCREEN-02@version).",
 "Single source: prose and rule live in one repo, one PR, one tag. Removes the semantic-drift class that cite-check cannot catch.",
 ["pack files present and validated", "no absolute abn.os.enterprise@tag self-refs remain", "OpenGate copy marked deprecated in its MIGRATION.md"]),

("L4-07 — Retire cite-only machinery, add same-repo consistency check",
 "type:engine",
 "With content co-located, docs/enterprise-pins.yaml shrinks to a bundle pin. Replace per-rule cite check with a check that pack skill prose cites existing rule ids at existing versions in the same repo.",
 "Cite-check verified strings, never semantics. Co-location makes the weaker check unnecessary.",
 ["checker resolves pack cites against industries/<id>/rules/", "stale-version fixture goes red", "docs explain why the old check was retired"]),

("L4-08 — Bundle build: bin/build-pack produces a signed pinned bundle",
 "type:engine",
 "Build industries/<id>/pack into dist/<id>-pack-<ver>.tar.gz + MANIFEST.sha256, deterministic (sorted entries, fixed mtime), so OpenGate can fetch and verify byte-identical content.",
 "OpenGate should consume a bundle, not a git checkout of someone else's repo.",
 ["deterministic rebuild (same sha twice)", "manifest lists every file", "bundle excludes secrets/large binaries"]),

("L4-09 — Scaffold industries/legal/ (second industry, proves the shape)",
 "type:metamodel",
 "Create industries/legal/: industry.yaml (tier commercial, jurisdiction VN), org skeleton, 2 structural rule packs (citation integrity, no-conclusion-without-human) marked authority: pending-legal-review, 1 flow (charge determination review).",
 "One industry proves nothing; the second proves the contract.",
 ["manifest validates", "rule packs carry pending-review authority (no invented thresholds)", "flow validates + trace verifies"]),

("L4-10 — Legal pack content moved in (draft status)",
 "type:touchpoint",
 "Port domains/legal agent/skill structure into industries/legal/pack/, every business claim either cited to a same-repo rule pack or marked placeholder pending legal review. No fabricated law.",
 "Legal is the largest existing pack (70 files) and the honesty test: structure moves, unverified claims do not get promoted by accident.",
 ["pack validates against pack.schema", "zero uncited numeric/legal claims (scanner)", "placeholders explicitly listed in docs"]),

("L4-11 — Cross-industry consistency CI",
 "type:engine",
 "One check across all industries: manifests complete, provider/rule/flow ids globally unique, no cross-industry references, every industry declares tier, every pack resolves.",
 "Multi-industry fails at the seams: duplicate ids and accidental cross-reads.",
 ["checker green on banking+legal", "duplicate-id fixture red", "runs in CI"]),

("L4-12 — Confidentiality tiers + repo-split rule",
 "type:grc",
 "Define tiers (public/commercial/restricted/classified) per industry. Rule: this repo hosts public+commercial; restricted/classified industries live in their own repo, reusing metamodel/ at a pinned tag. Encode in docs + manifest check + CI.",
 "Putting defense-ops next to banking in one git history is a classification incident waiting to happen.",
 ["docs/core/confidentiality.md with the rule", "manifest tier enforced (L4-01)", "explicit path for a classified industry repo"]),

("L4-13 — Tooling path independence (no more hardcoded examples/bank)",
 "type:engine",
 "Refactor validate.py, run_all_traces.py, export_bpmn.py, eval_harness.py, risk_pack.py, promo_pack.py, pii_scan.py to iterate industries/* instead of examples/bank/*.",
 "Every script currently assumes one industry; that silently blocks industry #3.",
 ["zero paths containing examples/bank in scripts/", "all scripts green with 2 industries", "new industry picked up automatically"]),

("L4-14 — OpenGate: resolver --pack-root + bundle fetch/verify",
 "type:engine",
 "In abn.platform.opengate: add --pack-root / bundle map to gateway/resolve.py, fetch dist bundles into .opengate/bundles/<id>@<ver>/, verify MANIFEST.sha256 before use.",
 "Consuming bundles is the actual integration; citations were a stopgap.",
 ["resolve --validate-pack banking --pack-root <dir> green", "tampered bundle refused", "no behavior change when pack absent"]),

("L4-15 — OpenGate: retire domains/banking, customers become bundle pointers",
 "type:engine",
 "Delete domains/banking/ after L4-14 lands; customers/<id>/{profile,org} reference the pinned bundle + local portal roles only.",
 "Two copies of the same pack is the failure mode this whole loop removes.",
 ["domains/banking removed", "customer overlay = pointer + portal roles", "sync gate green"]),

("L4-16 — Industry onboarding playbook",
 "type:metamodel",
 "docs/core/onboarding-industry.md: from zero to a validated industry in one day (manifest, org, 1 rule pack, 1 flow, pack skeleton, tier, tags, bundle).",
 "Growth will be by copy-paste; make the copy-paste correct.",
 ["playbook produces a green industry from scratch (dry-run documented)", "checklist matches CI checks exactly"]),

("L4-17 — Multi-industry narrative + scorecard/cost generalization",
 "type:data",
 "README/ARCHITECTURE/ROADMAP rewritten around industries; scorecard + cost model get per-industry dimension instead of banking-only docs.",
 "The repo's front page still reads as a bank project; that misleads every new reader and every reviewer.",
 ["no banking-only claims on the front page", "scorecard/cost templates per industry", "link check green"]),

("L4-18 — Pack-to-rule drift test (semantic, not string)",
 "type:ai",
 "Test that each pack skill's cited thresholds match the rule pack values, by parsing both and comparing numbers - the check citation alone could not do.",
 "This is the bug class that motivated moving content in; prove it is now caught.",
 ["parse pack prose numbers, compare to rule table values", "deliberate drift fixture goes red", "runs in CI"]),
]

def main():
    raw = subprocess.run(["gh", "issue", "list", "--repo", REPO, "--state", "all",
                          "--limit", "400", "--json", "title"],
                         capture_output=True, text=True, check=True).stdout
    have = {x["title"] for x in json.loads(raw)}
    created = skipped = failed = 0
    for title, label, goal, ctx, acc in ISSUES:
        if title in have:
            skipped += 1
            continue
        body = (f"## Goal\n{goal}\n\n## Context\n{ctx} "
                "Loop 4: repo becomes multi-industry; L2-content (agent pack) moves in from OpenGate.\n\n"
                "## Acceptance criteria\n" + "\n".join(f"- [ ] {a}" for a in acc))
        r = subprocess.run(["gh", "issue", "create", "--repo", REPO, "--title", title,
                            "--label", f"loop:4,{label}", "--body", body],
                           capture_output=True, text=True)
        if r.returncode == 0:
            created += 1
            print("created:", title)
        else:
            failed += 1
            print("FAILED:", title, r.stderr[:160])
    print(f"done: created={created} skipped={skipped} failed={failed} total={len(ISSUES)}")

if __name__ == "__main__":
    main()
