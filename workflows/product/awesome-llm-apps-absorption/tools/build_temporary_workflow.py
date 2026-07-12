#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path

def toks(s): return {x for x in re.split(r'[^a-z0-9\u4e00-\u9fff]+',s.lower()) if len(x)>1}
def score(query, module):
    q=toks(query); routing=module.get('routing',{})
    hay=' '.join(routing.get('applies_when',[])+module.get('contracts',{}).get('produces',[])+[module.get('id',''),module.get('responsibility','')])
    h=toks(hay)
    exact=len(q & h)*3
    substr=sum(1 for a in q for b in h if len(a)>=3 and (a in b or b in a))
    return exact+substr

def main():
    p=argparse.ArgumentParser(); p.add_argument('--registry',required=True); p.add_argument('--query',required=True); p.add_argument('--out',required=True); p.add_argument('--top',type=int,default=5); a=p.parse_args()
    reg=json.loads(Path(a.registry).read_text())
    foundations=['intent_seed_capture','source_evidence_collector','risk_modeler','output_contract_builder','evidence_gate']
    byid={m['id']:m for m in reg['modules']}
    domain=[]
    for m in reg['modules']:
        if m['id'] in foundations: continue
        s=score(a.query,m)
        if s: domain.append((s,m))
    domain=sorted(domain,key=lambda x:(-x[0],x[1]['id']))[:a.top]
    selected=[byid[x] for x in foundations if x in byid]+[m for _,m in domain]
    nodes=[]
    for i,m in enumerate(selected):
        nodes.append({'id':m['id'],'kind':m['kind'],'responsibility':m['responsibility'],'depends_on':[selected[i-1]['id']] if i else [],'consumes':m['contracts']['consumes'],'produces':m['contracts']['produces'],'source_refs':m.get('source_refs',[])[:5]})
    result={
      'schema':'hermes_temporary_capability_workflow_v1','id':'tmp-awesome-llm-apps-functional-absorption',
      'maturity':'temporary_candidate','query':a.query,'created_at':datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z'),
      'source':{'repo':'https://github.com/Shubhamsaboo/awesome-llm-apps','commit':reg.get('source_commit')},
      'objective':'Recommend source-backed capability families and compose a local-only absorption workflow.',
      'inputs':['requested_function','target_environment','acceptance_boundary'],
      'outputs':['recommended_capabilities','source_evidence','risk_report','replication_plan','evidence_verdict'],
      'nodes':nodes,'edges':[{'from':n['depends_on'][0],'to':n['id']} for n in nodes if n['depends_on']],
      'gates':[
        {'id':'source_identity_gate','outcomes':{'pass':'continue','warn':'continue_with_warning','fail':'stop','blocked':'human_gate'}},
        {'id':'license_dependency_gate','outcomes':{'pass':'continue','warn':'isolate_or_rewrite','fail':'reject_import','blocked':'human_gate'}},
        {'id':'runtime_evidence_gate','outcomes':{'pass':'candidate_for_replication','warn':'static_evidence_only','fail':'demote','blocked':'credential_or_provider_gate'}}],
      'closure_states':['recommended','static_evidence_only','runtime_verified','blocked','rejected'],
      'side_effects':{'external':False,'cron':False,'taskpool':False,'agentos':False,'publish':False,'destructive':False},
      'cannot_prove':['selected upstream examples run locally','external provider availability','production readiness'],
      'recommendation_scores':[{'module':m['id'],'score':s} for s,m in domain]
    }
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'ok','selected_modules':[m['id'] for m in selected],'out':str(out),'side_effects':result['side_effects']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
