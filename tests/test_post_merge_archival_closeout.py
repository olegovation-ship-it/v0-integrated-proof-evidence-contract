from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
MERGE = "820947103d24153e00b215ced53ee8b33ef0c7bf"
CLOSURE = "fad1d22152c68f82048b2f462b61660f4fe5b38e"

def load(rel):
    return json.loads((ROOT / rel).read_text())

def test_fixed_merge_baseline():
    x = load("release/v0.1/POST_MERGE_ARCHIVAL_CLOSEOUT_RECORD.json")
    assert x["merged_pr"] == 1
    assert x["closure_commit"] == CLOSURE
    assert x["merge_commit"] == MERGE
    assert x["gate2_closure_preserved"] is True
    assert x["gate2_acceptance_gates"]["pass"] == 20
    assert x["gate2_acceptance_gates"]["pending"] == 0

def test_observed_post_merge_ci_is_exact_head():
    x = load("evidence/POST_MERGE_HOSTED_CI_EVIDENCE.json")
    assert x["workflow_run_number"] == 9
    assert x["head_branch"] == "main"
    assert x["head_sha"] == MERGE
    assert x["event"] == "push"
    assert x["conclusion"] == "success"

def test_mandatory_jobs_are_named():
    x = load("evidence/POST_MERGE_HOSTED_CI_EVIDENCE.json")
    assert x["mandatory_jobs"]["07"]["name"] == "07 Upstream Validator replay"
    assert x["mandatory_jobs"]["08"]["name"] == "08 Upstream OSAP Python replay"
    assert x["mandatory_jobs"]["09"]["name"] == "09 Upstream OSAP Lean replay"
    assert x["mandatory_jobs"]["10"]["name"] == "10 Upstream OSAP Coq replay"

def test_no_release_action_is_authorized():
    x = load("release/v0.1/POST_MERGE_ARCHIVAL_CLOSEOUT_RECORD.json")
    assert not any(x["release_actions"].values())
    assert x["frozen_upstreams_modified"] is False
    assert x["paper_b_baseline_modified"] is False

def test_branch_sync_is_fast_forward_only():
    x = load("release/v0.1/DEVELOPMENT_BRANCH_SYNCHRONIZATION_RECORD.json")
    assert x["sync_mode"] == "FAST_FORWARD_ONLY"
    assert x["history_rewrite_authorized"] is False
    assert x["baseline_merge_commit"] == MERGE

def test_patch_sha256_ledger():
    for line in (ROOT / "SHA256SUMS.txt").read_text().splitlines():
        if not line.strip():
            continue
        expected, rel = line.split("  ", 1)
        path = ROOT / rel
        assert path.is_file(), rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, rel
