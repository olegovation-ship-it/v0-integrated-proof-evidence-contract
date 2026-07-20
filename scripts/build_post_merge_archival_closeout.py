#!/usr/bin/env python3
"""Build post-merge closeout and branch-synchronization records."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MERGE_SHA = "820947103d24153e00b215ced53ee8b33ef0c7bf"
CLOSURE_SHA = "fad1d22152c68f82048b2f462b61660f4fe5b38e"
REPO = "olegovation-ship-it/v0-integrated-proof-evidence-contract"

EVIDENCE = ROOT / "evidence" / "POST_MERGE_HOSTED_CI_EVIDENCE.json"
CLOSEOUT = ROOT / "release" / "v0.1" / "POST_MERGE_ARCHIVAL_CLOSEOUT_RECORD.json"
SYNC = ROOT / "release" / "v0.1" / "DEVELOPMENT_BRANCH_SYNCHRONIZATION_RECORD.json"
LEDGER = ROOT / "SHA256SUMS.txt"

PATCH_FILES = [
    ".github/workflows/post-merge-archival-closeout.yml",
    "POST_MERGE_CLOSEOUT_INSTRUCTIONS.md",
    "PRE_FLIGHT.txt",
    "README.md",
    "STATUS_AND_NONCLAIMS.md",
    "V0_Integrated_Proof_Evidence_Contract_v0.1_Post_Merge_Archival_Closeout_and_Development_Branch_Synchronization_Patch_v0.1.md",
    "evidence/POST_MERGE_HOSTED_CI_EVIDENCE.json",
    "release/v0.1/DEVELOPMENT_BRANCH_SYNCHRONIZATION_RECORD.json",
    "release/v0.1/POST_MERGE_ARCHIVAL_CLOSEOUT_RECORD.json",
    "schemas/v0.1/development_branch_synchronization_record.schema.json",
    "schemas/v0.1/post_merge_archival_closeout_record.schema.json",
    "schemas/v0.1/post_merge_hosted_ci_evidence.schema.json",
    "scripts/build_post_merge_archival_closeout.py",
    "scripts/capture_post_merge_ci_evidence.py",
    "scripts/synchronize_gate2_development.sh",
    "scripts/verify_post_merge_archival_closeout.py",
    "tests/test_post_merge_archival_closeout.py",
]

def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())

def git(*args: str, allow_missing: bool = False) -> str | None:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True
    )
    if completed.returncode:
        if allow_missing:
            return None
        raise SystemExit(
            "ERROR: git command failed: git "
            + " ".join(args)
            + "\n"
            + completed.stderr
        )
    return completed.stdout.strip()

def is_ancestor(older: str, newer: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=ROOT,
        capture_output=True,
    ).returncode == 0

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def update_ledger() -> None:
    entries: dict[str, str] = {}
    order: list[str] = []
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            if not line.strip():
                continue
            digest, rel = line.split("  ", 1)
            entries[rel] = digest
            order.append(rel)
    for rel in PATCH_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise SystemExit(f"ERROR: patch file missing: {rel}")
        entries[rel] = sha256(path)
        if rel not in order:
            order.append(rel)
    LEDGER.write_text("\n".join(f"{entries[rel]}  {rel}" for rel in order) + "\n")

def main() -> int:
    evidence = load(EVIDENCE)
    authenticated = (
        evidence.get("evidence_state") == "AUTHENTIC_GITHUB_API_EVIDENCE_RECORDED"
        and isinstance(evidence.get("workflow_run_id"), int)
        and evidence.get("head_sha") == MERGE_SHA
        and evidence.get("conclusion") == "success"
    )

    head = git("rev-parse", "HEAD")
    origin_main = git("rev-parse", "refs/remotes/origin/main", allow_missing=True)
    origin_dev = git(
        "rev-parse", "refs/remotes/origin/gate2-development", allow_missing=True
    )
    current_branch = git("branch", "--show-current")

    if not is_ancestor(MERGE_SHA, head):
        raise SystemExit("ERROR: current HEAD does not contain the Gate 2 merge commit.")
    if origin_main and not is_ancestor(MERGE_SHA, origin_main):
        raise SystemExit("ERROR: origin/main does not contain the Gate 2 merge commit.")

    if not origin_dev or not origin_main:
        relation = "PENDING_REF_CAPTURE"
    elif origin_dev == origin_main:
        relation = "SYNCHRONIZED_TO_CURRENT_MAIN"
    elif is_ancestor(origin_dev, origin_main):
        relation = "FAST_FORWARD_AVAILABLE"
    elif is_ancestor(MERGE_SHA, origin_dev):
        relation = "BASELINE_MAIN_CONTAINED"
    else:
        relation = "DIVERGED"

    if relation == "DIVERGED":
        raise SystemExit("ERROR: development branch diverged; force updates are prohibited.")

    post_merge_ci = (
        "PASS_AUTHENTICATED" if authenticated else "PASS_OBSERVED_ID_PENDING"
    )
    status = (
        "POST_MERGE_CLOSEOUT_READY_FOR_PR"
        if authenticated and relation != "PENDING_REF_CAPTURE"
        else "READY_FOR_APPLICATION"
    )
    decision = (
        "OPEN_CLOSEOUT_PR"
        if status == "POST_MERGE_CLOSEOUT_READY_FOR_PR"
        else "CAPTURE_AUTHENTIC_CI_AND_SYNCHRONIZE_DEVELOPMENT_BRANCH"
    )

    closeout = {
        "artifact_id": "V0_IPEC_POST_MERGE_ARCHIVAL_CLOSEOUT_RECORD",
        "contract_id": "V0-IPEC-0.1",
        "version": "0.1",
        "date": "2026-07-20",
        "repository": REPO,
        "merged_pr": 1,
        "pre_merge_main": "d251a60e2472eb75373b0f2a42a95ae522e71181",
        "closure_commit": CLOSURE_SHA,
        "merge_commit": MERGE_SHA,
        "merged_at": "2026-07-20T10:53:30Z",
        "gate2_closure_preserved": True,
        "gate2_acceptance_gates": {"pass": 20, "total": 20, "pending": 0, "fail": 0},
        "post_merge_ci": post_merge_ci,
        "post_merge_ci_run_id": evidence.get("workflow_run_id"),
        "post_merge_ci_run_number": evidence.get("workflow_run_number"),
        "branch_relation": relation,
        "observed_head": head,
        "observed_branch": current_branch,
        "observed_origin_main": origin_main,
        "observed_origin_gate2_development": origin_dev,
        "status": status,
        "decision": decision,
        "frozen_upstreams_modified": False,
        "paper_b_baseline_modified": False,
        "release_actions": {
            "tag": False,
            "github_release": False,
            "zenodo": False,
            "doi": False,
        },
    }
    CLOSEOUT.write_text(json.dumps(closeout, indent=2) + "\n")

    sync = {
        "artifact_id": "V0_IPEC_DEVELOPMENT_BRANCH_SYNCHRONIZATION_RECORD",
        "contract_id": "V0-IPEC-0.1",
        "version": "0.1",
        "date": "2026-07-20",
        "repository": REPO,
        "development_branch": "gate2-development",
        "main_branch": "main",
        "sync_mode": "FAST_FORWARD_ONLY",
        "baseline_merge_commit": MERGE_SHA,
        "pre_sync_development_tip": CLOSURE_SHA,
        "observed_main_tip": origin_main,
        "current_development_tip": origin_dev,
        "current_main_tip": origin_main,
        "relation": relation,
        "status": (
            "SYNCHRONIZED_TO_CURRENT_MAIN"
            if relation == "SYNCHRONIZED_TO_CURRENT_MAIN"
            else "FINAL_FAST_FORWARD_REQUIRED"
        ),
        "history_rewrite_authorized": False,
        "branch_deletion_authorized": relation == "SYNCHRONIZED_TO_CURRENT_MAIN",
        "final_sync_required_after_closeout_merge": True,
    }
    SYNC.write_text(json.dumps(sync, indent=2) + "\n")

    update_ledger()
    print(json.dumps({
        "status": status,
        "decision": decision,
        "post_merge_ci": post_merge_ci,
        "branch_relation": relation,
        "release_actions_authorized": False,
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
