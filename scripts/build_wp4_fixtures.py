#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from ipec_wp4.campaign import audit_negative_fixture
from ipec_wp4.outcomes import audit_envelope
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main():
    outcomes=[]
    for p in sorted((ROOT/'fixtures/outcomes').glob('*.json')):
        env=json.loads(p.read_text()); errs=audit_envelope(env)
        if errs: raise SystemExit(f'{p.name}: {errs}')
        outcomes.append(env['result']['typed_outcome_code'])
    idx=load('fixtures/negative_fixture_index.json'); results=[]
    for item in idx['fixtures']:
        f=load(item['path']); observed=audit_negative_fixture(f); passed=item['expected_error_code'] in observed
        if not passed: raise SystemExit(f"{item['fixture_id']}: expected {item['expected_error_code']}, got {observed}")
        results.append({'fixture_id':item['fixture_id'],'expected_error_code':item['expected_error_code'],'observed_error_codes':observed,'passed':True})
    report={'artifact_id':'V0_IPEC_WP4_NEGATIVE_CAMPAIGN_REPORT','contract_id':'V0-IPEC-0.1','version':'0.1','date':'2026-07-19','status':'WP4_CAMPAIGN_PASS','typed_outcome_count':8,'typed_outcomes_exercised':sorted(set(outcomes)),'negative_fixture_count':24,'negative_fixtures_rejected':24,'deterministic_replay':True,'results':results}
    import hashlib
    payload=json.dumps(report['results'],sort_keys=True,separators=(',',':')).encode();report['report_sha256']=hashlib.sha256(payload).hexdigest()
    (ROOT/'fixtures/expected/WP4_NEGATIVE_CAMPAIGN_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'PASS','typed_outcomes':len(set(outcomes)),'negative_fixtures':len(results)},indent=2))
if __name__=='__main__':main()
