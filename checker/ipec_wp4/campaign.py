from __future__ import annotations
import hashlib, json
from typing import Any
from .canonical import canonical_bytes
from .outcomes import audit_envelope, OWNERSHIP, RULES, LOCK

def _hash_obj(x:Any)->str:
    return hashlib.sha256(canonical_bytes(x)).hexdigest()

def _ownership_errors(obj:dict[str,Any])->list[str]:
    errors=[]; records=obj.get('records',[])
    tids=[r.get('theorem_id') for r in records]
    if len(tids)!=len(set(tids)):errors.append('DUPLICATE_THEOREM_OWNER')
    baseline={r['theorem_id']:r for r in OWNERSHIP['records']}
    for r in records:
        tid=r.get('theorem_id'); base=baseline.get(tid)
        if not base:errors.append('UNKNOWN_THEOREM_ID');continue
        if r.get('canonical_owner',{}).get('artifact_id')!=base.get('canonical_owner',{}).get('artifact_id'):errors.append('DUPLICATE_THEOREM_OWNER')
        observed=r.get('statement',{}).get('statement_sha256'); expected=base.get('statement',{}).get('statement_sha256')
        if observed!=expected:
            if base.get('statement',{}).get('hash_class')=='DERIVED_PHASE1_NORMALIZATION':errors.append('PHASE1_DERIVED_HASH_MISMATCH')
            else:errors.append('UPSTREAM_STATEMENT_HASH_MISMATCH')
    return sorted(set(errors))

def _crosswalk_errors(obj:dict[str,Any])->list[str]:
    bytid={r['primary_theorem_id']:r for r in RULES['rules']}; errors=[]
    for x in obj.get('records',[]):
        r=bytid.get(x.get('theorem_id'))
        if not r:errors.append('UNKNOWN_THEOREM_ID')
        elif x.get('primary_rule_id')!=r.get('rule_id'):errors.append('THEOREM_RULE_SEMANTIC_ROLE_MISMATCH')
    return sorted(set(errors))

def _lock_errors(obj:dict[str,Any])->list[str]:
    expected={x['upstream_id']:x for x in LOCK['upstreams']}; errors=[]
    for x in obj.get('upstreams',[]):
        e=expected.get(x.get('upstream_id'))
        if e and (x.get('source_ref')!=e.get('source_ref') or x.get('exact_source_commit')!=e.get('exact_source_commit')):errors.append('RELEASE_TAG_TARGET_MISMATCH')
    return errors

def audit_negative_fixture(f:dict[str,Any])->list[str]:
    t=f.get('target_type'); payload=f.get('payload',{}); aux=f.get('auxiliary',{})
    if t=='CANONICAL_ENVELOPE':
        errors=audit_envelope(payload)
        # Evidence content hash verification for fixtures that provide payload material.
        for eid,material in aux.get('evidence_payloads',{}).items():
            matches=[e for e in payload.get('evidence_lineage',[]) if e.get('evidence_id')==eid]
            if matches and matches[0].get('evidence_sha256')!=_hash_obj(material):errors.append('EVIDENCE_HASH_MISMATCH')
        if 'input_payload' in aux:
            expected=_hash_obj(aux['input_payload'])
            if payload.get('request',{}).get('input_identity',{}).get('payload_sha256')!=expected:errors.append('INPUT_PAYLOAD_HASH_MISMATCH')
        expected_osap='13bf095688bcabd5b090f188e9bd28a16237edeb'
        for e in payload.get('evidence_lineage',[]):
            sr=e.get('source_release',{})
            if sr.get('repository')=='olegovation-ship-it/v0-osap-formal-core' and sr.get('commit')!=expected_osap:errors.append('UPSTREAM_SOURCE_COMMIT_MISMATCH')
        lock=payload.get('upstream_lock',{})
        if lock.get('osap',{}).get('exact_source_commit')!=expected_osap:errors.append('RELEASE_TAG_TARGET_MISMATCH')
        current=aux.get('current_version_lock'); expected=aux.get('expected_version_lock')
        if current is not None and expected is not None and current!=expected:errors.append('VERSION_LOCK_TUPLE_MISMATCH')
        return sorted(set(errors))
    if t=='THEOREM_OWNERSHIP_MAP':return _ownership_errors(payload)
    if t=='THEOREM_RULE_CROSSWALK':return _crosswalk_errors(payload)
    if t=='UPSTREAM_LOCK':return _lock_errors(payload)
    if t=='REPLAY_PAIR':
        first=payload.get('first',{}); second=payload.get('second',{})
        return [] if first.get('integrity',{}).get('canonical_sha256')==second.get('integrity',{}).get('canonical_sha256') else ['REPLAY_NONDETERMINISTIC_RESULT']
    if t=='BASELINE_HASH_SET':
        return [] if payload.get('expected_sha256')==payload.get('observed_sha256') else ['FROZEN_BASELINE_MUTATION_DETECTED']
    return ['UNKNOWN_NEGATIVE_FIXTURE_TARGET']
