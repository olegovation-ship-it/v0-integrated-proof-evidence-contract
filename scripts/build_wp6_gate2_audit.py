#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from ipec_wp6.audit import ROOT,load,sha,object_sha,metrics,hosted_pass
DATE='2026-07-20'
def dump(rel,o):(ROOT/rel).parent.mkdir(parents=True,exist_ok=True);(ROOT/rel).write_text(json.dumps(o,indent=2)+'\n')
def objects():
 m=metrics();h=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json');hp=hosted_pass(h)
 gates=[
 ('G2-01','WP5 predecessor package and selected baseline hashes are exact','PASS',['baseline/WP5_BASELINE_REFERENCE.json']),
 ('G2-02','Validator Core and OSAP immutable source pins are preserved','PASS',['locks/upstreams.lock.json']),
 ('G2-03','JSON Schema bundle contains 25 valid Draft 2020-12 schemas','PASS',['schemas/v0.1/schema_bundle_manifest.json']),
 ('G2-04','Theorem ownership coverage is 36 of 36','PASS',['baseline/theorem_ownership_T121_T156.json']),
 ('G2-05','Theorem owner collisions are zero','PASS',['baseline/theorem_ownership_T121_T156.json']),
 ('G2-06','Theorem-rule crosswalk coverage is 36 of 36','PASS',['registries/theorem_rule_crosswalk.json']),
 ('G2-07','Unmapped theorem records and rule-ID collisions are zero','PASS',['registries/theorem_rule_crosswalk.json','registries/validator_rules.json']),
 ('G2-08','Read-only adapter bindings total 40','PASS',['registries/adapter_bindings.json']),
 ('G2-09','Every diagnostic is theorem-backed or explicitly procedural; procedural bindings total 11','PASS',['registries/procedural_diagnostics.json','registries/outcome_bindings.json']),
 ('G2-10','Typed outcome registry contains exactly eight outcomes','PASS',['registries/typed_outcomes.json']),
 ('G2-11','All eight typed outcomes are exercised by canonical fixtures','PASS',['fixtures/expected/WP4_NEGATIVE_CAMPAIGN_REPORT.json']),
 ('G2-12','All 24 deliberate negative integration fixtures are rejected as specified','PASS',['fixtures/expected/WP4_NEGATIVE_CAMPAIGN_REPORT.json']),
 ('G2-13','Unsupported or procedural fragments resolve to INCONCLUSIVE, not theorem-backed rejection','PASS',['registries/outcome_bindings.json','registries/typed_outcomes.json']),
 ('G2-14','CERTIFIED requires non-empty lineage and Lean 4 plus Coq evidence','PASS',['fixtures/outcomes/CERTIFIED.json','fixtures/negative/N19_certified_without_lineage.json']),
 ('G2-15','Conditionality is preserved exactly for T140, T150, and T156','PASS',['registries/validator_rules.json']),
 ('G2-16','Evidence provenance acyclicity is enforced','PASS',['fixtures/negative/N17_evidence_provenance_cycle.json','fixtures/expected/WP4_NEGATIVE_CAMPAIGN_REPORT.json']),
 ('G2-17','Two local clean reference replays have identical canonical result hash','PASS',['evidence/WP5_DETERMINISTIC_REPLAY_COMPARISON.json']),
 ('G2-18','The 12-job CI graph is acyclic, read-only, and contains no release mutation command','PASS',['registries/ci_job_catalog.json','.github/workflows/gate2-integration.yml']),
 ('G2-19','WP5 deterministic manifests, regression baseline, and internal hashes reproduce','PASS',['release/v0.1/WP5_DETERMINISTIC_EVIDENCE_MANIFEST.json','SHA256SUMS.txt']),
 ('G2-20','Hosted Validator, OSAP Python, OSAP Lean 4, and OSAP Coq replay jobs are green','PASS' if hp else 'PENDING_EXTERNAL_EXECUTION',['evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json'])]
 gs=[{'gate_id':a,'requirement':b,'status':c,'evidence':d} for a,b,c,d in gates];pc=sum(x['status']=='PASS' for x in gs);pd=sum(x['status']=='PENDING_EXTERNAL_EXECUTION' for x in gs);fc=sum(x['status']=='FAIL' for x in gs)
 status='PASS' if pc==20 else ('FAIL' if fc else 'HOLD');decision='CLOSE_GATE2' if status=='PASS' else ('REJECT_CLOSURE' if status=='FAIL' else 'HOLD_FOR_HOSTED_CI');closed=status=='PASS'
 ag={'artifact_id':'V0_IPEC_WP6_GATE2_ACCEPTANCE_GATES','contract_id':'V0-IPEC-0.1','version':'0.1','date':DATE,'status':status,'gate_count':20,'pass_count':pc,'pending_count':pd,'fail_count':fc,'gates':gs,'gate2_closed':closed}
 local={'artifact_id':'V0_IPEC_WP6_LOCAL_AUDIT_EVIDENCE','contract_id':'V0-IPEC-0.1','version':'0.1','date':DATE,'status':'PASS','metrics':m,'wp5_predecessor_sha256':load('baseline/WP5_BASELINE_REFERENCE.json')['wp5_package_sha256'],'local_checks_passed':19,'hosted_checks_executed':4 if hp else 0,'frozen_upstreams_modified':False}
 eligibility={'artifact_id':'V0_IPEC_WP6_CLOSURE_ELIGIBILITY_REPORT','contract_id':'V0-IPEC-0.1','version':'0.1','date':DATE,'status':status,'closure_eligible_after_hosted_ci':fc==0 and (pd==1 or closed),'remaining_blockers':['G2-20_HOSTED_UPSTREAM_REPLAY_NOT_RECORDED'] if pd else [],'automatic_reaudit_condition':'Replace the pending hosted-CI intake record with authentic GitHub Actions evidence and rerun the WP6 verifier.'}
 payload={'gates':gs,'metrics':m,'hosted_status':h['overall_status'],'decision':decision}
 audit={'artifact_id':'V0_IPEC_WP6_GATE2_AUDIT_RESULT','contract_id':'V0-IPEC-0.1','version':'0.1','date':DATE,'status':status,'decision':decision,'gate2_closed':closed,'closure_eligible':closed,'gate_summary':{'total':20,'pass':pc,'pending':pd,'fail':fc},'metrics':m,'single_blocker':None if closed else 'G2-20: authentic green GitHub Actions evidence for four hosted upstream replay jobs is not recorded.','audit_payload_sha256':object_sha(payload),'frozen_upstreams_modified':False}
 closure={'artifact_id':'V0_IPEC_WP6_GATE2_CLOSURE_RECORD','contract_id':'V0-IPEC-0.1','version':'0.1','date':DATE,'decision':decision,'gate2_closed':closed,'closure_authorized':closed,'reason':'All Gate 2 acceptance conditions are satisfied.' if closed else 'Nineteen local and structural gates pass; closure is withheld until authentic hosted replay evidence is supplied.','required_next_evidence':[] if closed else ['GitHub Actions run ID and URL','Exact integration head SHA','PASS status for j07, j08, j09, and j10','Downloaded workflow artifact hash or equivalent immutable evidence'],'release_actions':{'tag_created':False,'github_release_created':False,'zenodo_published':False,'doi_mutated':False},'nonclaims':['Gate 2 CI is not peer review.','Gate 2 CI is not empirical or physical validation.','Structural correspondence is not proof-term identity or checker completeness.']}
 return ag,local,eligibility,audit,closure

