#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1];SD=ROOT/'schemas/v0.1';OUT=SD/'schema_bundle_manifest.json'
def build():
 files={}
 for p in sorted(SD.glob('*.schema.json')):
  x=json.loads(p.read_text());Draft202012Validator.check_schema(x);files[p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'id':x['$id']}
 return {'artifact_id':'V0_IPEC_WP6_SCHEMA_BUNDLE','contract_id':'V0-IPEC-0.1','version':'0.1','date':'2026-07-19','baseline_wp5_schema_count':21,'wp6_added_schema_count':4,'post_merge_added_schema_count':3,'schema_count':len(files),'files':files}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();o=build();t=json.dumps(o,indent=2)+'\n'
 if a.check:
  if not OUT.exists() or OUT.read_text()!=t:print(json.dumps({'status':'FAIL','error':'schema manifest drift'},indent=2));return 1
 else:OUT.write_text(t)
 print(json.dumps({'status':'PASS','schema_count':o['schema_count']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
