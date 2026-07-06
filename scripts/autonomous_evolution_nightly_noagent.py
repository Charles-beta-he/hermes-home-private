#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from hermes_evolution_store import EvolutionStore, classify_nightly_result

SCRIPT = Path.home() / ".hermes" / "scripts" / "autonomous-evolution-nightly.py"


def _tail(value: str | bytes | None, limit: int) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[-limit:]
    return value[-limit:]


def emit_payload(payload: dict) -> None:
    store = EvolutionStore()
    record = store.append_dream_run(payload)
    payload["dream_run_proof_hash"] = record.get("proof_hash")
    payload["dream_run_ledger"] = str(store.runs_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    try:
        p = subprocess.run([sys.executable, str(SCRIPT)], text=True, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        payload = {
            "schema": "autonomous_evolution_nightly_noagent_v1",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "timeout_recorded",
            "returncode": 124,
            "effective_audit": False,
            "state_advanced": False,
            "degraded": True,
            "write_blocked": False,
            "reasons": ["timeout_recorded", "subprocess_timeout"],
            "stdout_tail": _tail(exc.stdout, 3000).strip(),
            "stderr_tail": _tail(exc.stderr, 1000).strip(),
        }
        emit_payload(payload)
        return 0

    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    health = classify_nightly_result(p.returncode, out, err)
    payload = {
        "schema": "autonomous_evolution_nightly_noagent_v1",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": health["status"],
        "returncode": p.returncode,
        "effective_audit": health["effective_audit"],
        "state_advanced": health["state_advanced"],
        "degraded": health["degraded"],
        "write_blocked": health["write_blocked"],
        "reasons": health["reasons"],
        "stdout_tail": out[-3000:],
        "stderr_tail": err[-1000:],
    }
    emit_payload(payload)
    return 0 if health["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