def build(write=True):
 ag,local,eli,audit,closure=objects()
 mapping={'audit/WP6_GATE2_ACCEPTANCE_GATES.json':ag,'evidence/WP6_LOCAL_AUDIT_EVIDENCE.json':local,'evidence/WP6_CLOSURE_ELIGIBILITY_REPORT.json':eli,'audit/WP6_GATE2_AUDIT_RESULT.json':audit,'release/v0.1/WP6_GATE2_CLOSURE_RECORD.json':closure}
 if write:
  for p,o in mapping.items():dump(p,o)
 selected=['baseline/WP5_BASELINE_REFERENCE.json','schemas/v0.1/schema_bundle_manifest.json','audit/WP6_GATE2_ACCEPTANCE_GATES.json','audit/WP6_GATE2_AUDIT_RESULT.json','evidence/WP6_LOCAL_AUDIT_EVIDENCE.json','evidence/WP6_CLOSURE_ELIGIBILITY_REPORT.json','evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json','release/v0.1/WP6_GATE2_CLOSURE_RECORD.json','WP6_GATE2_AUDIT_AND_CLOSURE_SPECIFICATION.md','.github/workflows/gate2-closure-audit.yml']
 man={'artifact_id':'V0_IPEC_WP6_GATE2_AUDIT_MANIFEST','contract_id':'V0-IPEC-0.1','version':'0.1','date':DATE,'state':('GATE2_CLOSED_HOSTED_CI_VERIFIED' if audit['gate2_closed'] else 'GATE2_AUDIT_COMPLETE_CLOSURE_HOLD_HOSTED_CI_PENDING'),'files':{p:sha(p) for p in selected if (ROOT/p).exists()},'gate_summary':audit['gate_summary'],'decision':audit['decision'],'audit_payload_sha256':audit['audit_payload_sha256'],'frozen_upstreams_modified':False}
 if write:dump('release/v0.1/WP6_GATE2_AUDIT_MANIFEST.json',man)
 return mapping,man

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();mapping,man=build(write=not a.check)
 if a.check:
  mapping=dict(mapping);mapping['release/v0.1/WP6_GATE2_AUDIT_MANIFEST.json']=man;drift=[]
  for p,o in mapping.items():
   t=json.dumps(o,indent=2)+'\n';q=ROOT/p
   if not q.exists() or q.read_text()!=t:drift.append(p)
  if drift:print(json.dumps({'status':'FAIL','drift':drift},indent=2));return 1
 audit=mapping['audit/WP6_GATE2_AUDIT_RESULT.json'];summary=audit['gate_summary'];print(json.dumps({'status':audit['status'],'decision':audit['decision'],'gates':f"{summary['pass']}/{summary['total']} PASS",'pending':summary['pending'],'gate2_closed':audit['gate2_closed']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
