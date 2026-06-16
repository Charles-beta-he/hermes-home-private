#!/usr/bin/env python3
import json, sys
from pathlib import Path

path = Path(__file__).with_name('module-registry.json')
data = json.loads(path.read_text())
assert data['schema'] == 'open_source_absorption_module_registry_v1'
modules = data['modules']
assert len(modules) == 18, f"expected 18 modules, got {len(modules)}"
ids = [m['id'] for m in modules]
assert len(ids) == len(set(ids)), 'module ids must be unique'
missing=[]
for m in modules:
    for r in m.get('representative_tasks', []):
        p = Path(r['path'])
        if not p.exists():
            missing.append(str(p))
if missing:
    raise SystemExit('missing representative task paths:\n' + '\n'.join(missing[:20]))
summary = data['summary']
assert summary['matched_task_refs'] >= summary['primary_task_refs'] >= 1
assert summary['modules'] == 18
print(json.dumps({
    'ok': True,
    'modules': len(modules),
    'matched_task_refs': summary['matched_task_refs'],
    'primary_task_refs': summary['primary_task_refs'],
    'support_task_refs': summary['support_task_refs'],
    'nonempty_modules': sum(1 for m in modules if m.get('task_ref_count', 0) > 0)
}, ensure_ascii=False, indent=2))
