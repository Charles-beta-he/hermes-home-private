#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess, sys, time
from pathlib import Path

H = Path.home() / '.hermes'
S = H / 'scripts'

def run(args, timeout=120):
    p = subprocess.run([sys.executable, *map(str, args)], cwd=str(S), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout

def parse_pass_rate(text: str):
    m = re.search(r'Overall:\s+total=\d+\s+pass=([0-9.]+)%', text)
    return float(m.group(1))/100 if m else None

def main() -> int:
    route_rc, route_out = run([S / 'route_store.py', 'summary'])
    eval_rc, eval_out = run([S / 'eval-harness.py', '--status'])
    staging = H / 'skills-staging'
    now = time.time()
    pending = []
    old = []
    if staging.exists():
        for p in staging.iterdir():
            if p.name.startswith('.'):
                continue
            pending.append(str(p.name))
            try:
                age_days = (now - p.stat().st_mtime) / 86400
                if age_days > 3:
                    old.append({'name': p.name, 'age_days': round(age_days, 1)})
            except OSError:
                pass
    pass_rate = parse_pass_rate(route_out)
    issues = []
    if route_rc != 0:
        issues.append({'type': 'route_store_error', 'output': route_out[-2000:]})
    if eval_rc != 0:
        issues.append({'type': 'eval_status_error', 'output': eval_out[-2000:]})
    if pass_rate is None:
        issues.append({'type': 'route_pass_rate_unknown'})
    elif pass_rate < 0.7:
        issues.append({'type': 'route_pass_rate_low', 'pass_rate': pass_rate})
    if old:
        issues.append({'type': 'staging_old', 'items': old})
    if len(pending) > 10:
        issues.append({'type': 'staging_backlog_large', 'count': len(pending), 'items': pending[:20]})
    if not issues:
        return 0
    print(json.dumps({
        'status': 'WARNING',
        'issues': issues,
        'route_pass_rate': pass_rate,
        'staging_count': len(pending),
        'route_summary_excerpt': route_out[:1200],
        'eval_status_excerpt': eval_out[:1200],
    }, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
