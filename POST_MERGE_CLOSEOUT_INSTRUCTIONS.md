# Post-merge archival closeout instructions

## A. Baseline synchronization before applying the overlay

From a clean repository:

```bash
git fetch origin --prune
git switch gate2-development
git merge --ff-only origin/main
git push origin gate2-development
git switch main
```

The baseline `origin/main` must contain `820947103d24153e00b215ced53ee8b33ef0c7bf`.

## B. Apply the overlay

Copy this package directory into the repository root:

```bash
cp -a /path/to/V0_Integrated_Proof_Evidence_Contract_v0.1_Post_Merge_Archival_Closeout_and_Development_Branch_Synchronization_Patch_v0.1/. /workspaces/v0-integrated-proof-evidence-contract/
cd /workspaces/v0-integrated-proof-evidence-contract
git switch gate2-development
```

Do not copy the outer directory as a nested repository folder.

## C. Capture authentic hosted-CI evidence

```bash
python scripts/capture_post_merge_ci_evidence.py
```

The script queries GitHub using `gh`, selects workflow `gate2-integration.yml`, branch `main`, event `push`, and exact commit `820947103d24153e00b215ced53ee8b33ef0c7bf`. It refuses to invent a run ID.

## D. Build and verify

```bash
python scripts/build_post_merge_archival_closeout.py
python scripts/verify_post_merge_archival_closeout.py
pytest -q tests/test_post_merge_archival_closeout.py
python scripts/verify_sha256s.py
git diff --check
```

Expected strict result:

```text
status=PASS
decision=POST_MERGE_CLOSEOUT_READY_FOR_PR
post_merge_ci=PASS
branch_relation=BASELINE_MAIN_CONTAINED
release_actions_authorized=False
```

## E. Commit and pull request

Suggested commit:

```bash
git add .
git commit -m "Add V0-IPEC post-merge archival closeout"
git push origin gate2-development
```

Suggested PR title:

```text
V0-IPEC v0.1: post-merge archival closeout and development-branch synchronization
```

Use a normal merge commit.

## F. Final synchronization after the closeout PR is merged

```bash
git fetch origin --prune
bash scripts/synchronize_gate2_development.sh final
```

The script requires a clean tree and uses `git merge --ff-only`; it will not force-update or rewrite history.

After the final ref equality check, the branch may be preserved as an archival development ref or deleted manually. No automatic deletion is performed.
