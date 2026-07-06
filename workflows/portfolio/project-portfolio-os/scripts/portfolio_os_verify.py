#!/usr/bin/env python3
"""Strict Portfolio OS verification.

Exits non-zero on any portfolio doctor error. Warnings remain visible but do not
block strict verification unless --fail-on-warning is supplied.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts" / "portfolio_doctor.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()
    proc = subprocess.run([sys.executable, str(DOCTOR), "--json"], text=True, capture_output=True, check=False)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"ok": False, "counts": {"error": 1, "warning": 0}, "findings": [{"severity": "error", "project": "portfolio", "check": "doctor_json", "message": proc.stdout[-1000:]}]}
    counts = payload.get("counts") or {}
    errors = int(counts.get("error") or 0)
    warnings = int(counts.get("warning") or 0)
    ok = proc.returncode == 0 and errors == 0 and (warnings == 0 or not args.fail_on_warning)
    result = {
        "schema": "portfolio_os_strict_verify_v1",
        "ok": ok,
        "doctor_ok": bool(payload.get("ok")),
        "doctor_returncode": proc.returncode,
        "counts": counts,
        "fail_on_warning": args.fail_on_warning,
        "doctor": payload,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
