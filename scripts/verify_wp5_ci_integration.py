#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from ipec_wp4.validation import schema_registry,validate_instance
from ipec_wp5.ci_catalog import audit_catalog,audit_workflow_text
from ipec_wp5.evidence import source_snapshot,object_sha,replay_report
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wp4-package',type=Path);a=ap.parse_args();errors=[]
    ref=load('baseline/WP4_BASELINE_REFERENCE.json')
    if a.wp4_package and sha(a.wp4_package)!=ref['wp4_package_sha256']:errors.append('WP4_PACKAGE_HASH_MISMATCH')
    for m in ref['baseline_files'].values():
        if sha(ROOT/m['path'])!=m['sha256']:errors.append(f"WP4_BASELINE_HASH_MISMATCH:{m['path']}")
    _,schemas=schema_registry()
    if len(schemas)!=21:errors.append(f'SCHEMA_COUNT_MISMATCH:{len(schemas)}')
    catalog=load('registries/ci_job_catalog.json');errors += validate_instance(catalog,'https://v0-ipec.example/spec/v0.1/ci_job_catalog.schema.json');errors += audit_catalog(catalog)
    wf=(ROOT/'.github/workflows/gate2-integration.yml').read_text();errors += audit_workflow_text(wf,[x['job_id'] for x in catalog['jobs']])
    r1=load('evidence/WP5_DETERMINISTIC_REPLAY_RUN_1.json');r2=load('evidence/WP5_DETERMINISTIC_REPLAY_RUN_2.json');comp=load('evidence/WP5_DETERMINISTIC_REPLAY_COMPARISON.json')
    errors += validate_instance(r1,'https://v0-ipec.example/spec/v0.1/replay_report.schema.json');errors += validate_instance(r2,'https://v0-ipec.example/spec/v0.1/replay_report.schema.json');errors += validate_instance(comp,'https://v0-ipec.example/spec/v0.1/replay_comparison.schema.json')
    fresh1=replay_report('RUN_1');fresh2=replay_report('RUN_2')
    if r1!=fresh1 or r2!=fresh2:errors.append('DETERMINISTIC_REPLAY_RECORD_DRIFT')
    if r1['result_payload_sha256']!=r2['result_payload_sha256'] or not comp['deterministic']:errors.append('DETERMINISTIC_REPLAY_MISMATCH')
    for p in ['release/v0.1/WP5_DETERMINISTIC_EVIDENCE_MANIFEST.json','release/v0.1/WP5_CI_INTEGRATION_MANIFEST.json']:
        x=load(p);errors += validate_instance(x,'https://v0-ipec.example/spec/v0.1/evidence_manifest.schema.json')
        for rel,h in x['files'].items():
            if sha(ROOT/rel)!=h:errors.append(f'MANIFEST_HASH_MISMATCH:{rel}')
    m=r1['metrics']
    expected={'theorem_owners':36,'theorem_rule_bindings':36,'validator_rules':36,'adapter_bindings':40,'typed_outcomes':8,'procedural_bindings':11,'negative_fixtures':24,'negative_fixtures_rejected':24}
    for k,v in expected.items():
        if m.get(k)!=v:errors.append(f'METRIC_MISMATCH:{k}')
    if errors:
        print(json.dumps({'status':'FAIL','errors':sorted(set(errors))},indent=2));return 1
    print(json.dumps({'status':'PASS','schema_count':21,'ci_jobs':'12/12','theorem_ownership':'36/36','crosswalk':'36/36','adapter_bindings':40,'typed_outcomes':'8/8','negative_fixtures':'24/24','deterministic_replay':'2/2','global_permissions':'contents:read','remote_ci_execution':'PENDING_IN_STANDALONE_PATCH','frozen_upstreams_modified':False,'next_deliverable':'WP6_GATE2_AUDIT_AND_CLOSURE'},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
