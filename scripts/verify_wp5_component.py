#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path
from ipec_wp4.validation import schema_registry,validate_instance
from ipec_wp4.campaign import audit_negative_fixture
from ipec_wp5.ci_catalog import audit_catalog
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text())
def fail(e):print(json.dumps({'status':'FAIL','errors':e},indent=2));return 1
def main():
    c=sys.argv[1] if len(sys.argv)>1 else '';errors=[]
    if c=='schema':
        _,s=schema_registry();errors+=[] if len(s)==28 else [f'SCHEMA_COUNT:{len(s)}']
    elif c=='pins':
        lock=load('locks/upstreams.lock.json');exp={'V0_VALIDATOR_CORE_V0_12':('v0.12-compiler-passed-freeze','3540f47198140ca0a3612f247cfe356fa7fba2cb'),'V0_OSAP_V1_3_0':('v1.3.0','13bf095688bcabd5b090f188e9bd28a16237edeb')}
        for x in lock['upstreams']:
            if (x['source_ref'],x['exact_source_commit'])!=exp[x['upstream_id']]:errors.append('UPSTREAM_PIN_MISMATCH')
            if x['mutation_authorized']:errors.append('UPSTREAM_MUTATION_AUTHORIZED')
    elif c=='ownership':
        r=load('baseline/theorem_ownership_T121_T156.json')['records'];ids=[x['theorem_id'] for x in r]
        if len(r)!=36 or len(set(ids))!=36:errors.append('OWNERSHIP_NOT_36_UNIQUE')
    elif c=='crosswalk':
        r=load('registries/theorem_rule_crosswalk.json')['records']
        if len(r)!=36 or any(x.get('mapping_status')=='UNMAPPED' for x in r):errors.append('CROSSWALK_NOT_TOTAL')
    elif c in {'validator-adapter','osap-adapter'}:
        profile='VALIDATOR_CORE_V0_12_FINITE_MODEL' if c.startswith('validator') else 'OSAP_FC1_V1_1_REGISTRY';b=[x for x in load('registries/adapter_bindings.json')['bindings'] if x['source_profile']==profile]
        if not b:errors.append('ADAPTER_PROFILE_EMPTY')
        expected_class='LEGACY_STRUCTURAL_PROXY_BINDING' if c.startswith('validator') else 'EXACT_OSAP_CONSTRUCT_BINDING'
        expected_mode='DEFERRED_NO_SEMANTIC_CERTIFICATION' if c.startswith('validator') else 'DEFERRED_TO_WP4'
        if any(x.get('binding_class')!=expected_class or x.get('evaluation_mode')!=expected_mode for x in b):errors.append('ADAPTER_BINDING_POLICY_MISMATCH')
        lock=load('locks/upstreams.lock.json')
        if any(x.get('mutation_authorized') is not False for x in lock['upstreams']):errors.append('ADAPTER_UPSTREAM_MUTATION_AUTHORIZED')
    elif c=='campaign':
        idx=load('fixtures/negative_fixture_index.json')
        if len(idx['fixtures'])!=24:errors.append('NEGATIVE_FIXTURE_COUNT')
        for item in idx['fixtures']:
            if item['expected_error_code'] not in audit_negative_fixture(load(item['path'])):errors.append(item['fixture_id'])
    else:errors.append('UNKNOWN_COMPONENT')
    if errors:return fail(sorted(set(errors)))
    print(json.dumps({'status':'PASS','component':c},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
