#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

def run(args, timeout=300):
    p = subprocess.run([sys.executable, *map(str, args)], cwd=str(SCRIPTS), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return p.returncode, p.stdout

def extract_json(text: str):
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch not in '[{':
            continue
        try:
            obj, end = decoder.raw_decode(text[i:])
            # prefer a JSON object that reaches near the end, but any valid object is useful
            return obj
        except Exception:
            continue
    return None

def emit_failure(label, rc, out):
    print(json.dumps({"status":"error", "label":label, "returncode":rc, "output":out[-4000:]}, ensure_ascii=False, indent=2))
    return 1

def main():
    rc, out = run([SCRIPTS / 'task_pool_guardian.py', 'run'])
    obj = extract_json(out)
    if rc != 0 or not isinstance(obj, dict):
        return emit_failure('task_pool_guardian', rc, out)
    if obj.get('status') == 'ok' and int(obj.get('issues_found') or 0) == 0 and int(obj.get('issues_fixed') or 0) == 0:
        return 0
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
