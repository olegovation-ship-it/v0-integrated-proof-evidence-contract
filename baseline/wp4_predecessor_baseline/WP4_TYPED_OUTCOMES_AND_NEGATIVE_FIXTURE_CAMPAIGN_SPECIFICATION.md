# WP4 Typed Outcomes and Negative Fixture Campaign Specification

## Scope

WP4 consumes the frozen WP3 theorem-rule crosswalk and adapter boundary. It binds exactly eight public certification outcomes, defines deterministic precedence, classifies all 36 theorem-backed rules and all 11 procedural diagnostics, and executes 24 deliberately defective integration fixtures.

## Typed outcomes

1. `CERTIFIED`
2. `REJECTED_GUARD_FAILURE`
3. `REJECTED_DLE_FAILURE`
4. `REJECTED_LIVE_RESIDUAL`
5. `REJECTED_NONELIM_OBSTRUCTION`
6. `REJECTED_BRANCH_PROMOTION`
7. `INCONCLUSIVE_UNSUPPORTED_FRAGMENT`
8. `BACKEND_PARITY_FAILURE`

Procedural diagnostics never become theorem-backed logical rejections. Unsupported syntax or missing certification prerequisites yield `INCONCLUSIVE_UNSUPPORTED_FRAGMENT`.

## Certification boundary

`CERTIFIED` requires: completed execution; at least one blocking theorem-backed obligation; every blocking obligation satisfied; non-empty evidence lineage; Lean 4 and Coq proof evidence; valid theorem/rule bindings; complete conditional premises for T140, T150, and T156; coherent references; acyclic provenance; deterministic canonical digest; exact upstream identities.

## Negative campaign

The campaign covers theorem/diagnostic lineage, ownership uniqueness, statement hashes, backend evidence, source/tag pins, input/evidence hashes, reference integrity, provenance acyclicity, unsupported-fragment discipline, no-certification-without-lineage, conditional premises, canonicalization, deterministic replay, version locks, and frozen-baseline immutability.

## Release policy

This is a development patch only. No stable tag, GitHub Release, Zenodo version, DOI mutation, or upstream source edit is authorized.
