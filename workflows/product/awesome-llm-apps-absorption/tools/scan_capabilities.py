#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

CATEGORY_ROOTS = {
    "agent_skills": "agent_skill",
    "starter_ai_agents": "starter_agent",
    "advanced_ai_agents": "advanced_agent",
    "always_on_agents": "always_on_agent",
    "generative_ui_agents": "generative_ui",
    "mcp_ai_agents": "mcp_agent",
    "rag_tutorials": "rag",
    "voice_ai_agents": "voice_agent",
    "advanced_llm_apps": "advanced_llm_app",
    "ai_agent_framework_crash_course": "framework_example",
}
TOKENS = {
    "rag": ["rag", "retrieval", "pdf", "document", "knowledge", "chat_with"],
    "research": ["research", "deep_research", "report"],
    "memory": ["memory", "mem0", "long_term"],
    "mcp_tools": ["mcp", "tool", "browser", "github"],
    "multi_agent": ["multi_agent", "team", "crew", "swarm"],
    "voice": ["voice", "speech", "audio", "call"],
    "monitoring": ["always_on", "monitor", "watch", "sentinel", "alert"],
    "finance": ["finance", "financial", "investment", "stock", "trading"],
    "data_analysis": ["sql", "data", "analytics", "csv"],
    "generative_ui": ["generative_ui", "frontend", "ui", "website"],
    "coding": ["code", "coding", "github", "developer"],
    "content": ["blog", "content", "youtube", "news", "social"],
}

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def slug(s): return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')

def classify(path: str):
    s = slug(path)
    hits=[]
    for cap, words in TOKENS.items():
        if any(slug(w) in s for w in words): hits.append(cap)
    return hits or ["general_agent"]

def discover(repo: Path):
    apps=[]
    for root_name, family in CATEGORY_ROOTS.items():
        root=repo/root_name
        if not root.exists(): continue
        for readme in root.rglob('README.md'):
            d=readme.parent
            if d == root: continue
            rel=d.relative_to(repo).as_posix()
            depth=len(d.relative_to(root).parts)
            if depth > 4: continue
            files=[p.name for p in d.iterdir() if p.is_file()]
            runnable=any(n in files for n in ('app.py','main.py','requirements.txt','pyproject.toml','package.json'))
            if not runnable: continue
            apps.append({
                'id': slug(rel), 'title': d.name.replace('_',' '), 'family': family,
                'path': rel, 'capabilities': classify(rel),
                'evidence': {'readme': f'{rel}/README.md', 'files': sorted(files)},
                'runtime_hint': 'python' if any(n.endswith('.py') for n in files) else ('node' if 'package.json' in files else 'unknown'),
                'verification_status': 'source_present_unexecuted'
            })
    seen={}
    for a in apps: seen[a['path']]=a
    return sorted(seen.values(), key=lambda x:x['path'])

def module(cap, rows):
    examples=[r['path'] for r in rows[:8]]
    return {
      'schema':'hermes_capability_module_v1','id':f'awesome_{cap}','title':cap.replace('_',' ').title(),'version':1,
      'kind':'composite_module','responsibility':f'Provide reusable {cap} capability distilled from reference applications.',
      'contracts':{
        'consumes':['intent','source_inputs','runtime_config'], 'produces':[cap+'_result','evidence_refs'],
        'input_contract':{'required':['intent'],'optional':['source_inputs','runtime_config']},
        'output_contract':{'produces':[cap+'_result','evidence_refs'],'evidence_required':True,'confidence_required':True},
        'presentation_contract':{'surfaces':['cli','markdown'],'style':'concise_evidence_first'}},
      'routing':{
        'applies_when':[cap, cap.replace('_',' '), f'user requests {cap} capability'],
        'does_not_apply_when':['simple answer needs no workflow','required source or runtime is unavailable and no degraded mode exists'],
        'positive_examples':examples[:3], 'negative_examples':['word-only request without matching capability intent'],
        'neighbor_modules':[], 'forbidden_triggers':['the word agent alone']},
      'authority':{'side_effects':'none','required_authority':[],'can_run_autonomously':True},
      'lifecycle':{'maturity':'candidate','retention':'project_scoped'},
      'metrics':{'usage_count':0,'success_count':0,'evidence_pass_rate':0.0,'false_trigger_count':0,'human_intervention_rate':0.0},
      'promotion_policy':{'promote_when':['two independent verified runs','negative cases pass'],'demote_when':['source drift','runtime contradiction'],'cleanup_when':['superseded','no usage before TTL']},
      'source_refs':examples,'cannot_prove':['upstream app runtime works','provider/API availability','production readiness']}

def foundational_module(mid, responsibility, consumes, produces, kind='atomic_module'):
    m = module(mid, [])
    m['id'] = mid
    m['title'] = mid.replace('_', ' ').title()
    m['kind'] = kind
    m['responsibility'] = responsibility
    m['contracts']['consumes'] = consumes
    m['contracts']['produces'] = produces
    m['contracts']['input_contract'] = {'required': consumes, 'optional': []}
    m['contracts']['output_contract']['produces'] = produces
    m['routing']['applies_when'] = [mid, responsibility]
    m['source_refs'] = ['local absorption workflow contract']
    return m

def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo',required=True); p.add_argument('--out',required=True); a=p.parse_args()
    repo,out=Path(a.repo),Path(a.out); out.mkdir(parents=True,exist_ok=True)
    apps=discover(repo); groups=defaultdict(list)
    for app in apps:
        for c in app['capabilities']: groups[c].append(app)
    commit=__import__('subprocess').check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    catalog={'schema':'awesome_llm_apps_capability_catalog_v1','generated_at':now(),'source':{'repo':'https://github.com/Shubhamsaboo/awesome-llm-apps','commit':commit},'app_count':len(apps),'apps':apps,'capability_counts':dict(sorted(Counter(c for x in apps for c in x['capabilities']).items()))}
    foundations = [
      foundational_module('source_evidence_collector','Collect pinned source identity and file/path evidence.',['source_ref'],['evidence_refs']),
      foundational_module('evidence_gate','Separate source claims, static implementation evidence, and runtime proof.',['evidence_refs'],['evidence_verdict'],'gate'),
      foundational_module('risk_modeler','Classify license, credential, provider, side-effect, and runtime risks.',['evidence_refs'],['risk_report']),
      foundational_module('intent_seed_capture','Normalize requested functions and target ownership boundary.',['seed'],['intent']),
      foundational_module('output_contract_builder','Build stable workflow outputs, closure states, and not-proven boundaries.',['intent'],['output_contract']),
    ]
    registry={'schema':'hermes_capability_module_registry_v1','source_commit':commit,'modules':foundations+[module(c,rows) for c,rows in sorted(groups.items())]}
    (out/'capability-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
    (out/'module_registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'ok','commit':commit,'app_count':len(apps),'module_count':len(registry['modules']),'outputs':[str(out/'capability-catalog.json'),str(out/'module_registry.json')]},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
