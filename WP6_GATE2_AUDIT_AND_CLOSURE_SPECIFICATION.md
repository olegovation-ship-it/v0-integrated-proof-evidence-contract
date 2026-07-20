# WP6 Gate 2 Audit and Closure Specification

## Purpose

WP6 performs the final Gate 2 conformance audit over the frozen WP0–WP5 integration chain. It evaluates twenty acceptance gates covering upstream identity, theorem ownership, interchange schemas, rule bindings, typed outcomes, negative controls, evidence lineage, deterministic replay, and CI governance.

## Closure rule

Gate 2 closes only when all twenty gates are `PASS`. Nineteen gates are reproducible from this standalone package. Gate `G2-20` requires authentic GitHub Actions evidence showing green execution of the exact frozen Validator replay, OSAP Python replay, OSAP Lean 4 replay, and OSAP Coq replay jobs.

A workflow definition is not execution evidence. Run IDs, URLs, head SHAs, job IDs, and artifact hashes must not be invented. Therefore the initial standalone WP6 decision is `HOLD_FOR_HOSTED_CI`, not `CLOSE_GATE2`.

## Evidence intake

`evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json` is the only mutable intake surface. After an actual hosted run, replace the pending fields with authentic evidence using `scripts/ingest_hosted_ci_evidence.py`, rebuild the audit, and rerun the verifier without `--allow-pending`.

## Immutability

WP6 does not alter V0 Validator Core v0.12, V0 OSAP v1.3.0, their tags, exact source commits, archives, DOI metadata, or the submitted Paper B baseline. It creates no tag, GitHub Release, Zenodo record, or DOI mutation.
