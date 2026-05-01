#!/usr/bin/env python3
"""Hermes Actual Usage Score — reproducible grade for multi-model use."""
from __future__ import annotations
import json, os, sqlite3, re, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
HOME=Path.home(); H=HOME/'.hermes'; DB=Path(os.environ.get('HERMES_ROUTE_DB_PATH', str(H/'route_outcomes.db'))).expanduser(); OUT=H/'state'/'usage-score.json'
ENSEMBLE=H/'logs'/'ensemble-votes.jsonl'; CROSS=H/'logs'/'cross-patch.jsonl'; RATIFY=H/'logs'/'ratify.jsonl'
TARGET_MODELS=['gpt-5.5','claude-opus-4-7','deepseek-v4-pro','mimo-v2.5-pro']; NOW=datetime.now(timezone.utc)
def parse_ts(s):
    if not s: return None
    try: return datetime.fromisoformat(str(s).replace('Z','+00:00'))
    except Exception: return None
def read_jsonl(path):
    if not path.exists(): return []
    out=[]
    for line in path.read_text(errors='ignore').splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out
def grade(score): return 'A' if score>=85 else 'B' if score>=70 else 'C' if score>=55 else 'D'
def model_from_chain(chain):
    try:
        data=json.loads(chain)
        if isinstance(data,list) and data: return str(data[0])
    except Exception: pass
    return str(chain or '').strip('[]"')
