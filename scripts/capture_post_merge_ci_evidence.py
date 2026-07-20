#!/usr/bin/env python3
"""Capture the exact successful post-merge GitHub Actions run without fabricating identifiers."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "POST_MERGE_HOSTED_CI_EVIDENCE.json"
REPO = "olegovation-ship-it/v0-integrated-proof-evidence-contract"
WORKFLOW = "gate2-integration.yml"
WORKFLOW_NAME = "V0 IPEC Gate 2 CI Integration"
MERGE_SHA = "820947103d24153e00b215ced53ee8b33ef0c7bf"
RUN_NUMBER = 9

MANDATORY = {
    "07": "07 Upstream Validator replay",
    "08": "08 Upstream OSAP Python replay",
    "09": "09 Upstream OSAP Lean replay",
    "10": "10 Upstream OSAP Coq replay",
}

def run_json(args: list[str]) -> Any:
    try:
        completed = subprocess.run(args, check=True, text=True, capture_output=True)
    except FileNotFoundError as exc:
        raise SystemExit("ERROR: GitHub CLI `gh` is not installed.") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "ERROR: GitHub CLI request failed. Run `gh auth status` and retry.\n"
            + exc.stderr
        ) from exc
    return json.loads(completed.stdout)

def canonical_sha(payload: dict[str, Any]) -> str:
    copy = dict(payload)
    copy["canonical_sha256"] = None
    raw = json.dumps(copy, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    runs = run_json([
        "gh", "run", "list",
        "--repo", REPO,
        "--workflow", WORKFLOW,
        "--branch", "main",
        "--commit", MERGE_SHA,
        "--event", "push",
        "--limit", "20",
        "--json",
        "databaseId,number,displayTitle,headSha,headBranch,event,status,conclusion,workflowName,url,createdAt,updatedAt",
    ])

    matches = [
        item for item in runs
        if item.get("headSha") == MERGE_SHA
        and item.get("headBranch") == "main"
        and item.get("event") == "push"
        and item.get("conclusion") == "success"
        and item.get("workflowName") == WORKFLOW_NAME
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"ERROR: expected exactly one successful exact-head run, found {len(matches)}."
        )

    selected = matches[0]
    if selected.get("number") != RUN_NUMBER:
        raise SystemExit(
            f"ERROR: expected workflow run number {RUN_NUMBER}, got {selected.get('number')}."
        )

    run_id = selected.get("databaseId")
    details = run_json([
        "gh", "run", "view", str(run_id),
        "--repo", REPO,
        "--json", "jobs",
    ])
    jobs = details.get("jobs", [])
    normalized_jobs = []
    for job in jobs:
        normalized_jobs.append({
            "name": job.get("name"),
            "job_id": job.get("databaseId"),
            "status": job.get("status"),
            "conclusion": job.get("conclusion"),
            "started_at": job.get("startedAt"),
            "completed_at": job.get("completedAt"),
            "url": job.get("url"),
        })

    mandatory = {}
    by_name = {item["name"]: item for item in normalized_jobs}
    for key, name in MANDATORY.items():
        job = by_name.get(name)
        if not job or job.get("conclusion") != "success":
            raise SystemExit(f"ERROR: mandatory job not successful: {name}")
        mandatory[key] = {
            "name": name,
            "job_id": job.get("job_id"),
            "conclusion": "success",
            "url": job.get("url"),
        }

    payload = {
        "artifact_id": "V0_IPEC_POST_MERGE_HOSTED_CI_EVIDENCE",
        "contract_id": "V0-IPEC-0.1",
        "version": "0.1",
        "date": "2026-07-20",
        "repository": REPO,
        "workflow": WORKFLOW_NAME,
        "workflow_file": WORKFLOW,
        "workflow_run_number": selected.get("number"),
        "workflow_run_id": run_id,
        "workflow_run_url": selected.get("url"),
        "head_branch": selected.get("headBranch"),
        "head_sha": selected.get("headSha"),
        "event": selected.get("event"),
        "status": selected.get("status"),
        "conclusion": selected.get("conclusion"),
        "evidence_state": "AUTHENTIC_GITHUB_API_EVIDENCE_RECORDED",
        "observation_source": "GITHUB_CLI_API",
        "observation_time_utc": selected.get("updatedAt"),
        "created_at": selected.get("createdAt"),
        "updated_at": selected.get("updatedAt"),
        "jobs": normalized_jobs,
        "mandatory_jobs": mandatory,
        "canonical_sha256": None,
    }
    payload["canonical_sha256"] = canonical_sha(payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "status": "PASS",
        "run_id": run_id,
        "run_number": payload["workflow_run_number"],
        "head_sha": payload["head_sha"],
        "mandatory_jobs": len(mandatory),
        "output": str(args.output),
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
