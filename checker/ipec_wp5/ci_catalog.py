from __future__ import annotations
from typing import Any
FORBIDDEN = ('git push','git tag','gh release create','gh release upload','zenodo upload','contents: write','pull-requests: write','packages: write','curl -x post')
def audit_catalog(catalog: dict[str, Any]) -> list[str]:
    errors=[]; jobs=catalog.get('jobs',[])
    if catalog.get('job_count')!=12 or len(jobs)!=12: errors.append('CI_JOB_COUNT_MISMATCH')
    ids=[j.get('job_id') for j in jobs]
    if len(ids)!=len(set(ids)): errors.append('DUPLICATE_CI_JOB_ID')
    if [j.get('sequence') for j in jobs] != list(range(1,13)): errors.append('CI_JOB_SEQUENCE_MISMATCH')
    known=set(ids); graph={j.get('job_id'):j.get('needs',[]) for j in jobs}
    for j in jobs:
        if j.get('write_permissions') is not False or j.get('upstream_mutation_authorized') is not False: errors.append('CI_WRITE_PERMISSION_FORBIDDEN')
        for dep in j.get('needs',[]):
            if dep not in known: errors.append('CI_UNKNOWN_DEPENDENCY')
        text='\n'.join(j.get('commands',[])).lower()
        if any(x in text for x in FORBIDDEN): errors.append('CI_REMOTE_MUTATION_COMMAND_FORBIDDEN')
    state={}
    def visit(n):
        if state.get(n)==1:return False
        if state.get(n)==2:return True
        state[n]=1
        for d in graph.get(n,[]):
            if not visit(d):return False
        state[n]=2;return True
    if not all(visit(n) for n in known): errors.append('CI_DEPENDENCY_CYCLE')
    return sorted(set(errors))
def audit_workflow_text(text: str, expected_job_ids: list[str]) -> list[str]:
    low=text.lower(); errors=[]
    if 'permissions:\n  contents: read' not in low: errors.append('WORKFLOW_GLOBAL_READ_PERMISSION_MISSING')
    for jid in expected_job_ids:
        if f'  {jid}:' not in text: errors.append(f'WORKFLOW_JOB_MISSING:{jid}')
    if any(x in low for x in FORBIDDEN): errors.append('WORKFLOW_REMOTE_MUTATION_COMMAND_FORBIDDEN')
    if low.count('uses: actions/upload-artifact@v4') < 1: errors.append('WORKFLOW_EVIDENCE_UPLOAD_MISSING')
    return sorted(set(errors))