def rows(hours=24):
    if not DB.exists(): return []
    conn=sqlite3.connect(DB); conn.row_factory=sqlite3.Row; cutoff=(NOW-timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
    try: return [dict(r) for r in conn.execute("SELECT * FROM route_outcomes WHERE ts >= ? AND model_chain != ''", (cutoff,))]
    finally: conn.close()
def cron_stats():
    txt=''
    try:
        txt=subprocess.run(['bash', str(H/'scripts'/'p10-health.sh'), '--json'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30).stdout
        d=json.loads(txt)
        details=d.get('details',{})
        return {
            'score_raw':float(d.get('components',{}).get('cron_health',0.0)),
            'ok':int(details.get('cron_good', details.get('cron_recent_24h', 0))),
            'total':int(details.get('cron_total',0)),
            'recent_24h':int(details.get('cron_recent_24h',0)),
            'pending_first_run':int(details.get('cron_pending_first_run',0)),
            'bad':int(details.get('cron_bad',0)),
            'source':'p10-health-json'
        }
    except Exception:
        pass
    return {'score_raw':0.0,'ok':0,'total':0,'recent_24h':0,'pending_first_run':0,'bad':0,'source':'unknown'}
def compute():
    r24=rows(24); real24=[r for r in r24 if int(r.get('is_synthetic') or 0)==0]
    # Integrity is for real model/API calls, not hook bookkeeping rows. Hook routes
    # intentionally do not carry token/cost and would drown the signal.
    call_rows=[r for r in real24 if not str(r.get('route') or '').startswith('hook:')]
    integrity=[r for r in call_rows if (r.get('duration_s') or 0)>0 and (r.get('tokens_in') or 0)>0 and (r.get('tokens_out') or 0)>0 and (r.get('cost_usd') or 0)>0]
    models=sorted(set(model_from_chain(r.get('model_chain')) for r in integrity)); target_seen=[m for m in TARGET_MODELS if m in models]
    breadth_score=25*min(len(target_seen)/4,1); integrity_ratio=(len(integrity)/len(call_rows)) if call_rows else 0; integrity_score=15*min(integrity_ratio/0.95,1)
    # Route diversity should measure model-routed work, not single-session hook
    # bookkeeping. Hook rows are produced by the active conversation model and
    # are intentionally not fanned out across providers; including them would
    # turn a healthy single-agent tool trace stream into a false low-diversity
    # penalty and invite Goodhart-style synthetic route padding.
    diversity_rows=[]
    route_models={}
    for r in real24:
        route=r.get('route') or r.get('skill') or ''
        if not route or str(route).startswith('hook:'):
            continue
        diversity_rows.append(r)
        route_models.setdefault(route,set()).add(model_from_chain(r.get('model_chain')))
    hot=sorted(route_models.items(), key=lambda kv: len(kv[1]), reverse=True)[:10]; mean_div=(sum(min(len(s)/3,1) for _,s in hot)/len(hot)) if hot else 0; diversity_score=15*mean_div
    ens7=[e for e in read_jsonl(ENSEMBLE) if parse_ts(e.get('ts')) and parse_ts(e.get('ts')) >= NOW-timedelta(days=7)]
    ens_real=[]
    for e in ens7:
        ms=e.get('models') or []; providers=set()
        for m in ms:
            s=str(m); providers.add('openai-codex' if 'gpt' in s else 'anthropic' if 'claude' in s else 'deepseek' if 'deepseek' in s else 'xiaomi' if 'mimo' in s else s)
        if e.get('execute') is True and (e.get('total_voters') or e.get('votes_count') or 0)>=3 and len(providers)>=3: ens_real.append(e)
    ensemble_score=15*min(len(ens_real)/3,1)
    # Ratification corpus accepts both dedicated ratify logs and executed ensemble
    # records: an executed 3+ provider vote is a real cross-model ratification.
    cross7=[e for e in read_jsonl(CROSS)+read_jsonl(RATIFY) if parse_ts(e.get('ts')) and parse_ts(e.get('ts')) >= NOW-timedelta(days=7)]
    ratified=[e for e in cross7 if e.get('actual_model_calls') or e.get('execute') or e.get('ratified') or e.get('verdict') in ('pass','approved','certified')]
    ratified.extend(ens_real)
    ratify_score=10*min(len(ratified)/3,1); cs=cron_stats(); cron_score=10*min((cs.get('score_raw') or 0)/0.94,1)
    closure_events=0
    for p in [H/'logs'/'evolve.log', H/'logs'/'autonomous-evolution.jsonl', H/'logs'/'skill-steward.jsonl']:
        for e in read_jsonl(p):
            ts=parse_ts(e.get('ts') or e.get('timestamp'))
            if ts and ts >= NOW-timedelta(days=14) and (e.get('status') in ('ok','applied','promoted') or e.get('kept') or e.get('eval_result')=='kept'): closure_events+=1
    closure_score=10*min(closure_events/5,1)
    total=round(breadth_score+integrity_score+diversity_score+ensemble_score+ratify_score+cron_score+closure_score,2)
    return {'ts':NOW.strftime('%Y-%m-%dT%H:%M:%SZ'),'score':total,'grade':grade(total),'components':{'model_breadth_24h':{'score':round(breadth_score,2),'max':25,'target_seen':target_seen,'all_integrity_models':models},'real_call_integrity':{'score':round(integrity_score,2),'max':15,'ratio':round(integrity_ratio,3),'integrity_rows':len(integrity),'call_rows':len(call_rows),'excluded_hook_rows':len(real24)-len(call_rows)},'route_diversity':{'score':round(diversity_score,2),'max':15,'mean_normalized':round(mean_div,3),'routes':{k:sorted(v) for k,v in hot[:5]},'evaluated_rows':len(diversity_rows),'excluded_hook_rows':len(real24)-len(diversity_rows)},'ensemble_executed':{'score':round(ensemble_score,2),'max':15,'count_7d':len(ens_real)},'ratification_corpus':{'score':round(ratify_score,2),'max':10,'count_7d':len(ratified)},'cron_green':{'score':round(cron_score,2),'max':10,**cs},'self_evolution_closure':{'score':round(closure_score,2),'max':10,'closure_events_14d':closure_events}},'thresholds':{'A':85,'B':70,'C':55}}
def main():
    data=compute(); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(data,indent=2,ensure_ascii=False)); print(json.dumps(data,indent=2,ensure_ascii=False)); return 0 if data['grade']=='A' else 1
if __name__=='__main__': raise SystemExit(main())
