#!/usr/bin/env python3
"""Build 100 ordered implementation prompts (one per issue #1..100) and put
them on top of the dashboard draft queue for this session so Auto can run
them top-first. Also writes docs/prompts/queue.json for reproducibility.

Usage: python3 scripts/make-queue.py [--apply]   (default --apply; writes
docs/prompts/queue.json always, touches dashboard drafts.json only with --apply)
"""
import json, random, shutil, string, subprocess, sys, time
from pathlib import Path

REPO_GH = "stevennt/abn.os.enterprise"
REPO_DIR = "/Users/thanhson/Workspace/abn.os.enterprise"
SESSION = "ses_e6fd7ed07ffe9bqG2jK5T6rfLH"
DRAFTS = Path("/Users/thanhson/.local/share/opencode/drafts.json")

TRACK_CTX = {
 "A": "nền: README.md, ARCHITECTURE.md, ROADMAP.md, metamodel/*.schema.yaml",
 "B": "nền: examples/bank/org-chart.yaml, metamodel/org.schema.yaml, docs/core/glossary.md",
 "C": "nền: examples/bank/process-catalog.yaml, examples/bank/loan-approval.flow.yaml, metamodel/process.schema.yaml",
 "D": "nền: metamodel/event.schema.yaml, các flow YAML đã có (payload mẫu)",
 "E": "nền: metamodel/rule.schema.yaml, ROADMAP P4, docs/core/glossary.md",
 "F": "nền: ARCHITECTURE.md (phần engine ADR), engine/",
 "G": "nền: engine/workflow-vs-ai-matrix.md, engine/automation-levels.md",
 "H": "nền: docs/core/touchpoint-taxonomy.md, metamodel/touchpoint.schema.yaml",
 "I": "nền: docs/core/simulation-plan.md, engine/automation-levels.md",
 "J": "nền: toàn repo + các flow/pilot đã xong ở prompt trước",
}

def prompt_for(k, n, total, title):
    track = title[0] if title[:1] in TRACK_CTX else "A"
    ctx = TRACK_CTX[track]
    short = title.split("—", 1)[1].strip() if "—" in title else title
    return (
f"[{k}/{total} · issue #{n}] {short} (repo abn.os.enterprise).\n"
f"Làm việc tại {REPO_DIR}, nhánh DEV (git pull trước).\n"
f"1) Đọc đề: gh issue view {n} --repo {REPO_GH} --json title,body. Làm đúng Acceptance criteria trong body; file {ctx}.\n"
f"2) Đọc nhanh file liên quan (prompt trước có thể đã đổi) rồi mới sửa; giữ schema/YAML hợp lệ.\n"
f"3) Kiểm tra: yamllint file YAML đổi, không vỡ file khác.\n"
f"4) Commit + push nhánh DEV (message: 'Issue #{n}: ...'), rồi đóng issue: gh issue close {n} --repo {REPO_GH} --comment 'Done: <file đổi + cách kiểm chứng>'.\n"
f"Chỉ làm đúng 1 issue này. Vướng thì comment vướng vào issue rồi dừng, không đoán bừa."
    )

def main():
    apply = "--apply" in sys.argv
    out = subprocess.run(["gh", "issue", "list", "--repo", REPO_GH, "--limit", "200",
                          "--json", "number,title"], capture_output=True, text=True, check=True).stdout
    issues = sorted(json.loads(out), key=lambda x: x["number"])
    total = len(issues)
    prompts = [prompt_for(k, it["number"], total, it["title"]) for k, it in enumerate(issues, 1)]
    qpath = Path(REPO_DIR) / "docs" / "core" / "prompts" / "queue.json"
    qpath.parent.mkdir(parents=True, exist_ok=True)
    qpath.write_text(json.dumps(
        [{"order": k, "issue": it["number"], "title": it["title"], "prompt": p}
         for k, (it, p) in enumerate(zip(issues, prompts), 1)],
        ensure_ascii=False, indent=1))
    print(f"queue.json: {total} prompts -> {qpath}")
    if not apply:
        return
    bak = DRAFTS.with_suffix(f".json.bak-queue-{time.strftime('%Y%m%d-%H%M%S')}")
    shutil.copy2(DRAFTS, bak)
    store = json.loads(DRAFTS.read_text())
    entry = store.get(SESSION, {"drafts": [], "sent": [], "deleted": {}})
    old = entry.get("drafts", [])
    oldmax = max([d.get("created", 0) for d in old] + [0])
    base = max(int(time.time() * 1000), oldmax)
    rnd = lambda: "".join(random.choices(string.ascii_lowercase + string.digits, k=9))
    # drafts[0] runs first -> issue #1 needs the LARGEST created (merge sorts desc)
    new = [{"id": f"{base + (total - k) * 1000}-{rnd()}",
            "text": p, "created": base + (total - k) * 1000}
           for k, p in enumerate(prompts, 1)]
    # Tombstone stale already-sent drafts (the 2 original user messages) so
    # Auto never re-fires them after the 100 drain.
    deleted = dict(entry.get("deleted", {}))
    for d in old:
        deleted[d["id"]] = base
    entry.update({"drafts": new, "sent": entry.get("sent", []),
                  "deleted": deleted, "updatedAt": base})
    store[SESSION] = entry
    DRAFTS.write_text(json.dumps(store, ensure_ascii=False))
    print(f"drafts.json: {len(new)} prompts now on top of {SESSION}; "
          f"{len(old)} stale drafts tombstoned (never re-fire). backup {bak}")

if __name__ == "__main__":
    main()
