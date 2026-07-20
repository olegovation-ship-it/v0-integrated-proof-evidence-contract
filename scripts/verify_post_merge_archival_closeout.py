#!/usr/bin/env python3
"""Verify the V0-IPEC post-merge archival closeout patch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGE_SHA = "820947103d24153e00b215ced53ee8b33ef0c7bf"
CLOSURE_SHA = "fad1d22152c68f82048b2f462b61660f4fe5b38e"
REPO = "olegovation-ship-it/v0-integrated-proof-evidence-contract"

def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text())

def verify_ledger() -> None:
    ledger = ROOT / "SHA256SUMS.txt"
    if not ledger.exists():
        raise AssertionError("SHA256SUMS.txt is missing")
    for line in ledger.read_text().splitlines():
        if not line.strip():
            continue
        expected, rel = line.split("  ", 1)
        path = ROOT / rel
        if not path.is_file():
            raise AssertionError(f"ledger file missing: {rel}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise AssertionError(f"SHA-256 mismatch: {rel}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-api-id-pending", action="store_true")
    args = parser.parse_args()

    evidence = load("evidence/POST_MERGE_HOSTED_CI_EVIDENCE.json")
    closeout = load("release/v0.1/POST_MERGE_ARCHIVAL_CLOSEOUT_RECORD.json")
    sync = load("release/v0.1/DEVELOPMENT_BRANCH_SYNCHRONIZATION_RECORD.json")

    assert evidence["repository"] == REPO
    assert evidence["workflow_run_number"] == 9
    assert evidence["head_branch"] == "main"
    assert evidence["head_sha"] == MERGE_SHA
    assert evidence["event"] == "push"
    assert evidence["conclusion"] == "success"

    authenticated = evidence["evidence_state"] == "AUTHENTIC_GITHUB_API_EVIDENCE_RECORDED"
    if not args.allow_api_id_pending:
        assert authenticated
        assert isinstance(evidence["workflow_run_id"], int)
        assert evidence["workflow_run_url"]
        assert len(evidence["jobs"]) >= 12
        for key in ["07", "08", "09", "10"]:
            job = evidence["mandatory_jobs"][key]
            assert isinstance(job["job_id"], int)
            assert job["conclusion"] == "success"

    assert closeout["merged_pr"] == 1
    assert closeout["closure_commit"] == CLOSURE_SHA
    assert closeout["merge_commit"] == MERGE_SHA
    assert closeout["gate2_closure_preserved"] is True
    assert closeout["gate2_acceptance_gates"] == {
        "pass": 20, "total": 20, "pending": 0, "fail": 0
    }
    assert closeout["frozen_upstreams_modified"] is False
    assert closeout["paper_b_baseline_modified"] is False
    assert not any(closeout["release_actions"].values())
    assert closeout["branch_relation"] != "DIVERGED"

    assert sync["sync_mode"] == "FAST_FORWARD_ONLY"
    assert sync["baseline_merge_commit"] == MERGE_SHA
    assert sync["history_rewrite_authorized"] is False

    verify_ledger()

    print(json.dumps({
        "status": "PASS",
        "decision": closeout["decision"],
        "post_merge_ci": closeout["post_merge_ci"],
        "branch_relation": closeout["branch_relation"],
        "gate2_closure_preserved": True,
        "release_actions_authorized": False,
        "api_id_pending_allowed": args.allow_api_id_pending,
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
