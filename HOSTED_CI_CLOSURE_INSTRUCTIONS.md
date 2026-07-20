# Hosted CI closure instructions

1. Create or populate `olegovation-ship-it/v0-integrated-proof-evidence-contract` on branch `gate2-development` with the WP6 package contents.
2. Run **V0 IPEC Gate 2 CI Integration** at the exact integration head commit.
3. Confirm that jobs j07, j08, j09, and j10 all pass.
4. Download or otherwise preserve the workflow evidence artifact and compute its SHA-256.
5. Populate a copy of `evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json` with authentic run, head, job, and artifact data.
6. Run `python scripts/ingest_hosted_ci_evidence.py <evidence.json>`.
7. Run `python scripts/build_wp6_gate2_audit.py`, then `python scripts/verify_wp6_gate2_audit.py` without `--allow-pending`.

Only the final successful verifier authorizes a subsequent Gate 2 closure evidence patch. It still does not itself authorize a public release or DOI publication.
