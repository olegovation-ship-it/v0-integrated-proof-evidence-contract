from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(rel):return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def sha(rel):return hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
def object_sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def metrics():
    own=load('baseline/theorem_ownership_T121_T156.json')['records'];cross=load('registries/theorem_rule_crosswalk.json')['records'];rules=load('registries/validator_rules.json')['rules'];adapt=load('registries/adapter_bindings.json')['bindings'];typed=load('registries/typed_outcomes.json')['outcomes'];bind=load('registries/outcome_bindings.json');neg=load('fixtures/expected/WP4_NEGATIVE_CAMPAIGN_REPORT.json');ci=load('registries/ci_job_catalog.json')['jobs']
    return {'theorem_owners':len(own),'unique_theorem_ids':len({x['theorem_id'] for x in own}),'theorem_rule_bindings':len(cross),'unmapped':sum(x.get('mapping_status')=='UNMAPPED' for x in cross),'validator_rules':len(rules),'unique_rule_ids':len({x['rule_id'] for x in rules}),'adapter_bindings':len(adapt),'typed_outcomes':len(typed),'procedural_bindings':len(bind['procedural_bindings']),'negative_fixtures':neg['negative_fixture_count'],'negative_fixtures_rejected':neg['negative_fixtures_rejected'],'typed_outcomes_exercised':len(neg['typed_outcomes_exercised']),'ci_jobs':len(ci),'conditional_theorems':sorted(x['primary_theorem_id'] for x in rules if x.get('conditional')),'local_replay_digest':load('evidence/WP5_DETERMINISTIC_REPLAY_COMPARISON.json')['result_payload_sha256']}
def hosted_pass(h):return h.get('overall_status')=='PASS' and h.get('evidence_source')=='GITHUB_ACTIONS' and all(j.get('status')=='PASS' and j.get('job_id_numeric') is not None for j in h.get('jobs',[]))
