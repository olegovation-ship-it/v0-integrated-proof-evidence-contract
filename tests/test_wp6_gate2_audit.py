from __future__ import annotations
import hashlib,json
from pathlib import Path
from ipec_wp4.validation import schema_registry,validate_instance
from ipec_wp5.ci_catalog import audit_catalog,audit_workflow_text
from ipec_wp6.audit import ROOT,load,metrics,hosted_pass

def sha(rel):return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
def test_schema_bundle_has_twenty_five_schemas():_,s=schema_registry();assert len(s)==25
def test_wp5_predecessor_selected_hashes_are_exact():
 x=load('baseline/WP5_BASELINE_REFERENCE.json');assert x['frozen'] and not x['mutation_authorized'];assert all(sha(m['path'])==m['sha256'] for m in x['baseline_files'].values())
def test_gate_registry_has_twenty_gates_and_consistent_closure_state():
 x=load('audit/WP6_GATE2_ACCEPTANCE_GATES.json');h=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json');assert x['gate_count']==20;assert x['fail_count']==0
 if hosted_pass(h):
  assert x['pass_count']==20;assert x['pending_count']==0;assert x['gate2_closed']
 else:
  assert x['pass_count']==19;assert x['pending_count']==1;assert not x['gate2_closed']
def test_gate_ids_are_unique_and_sequential():
 x=load('audit/WP6_GATE2_ACCEPTANCE_GATES.json')['gates'];assert [g['gate_id'] for g in x]==[f'G2-{i:02d}' for i in range(1,21)]
def test_audit_and_closure_schemas_validate():
 pairs=[('audit/WP6_GATE2_ACCEPTANCE_GATES.json','https://v0-ipec.example/spec/v0.1/gate2_acceptance_gates.schema.json'),('audit/WP6_GATE2_AUDIT_RESULT.json','https://v0-ipec.example/spec/v0.1/gate2_audit_result.schema.json'),('release/v0.1/WP6_GATE2_CLOSURE_RECORD.json','https://v0-ipec.example/spec/v0.1/gate2_closure_record.schema.json'),('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json','https://v0-ipec.example/spec/v0.1/hosted_ci_evidence.schema.json')]
 for p,s in pairs:assert validate_instance(load(p),s)==[]
def test_hosted_evidence_is_authentic_or_explicitly_pending():
 x=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json')
 if hosted_pass(x):
  assert x['overall_status']=='PASS' and x['evidence_source']=='GITHUB_ACTIONS';assert isinstance(x['run_id'],int);assert x['run_url'];assert isinstance(x['head_sha'],str) and len(x['head_sha'])==40
  assert all(j['status']=='PASS' and isinstance(j['job_id_numeric'],int) and isinstance(j['artifact_sha256'],str) and len(j['artifact_sha256'])==64 for j in x['jobs'])
 else:
  assert x['overall_status']=='PENDING' and x['evidence_source']=='NOT_RECORDED';assert x['run_id'] is x['run_url'] is x['head_sha'] is None;assert all(j['status']=='PENDING' and j['job_id_numeric'] is None for j in x['jobs'])
def test_audit_decision_matches_hosted_evidence():
 x=load('audit/WP6_GATE2_AUDIT_RESULT.json');h=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json')
 if hosted_pass(h):
  assert x['status']=='PASS';assert x['decision']=='CLOSE_GATE2';assert x['gate2_closed'] and x['closure_eligible'];assert x['gate_summary']=={'total':20,'pass':20,'pending':0,'fail':0}
 else:
  assert x['status']=='HOLD';assert x['decision']=='HOLD_FOR_HOSTED_CI';assert not x['gate2_closed'] and not x['closure_eligible'];assert x['gate_summary']=={'total':20,'pass':19,'pending':1,'fail':0}
