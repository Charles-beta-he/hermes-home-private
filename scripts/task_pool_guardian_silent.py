#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run(args, timeout=300):
    proc = subprocess.Popen(
        [sys.executable, *map(str, args)],
        cwd=str(SCRIPTS),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, out or ""
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            out, _ = proc.communicate(timeout=5)
            stdout += out or ""
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
            try:
                out, _ = proc.communicate(timeout=2)
                stdout += out or ""
            except Exception:
                pass
        payload = {
            "status": "error",
            "label": "task_pool_guardian",
            "returncode": 124,
            "reason": "subprocess_timeout",
            "timeout_seconds": timeout,
            "output": stdout[-4000:],
        }
        return 124, json.dumps(payload, ensure_ascii=False, indent=2)


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
    print(json.dumps({"status": "error", "label": label, "returncode": rc, "output": out[-4000:]}, ensure_ascii=False, indent=2))
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
