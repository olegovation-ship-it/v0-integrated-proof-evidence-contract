#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from ipec_wp4.validation import schema_registry,validate_instance
from ipec_wp5.ci_catalog import audit_catalog,audit_workflow_text
from ipec_wp6.audit import ROOT,load,sha,metrics,hosted_pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--wp5-package',type=Path);ap.add_argument('--allow-pending',action='store_true');a=ap.parse_args();e=[]
 ref=load('baseline/WP5_BASELINE_REFERENCE.json')
 if a.wp5_package and hashlib.sha256(a.wp5_package.read_bytes()).hexdigest()!=ref['wp5_package_sha256']:e.append('WP5_PACKAGE_HASH_MISMATCH')
 for m in ref['baseline_files'].values():
  if sha(m['path'])!=m['sha256']:e.append('WP5_BASELINE_HASH_MISMATCH:'+m['path'])
 _,schemas=schema_registry()
 if len(schemas)!=28:e.append('SCHEMA_COUNT_MISMATCH:'+str(len(schemas)))
 for p,sid in [('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json','https://v0-ipec.example/spec/v0.1/hosted_ci_evidence.schema.json'),('audit/WP6_GATE2_ACCEPTANCE_GATES.json','https://v0-ipec.example/spec/v0.1/gate2_acceptance_gates.schema.json'),('audit/WP6_GATE2_AUDIT_RESULT.json','https://v0-ipec.example/spec/v0.1/gate2_audit_result.schema.json'),('release/v0.1/WP6_GATE2_CLOSURE_RECORD.json','https://v0-ipec.example/spec/v0.1/gate2_closure_record.schema.json')]:e+=validate_instance(load(p),sid)
 m=metrics();expected={'theorem_owners':36,'unique_theorem_ids':36,'theorem_rule_bindings':36,'unmapped':0,'validator_rules':36,'unique_rule_ids':36,'adapter_bindings':40,'typed_outcomes':8,'procedural_bindings':11,'negative_fixtures':24,'negative_fixtures_rejected':24,'typed_outcomes_exercised':8,'ci_jobs':12}
 for k,v in expected.items():
  if m.get(k)!=v:e.append('METRIC_MISMATCH:'+k)
 if m['conditional_theorems']!=['T140','T150','T156']:e.append('CONDITIONAL_THEOREM_SET_MISMATCH')
 catalog=load('registries/ci_job_catalog.json');e+=audit_catalog(catalog);e+=audit_workflow_text((ROOT/'.github/workflows/gate2-integration.yml').read_text(),[x['job_id'] for x in catalog['jobs']])
 neg=load('fixtures/expected/WP4_NEGATIVE_CAMPAIGN_REPORT.json')
 byid={x['fixture_id']:x for x in neg['results']}
 for fid,code in [('N17','EVIDENCE_PROVENANCE_CYCLE'),('N18','UNSUPPORTED_FRAGMENT_REPORTED_AS_REJECTION'),('N19','CERTIFIED_WITHOUT_LINEAGE'),('N20','CONDITIONAL_THEOREM_PREMISE_MISSING')]:
  if code not in byid[fid]['observed_error_codes']:e.append('NEGATIVE_CONTROL_MISSING:'+fid)
 cert=load('fixtures/outcomes/CERTIFIED.json');backs={x['backend'] for x in cert['evidence_lineage']}
 if not cert['evidence_lineage'] or not {'LEAN4','COQ'}<=backs:e.append('CERTIFIED_EVIDENCE_LINEAGE_INCOMPLETE')
 proc=load('registries/outcome_bindings.json')['procedural_bindings']
 if any(x['outcome']!='INCONCLUSIVE_UNSUPPORTED_FRAGMENT' for x in proc):e.append('PROCEDURAL_OUTCOME_POLICY_MISMATCH')
 comp=load('evidence/WP5_DETERMINISTIC_REPLAY_COMPARISON.json')
 if not comp['deterministic'] or not comp['same_result_sha256']:e.append('LOCAL_REPLAY_NOT_DETERMINISTIC')
 gates=load('audit/WP6_GATE2_ACCEPTANCE_GATES.json');hosted=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json');hp=hosted_pass(hosted)
 if hp:
  if gates['status']!='PASS' or not gates['gate2_closed']:e.append('CLOSURE_STATE_NOT_UPDATED_AFTER_HOSTED_PASS')
 else:
  if gates['status']!='HOLD' or gates['pass_count']!=19 or gates['pending_count']!=1 or gates['gate2_closed']:e.append('PENDING_CLOSURE_STATE_INVALID')
 for rel,h in load('release/v0.1/WP6_GATE2_AUDIT_MANIFEST.json')['files'].items():
  if sha(rel)!=h:e.append('MANIFEST_HASH_MISMATCH:'+rel)
 if e:print(json.dumps({'status':'FAIL','errors':sorted(set(e))},indent=2));return 1
 if not hp and not a.allow_pending:
  print(json.dumps({'status':'HOLD','reason':'HOSTED_CI_EVIDENCE_PENDING','gate2_closed':False},indent=2));return 2
 print(json.dumps({'status':'PASS' if hp else 'HOLD_ACCEPTED','local_gates':'19/19','hosted_gate':'PASS' if hp else 'PENDING','gate2_closed':hp},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