def test_closure_record_matches_hosted_evidence_and_creates_no_release_action():
 x=load('release/v0.1/WP6_GATE2_CLOSURE_RECORD.json');h=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json')
 if hosted_pass(h):
  assert x['decision']=='CLOSE_GATE2';assert x['gate2_closed'] and x['closure_authorized']
 else:
  assert x['decision']=='HOLD_FOR_HOSTED_CI';assert not x['gate2_closed'] and not x['closure_authorized']
 assert not any(x['release_actions'].values())
def test_core_metrics_are_exact():
 m=metrics();assert m['theorem_owners']==m['unique_theorem_ids']==36;assert m['theorem_rule_bindings']==m['validator_rules']==m['unique_rule_ids']==36;assert m['unmapped']==0;assert m['adapter_bindings']==40;assert m['typed_outcomes']==8;assert m['procedural_bindings']==11;assert m['negative_fixtures']==m['negative_fixtures_rejected']==24;assert m['typed_outcomes_exercised']==8
def test_conditional_theorems_are_exact():assert metrics()['conditional_theorems']==['T140','T150','T156']
def test_procedural_bindings_are_inconclusive():assert all(x['outcome']=='INCONCLUSIVE_UNSUPPORTED_FRAGMENT' for x in load('registries/outcome_bindings.json')['procedural_bindings'])
def test_certified_fixture_has_lineage_and_dual_backend():
 x=load('fixtures/outcomes/CERTIFIED.json');assert x['evidence_lineage'];assert {'LEAN4','COQ'}<={e['backend'] for e in x['evidence_lineage']}
def test_critical_negative_controls_are_present():
 x={r['fixture_id']:r for r in load('fixtures/expected/WP4_NEGATIVE_CAMPAIGN_REPORT.json')['results']};assert 'EVIDENCE_PROVENANCE_CYCLE' in x['N17']['observed_error_codes'];assert 'UNSUPPORTED_FRAGMENT_REPORTED_AS_REJECTION' in x['N18']['observed_error_codes'];assert 'CERTIFIED_WITHOUT_LINEAGE' in x['N19']['observed_error_codes'];assert 'CONDITIONAL_THEOREM_PREMISE_MISSING' in x['N20']['observed_error_codes']
def test_local_replay_is_deterministic():
 x=load('evidence/WP5_DETERMINISTIC_REPLAY_COMPARISON.json');assert x['status']=='PASS' and x['deterministic'] and x['same_result_sha256']
def test_ci_graph_remains_read_only_and_acyclic():
 x=load('registries/ci_job_catalog.json');assert len(x['jobs'])==12;assert audit_catalog(x)==[];assert audit_workflow_text((ROOT/'.github/workflows/gate2-integration.yml').read_text(),[j['job_id'] for j in x['jobs']])==[]
def test_wp6_manifest_hashes_and_state_match():
 x=load('release/v0.1/WP6_GATE2_AUDIT_MANIFEST.json');h=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json')
 if hosted_pass(h):
  assert x['decision']=='CLOSE_GATE2';assert x['state']=='GATE2_CLOSED_HOSTED_CI_VERIFIED'
 else:
  assert x['decision']=='HOLD_FOR_HOSTED_CI';assert x['state']=='GATE2_AUDIT_COMPLETE_CLOSURE_HOLD_HOSTED_CI_PENDING'
 assert all(sha(p)==digest for p,digest in x['files'].items())
def test_no_frozen_upstream_mutation_is_claimed():
 assert load('audit/WP6_GATE2_AUDIT_RESULT.json')['frozen_upstreams_modified'] is False;assert load('release/v0.1/WP6_GATE2_AUDIT_MANIFEST.json')['frozen_upstreams_modified'] is False
def test_closure_eligibility_matches_hosted_evidence():
 x=load('evidence/WP6_CLOSURE_ELIGIBILITY_REPORT.json');h=load('evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json');assert x['closure_eligible_after_hosted_ci']
 if hosted_pass(h):
  assert x['status']=='PASS';assert x['remaining_blockers']==[]
 else:
  assert x['status']=='HOLD';assert x['remaining_blockers']==['G2-20_HOSTED_UPSTREAM_REPLAY_NOT_RECORDED']
