#!/usr/bin/env python3
"""Local verifier for an OpenWiki pilot repository.

Read-only. It checks generated documentation shape and emits a JSON report.
It does not run OpenWiki, mutate git state, read .env files, or make network calls.
"""
from __future__ import annotations
import argparse, json, re, subprocess
from pathlib import Path
from datetime import datetime, timezone

SECRET_PATTERNS=[re.compile(p,re.I) for p in [r'api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{16,}', r'(secret|token|password)\s*[:=]\s*[^\s`]+']]

def run(cmd, cwd):
    try:
        p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=20)
        return {'command':' '.join(cmd),'exit_code':p.returncode,'stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:]}
    except Exception as e:
        return {'command':' '.join(cmd),'error':repr(e)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('repo', help='target repository path after an OpenWiki pilot run')
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args()
    root=Path(args.repo).expanduser().resolve()
    ow=root/'openwiki'
    quick=ow/'quickstart.md'
    pages=sorted(ow.rglob('*.md')) if ow.exists() else []
    findings=[]
    def add(sev, check, msg, path=None):
        findings.append({'severity':sev,'check':check,'message':msg,**({'path':str(path)} if path else {})})
    if not root.exists(): add('error','repo_exists','repo path missing',root)
    if not ow.exists(): add('error','openwiki_dir','openwiki/ missing',ow)
    if not quick.exists(): add('error','quickstart','openwiki/quickstart.md missing',quick)
    if len(pages)>12: add('warning','page_count',f'{len(pages)} markdown pages; review for thin-page sprawl',ow)
    thin=[]
    source_refs=0
    secret_hits=[]
    for p in pages:
        txt=p.read_text(encoding='utf-8',errors='replace')
        words=len(re.findall(r'\w+',txt))
        if words<120: thin.append(str(p.relative_to(root)))
        source_refs += len(re.findall(r'`[^`]+\.(ts|tsx|js|jsx|py|go|rs|java|kt|swift|md|json|ya?ml)`',txt))
        for pat in SECRET_PATTERNS:
            if pat.search(txt): secret_hits.append(str(p.relative_to(root)))
    if thin: add('warning','thin_pages','possible thin pages: '+', '.join(thin[:10]),ow)
    if pages and source_refs<5: add('warning','source_references',f'only {source_refs} inline source-like references detected',ow)
    if secret_hits: add('error','secret_like_text','secret-like patterns in docs: '+', '.join(sorted(set(secret_hits))[:10]),ow)
    for name in ['AGENTS.md','CLAUDE.md']:
        fp=root/name
        if fp.exists():
            txt=fp.read_text(encoding='utf-8',errors='replace')
            if 'OpenWiki quickstart' not in txt and 'openwiki/quickstart.md' not in txt:
                add('warning',name.lower(),'file exists but no OpenWiki quickstart reference detected',fp)
    git_status=run(['git','status','--short'],root) if (root/'.git').exists() else {'skipped':'not a git repository'}
    errors=sum(1 for f in findings if f['severity']=='error')
    warnings=sum(1 for f in findings if f['severity']=='warning')
    payload={'schema':'openwiki_pilot_verifier_v1','checked_at':datetime.now(timezone.utc).isoformat(),'repo':str(root),'ok':errors==0,'counts':{'errors':errors,'warnings':warnings,'pages':len(pages),'source_refs':source_refs},'findings':findings,'git_status':git_status}
    print(json.dumps(payload,ensure_ascii=False,indent=2) if args.json else payload)
    return 0 if errors==0 else 1
if __name__=='__main__':
    raise SystemExit(main())
