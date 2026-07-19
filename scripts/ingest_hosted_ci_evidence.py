#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('evidence',type=Path);a=ap.parse_args();x=json.loads(a.evidence.read_text());schema=json.loads((ROOT/'schemas/v0.1/hosted_ci_evidence.schema.json').read_text());errs=sorted(e.message for e in Draft202012Validator(schema).iter_errors(x))
 if errs:print(json.dumps({'status':'FAIL','errors':errs},indent=2));return 1
 if x['evidence_source']!='GITHUB_ACTIONS' or x['overall_status']!='PASS' or not all(j['status']=='PASS' for j in x['jobs']):print(json.dumps({'status':'FAIL','error':'Evidence is not a complete green hosted run.'},indent=2));return 1
 shutil.copy2(a.evidence,ROOT/'evidence/WP6_HOSTED_CI_EVIDENCE_INTAKE_TEMPLATE.json');print(json.dumps({'status':'PASS','next':'rerun build_wp6_gate2_audit.py and verifier'},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
