from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
from .canonical import verify_envelope_digest
ROOT=Path(__file__).resolve().parents[2]

def load(rel: str)->Any:
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))

OUTCOMES=load('registries/typed_outcomes.json')
BINDINGS=load('registries/outcome_bindings.json')
RULES=load('registries/validator_rules.json')
OWNERSHIP=load('baseline/theorem_ownership_T121_T156.json')
LOCK=load('locks/upstreams.lock.json')
PRIORITY={x['code']:x['priority'] for x in OUTCOMES['outcomes']}
OUTCOME_META={x['code']:x for x in OUTCOMES['outcomes']}
RULE_OUTCOME={x['rule_id']:x['on_violation_outcome'] for x in BINDINGS['rule_bindings']}
RULE_THEOREM={x['rule_id']:x['theorem_id'] for x in BINDINGS['rule_bindings']}
RULE_BY_TID={x['primary_theorem_id']:x for x in RULES['rules']}
PROC_CODES={x['code'] for x in BINDINGS['procedural_bindings']}
TIDS={x['theorem_id'] for x in OWNERSHIP['records']}
EXPECTED_LOCK={x['upstream_id']:x for x in LOCK['upstreams']}

def _result(code: str, basis: list[str])->dict[str,Any]:
    meta=OUTCOME_META[code]
    return {'execution_status':'COMPLETED','logical_verdict':meta['logical_verdict'],'typed_outcome_code':code,'typed_outcome_registry_version':'0.1','outcome_binding_status':'BOUND','certification_claimed':meta['certification_claimed'],'resolution_basis':sorted(set(basis))}

def resolve_outcome(envelope: dict[str,Any])->dict[str,Any]:
    candidates: list[tuple[str,str]]=[]
    for d in envelope.get('diagnostic_envelope',{}).get('diagnostics',[]):
        if d.get('diagnostic_class')=='PROCEDURAL':
            candidates.append(('INCONCLUSIVE_UNSUPPORTED_FRAGMENT',f"procedural:{d.get('code')}"))
        else:
            rid=d.get('validator_rule_id')
            candidates.append((RULE_OUTCOME.get(rid,'INCONCLUSIVE_UNSUPPORTED_FRAGMENT'),f"diagnostic:{d.get('code')}"))
    for o in envelope.get('obligations',[]):
        if not o.get('blocking',False):
            continue
        if o.get('state')=='VIOLATED':
            rid=o.get('validator_rule_id')
            candidates.append((RULE_OUTCOME.get(rid,'INCONCLUSIVE_UNSUPPORTED_FRAGMENT'),f"violated:{o.get('obligation_id')}"))
        elif o.get('state') in {'UNSUPPORTED','DEFERRED'}:
            candidates.append(('INCONCLUSIVE_UNSUPPORTED_FRAGMENT',f"{o.get('state','unknown').lower()}:{o.get('obligation_id')}"))
    if candidates:
        code=max(candidates,key=lambda x:PRIORITY[x[0]])[0]
        basis=[b for c,b in candidates if c==code]
        return _result(code,basis)
    return _result('CERTIFIED',['all_blocking_obligations_satisfied'])

def _acyclic(items: list[dict[str,Any]])->bool:
    graph={x.get('evidence_id'):list(x.get('provenance_parent_ids',[])) for x in items}
    state:dict[str,int]={}
    def visit(n:str)->bool:
        if state.get(n)==1:return False
        if state.get(n)==2:return True
        state[n]=1
        for m in graph.get(n,[]):
            if m in graph and not visit(m):return False
        state[n]=2; return True
    return all(visit(n) for n in graph)

def audit_envelope(envelope: dict[str,Any])->list[str]:
    errors=[]
    obligations=envelope.get('obligations',[])
    diagnostics=envelope.get('diagnostic_envelope',{}).get('diagnostics',[])
    evidence=envelope.get('evidence_lineage',[])
    eids=[x.get('evidence_id') for x in evidence]
    if len(eids)!=len(set(eids)):errors.append('DUPLICATE_EVIDENCE_ID')
    eset=set(eids)
    for item in obligations+diagnostics:
        for eid in item.get('evidence_reference_ids',[]):
            if eid not in eset:errors.append('EVIDENCE_REFERENCE_MISSING')
    for e in evidence:
        for parent in e.get('provenance_parent_ids',[]):
            if parent not in eset:errors.append('EVIDENCE_REFERENCE_MISSING')
    if not _acyclic(evidence):errors.append('EVIDENCE_PROVENANCE_CYCLE')
    for o in obligations:
        tid=o.get('primary_theorem_id'); rid=o.get('validator_rule_id')
        if o.get('origin')=='THEOREM_BACKED':
            if tid not in TIDS:errors.append('UNKNOWN_THEOREM_ID')
            if rid not in RULE_THEOREM or RULE_THEOREM.get(rid)!=tid:errors.append('THEOREM_RULE_SEMANTIC_ROLE_MISMATCH')
            rule=RULE_BY_TID.get(tid)
            if rule and rule.get('conditional'):
                missing=set(rule.get('conditional_premises',[]))-set(o.get('premises',[]))
                if missing:errors.append('CONDITIONAL_THEOREM_PREMISE_MISSING')
    for d in diagnostics:
        if d.get('diagnostic_class')=='THEOREM_BACKED':
            if d.get('theorem_id') is None:errors.append('THEOREM_BACKED_DIAGNOSTIC_MISSING_THEOREM_ID')
            if d.get('theorem_id') not in TIDS:errors.append('UNKNOWN_THEOREM_ID')
            if RULE_THEOREM.get(d.get('validator_rule_id'))!=d.get('theorem_id'):errors.append('THEOREM_RULE_SEMANTIC_ROLE_MISMATCH')
        if d.get('diagnostic_class')=='PROCEDURAL' and d.get('procedural_label') is not True:errors.append('PROCEDURAL_DIAGNOSTIC_MISSING_LABEL')
    result=envelope.get('result',{})
    resolved=resolve_outcome(envelope)
    for key in ['logical_verdict','typed_outcome_code','certification_claimed']:
        if result.get(key)!=resolved.get(key):
            if any(d.get('code')=='UNSUPPORTED_CLAIM_KIND' for d in diagnostics) and str(result.get('typed_outcome_code','')).startswith('REJECTED_'):
                errors.append('UNSUPPORTED_FRAGMENT_REPORTED_AS_REJECTION')
            elif any(d.get('code')=='BACKEND_STATEMENT_HASH_MISMATCH' for d in diagnostics):
                errors.append('BACKEND_STATEMENT_PARITY_MISMATCH')
            else:errors.append('TYPED_OUTCOME_RESOLUTION_MISMATCH')
            break
    if result.get('typed_outcome_code')=='CERTIFIED':
        if not evidence:errors.append('CERTIFIED_WITHOUT_LINEAGE')
        if not obligations or any(o.get('blocking') and o.get('state')!='SATISFIED' for o in obligations):errors.append('CERTIFIED_WITH_UNSATISFIED_OBLIGATION')
        lean=any(e.get('backend')=='LEAN4' and e.get('proof_status') in {'PROVED','VERIFIED'} for e in evidence)
        coq=any(e.get('backend')=='COQ' and e.get('proof_status') in {'PROVED','VERIFIED'} for e in evidence)
        if not lean:errors.append('LEAN_BACKEND_EVIDENCE_MISSING')
        if not coq:errors.append('COQ_BACKEND_EVIDENCE_MISSING')
    if not verify_envelope_digest(envelope):errors.append('CANONICAL_SERIALIZATION_MISMATCH')
    return sorted(set(errors))
