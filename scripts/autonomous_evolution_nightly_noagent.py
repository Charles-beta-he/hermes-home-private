#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import hermes_dreaming as hd
from hermes_evolution_store import EvolutionStore

SCRIPT = Path(__file__).with_name("autonomous-evolution-nightly.py")


def _tail(value: str | bytes | None, limit: int) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")[-limit:]
    return value[-limit:]


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"noagent-{stamp}-{uuid.uuid4().hex[:8]}"


def receipt_path_for_run(run_id: str) -> Path:
    """Per-run receipt path the child script is told to write to.

    Read fresh at call time (not at import time) so ``HERMES_HOME`` and
    ``HERMES_DREAMING_RECEIPT_PATH`` overrides set by callers/tests after
    import still take effect. A fresh, unique path per ``run_id`` means a
    stale receipt left over from a previous run can never be mistaken for
    this run's evidence.
    """
    override = os.environ.get("HERMES_DREAMING_RECEIPT_PATH")
    if override:
        return Path(override)
    home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
    return home / "state" / "dreaming" / "receipts" / f"{run_id}.json"


def emit_payload(payload: dict) -> None:
    store = EvolutionStore()
    if hd.dreaming_write_boundary_preflight(store.home, store.runs_path) is None:
        record = store.append_dream_run(payload)
        payload["dream_run_proof_hash"] = record.get("proof_hash")
        payload["dream_run_ledger"] = str(store.runs_path)
    else:
        payload["dream_run_proof_hash"] = None
        payload["dream_run_ledger"] = None
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    run_id = new_run_id()
    receipt_path = receipt_path_for_run(run_id)
    env = dict(os.environ)
    env["HERMES_DREAMING_RECEIPT_PATH"] = str(receipt_path)
    env["HERMES_DREAMING_RUN_ID"] = run_id

    try:
        p = subprocess.run(
            [sys.executable, str(SCRIPT)], text=True, capture_output=True, timeout=300, env=env
        )
    except subprocess.TimeoutExpired as exc:
        payload = {
            "schema": "autonomous_evolution_nightly_noagent_v1",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "ERROR",
            "returncode": 124,
            "job_success": False,
            "effective_audit": False,
            "candidate_generated": False,
            "state_advanced": False,
            "promoted": False,
            "degraded": True,
            "write_blocked": False,
            "reasons": ["timeout_recorded", hd.REASON_SUBPROCESS_TIMEOUT],
            "receipt_source": None,
            "candidate_artifact": None,
            "run_id": run_id,
            "stdout_tail": _tail(exc.stdout, 3000).strip(),
            "stderr_tail": _tail(exc.stderr, 1000).strip(),
        }
        emit_payload(payload)
        return 2
    except Exception:
        # Spawn/runtime failures are data, not terminal exceptions. Never
        # include exception messages or tracebacks in the payload or ledger.
        payload = {
            "schema": "autonomous_evolution_nightly_noagent_v1",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "ERROR",
            "returncode": 2,
            "job_success": False,
            "effective_audit": False,
            "candidate_generated": False,
            "state_advanced": False,
            "promoted": False,
            "degraded": True,
            "write_blocked": False,
            "reasons": [hd.REASON_UNEXPECTED_EXCEPTION],
            "receipt_source": None,
            "candidate_artifact": None,
            "run_id": run_id,
            "stdout_tail": "",
            "stderr_tail": "",
        }
        emit_payload(payload)
        return 2

    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    # Typed receipt is the only progress evidence. Missing, invalid,
    # malformed, or mismatched receipts all fail closed; stdout is diagnostic
    # text only and cannot upgrade health.
    health = hd.classify_run_result(p.returncode, out, err, receipt_path, expected_run_id=run_id)
    if health.get("state_advanced") or health.get("promoted"):
        # Loop A is candidate-only. Even a schema-valid receipt cannot grant
        # itself advancement/promotion authority.
        health = {
            "status": "ERROR",
            "job_success": False,
            "effective_audit": False,
            "candidate_generated": False,
            "state_advanced": False,
            "promoted": False,
            "degraded": True,
            "write_blocked": True,
            "reasons": [hd.REASON_RECEIPT_INVALID],
            "receipt_source": "receipt_rejected",
            "target": health.get("target"),
            "candidate_artifact": None,
        }
    artifact = health.get("candidate_artifact")
    if not health.get("job_success") or p.returncode != 0:
        artifact = None
    payload = {
        "schema": "autonomous_evolution_nightly_noagent_v1",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": health["status"],
        "returncode": p.returncode,
        "job_success": health["job_success"],
        "effective_audit": health["effective_audit"],
        "candidate_generated": health.get("candidate_generated", False),
        "state_advanced": health["state_advanced"],
        "promoted": health.get("promoted", False),
        "degraded": health["degraded"],
        "write_blocked": health["write_blocked"],
        "reasons": health["reasons"],
        "receipt_source": health.get("receipt_source"),
        "target": health.get("target"),
        "candidate_artifact": artifact,
        "run_id": run_id,
        "stdout_tail": out[-3000:],
        "stderr_tail": err[-1000:],
    }
    emit_payload(payload)
    return 0 if health["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
