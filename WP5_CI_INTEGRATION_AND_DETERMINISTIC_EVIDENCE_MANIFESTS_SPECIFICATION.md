# WP5 CI Integration and Deterministic Evidence Manifests Specification

## Scope

WP5 consumes the frozen WP4 typed-outcome and negative-fixture baseline. It defines a read-only twelve-job Gate 2 CI graph, pins both upstream repositories by immutable tag and exact commit, and produces deterministic proof-evidence manifests from the WP1–WP4 registries.

## CI graph

The graph contains twelve ordered jobs: contract schemas; upstream pins; theorem ownership; crosswalk totality; Validator adapter; OSAP adapter; frozen Validator replay; OSAP Python replay; OSAP Lean replay; OSAP Coq replay; negative-fixture campaign; and Gate 2 pre-audit aggregation.

Every job has `contents: read`. No job may push, create or move tags, publish a release, upload to Zenodo, edit DOI metadata, or mutate either upstream source tree.

## Deterministic evidence

Two independent local reference replays are generated from the same canonical source snapshot. Their result payload SHA-256 values must be identical. Runtime timestamps, runner identifiers, temporary paths, and network ordering are excluded from the canonical result payload.

## Execution boundary

The standalone patch validates the workflow graph, contracts, hashes, fixtures, and deterministic local replay. Actual GitHub-hosted execution of the four upstream replay jobs occurs only after the patch is placed on the integration repository branch. WP5 does not claim that those remote jobs have already run.

## Release policy

This is a development patch. It authorizes preparation of WP6 but does not close Gate 2, create a stable tag, publish a GitHub Release, create a Zenodo version, mutate a DOI, or change the frozen Paper B baseline.
