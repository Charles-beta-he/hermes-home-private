#!/usr/bin/env python3
"""No-argument cron wrapper for the daily full multi-model smoke check.

Phase 28: this single opt-in wrapper consumes the local provider-health gate
before running the Xiaomi/MiMo daily smoke. If the latest gate classifies the
job as `skip_provider_health_degraded`, the wrapper records a typed local skip
and exits 0 instead of burning a known-degraded provider call.
"""
from __future__ import annotations

import glob
import hashlib
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SAFE = SCRIPT_DIR / "multi-model-smoke-safe.py"
JOB_ID = "42baeebb646c"
JOB_NAME = "multi-model-smoke-daily-full"
DEFAULT_GATE_GLOB = str(Path.home() / ".hermes" / "hermes-agent" / "docs" / "private" / "workflow-kernel-cron-provider-health-gate" / "cron_provider_health_gate_*.json")
DEFAULT_SKIP_LEDGER = Path.home() / ".hermes" / "state" / "cron-provider-health-gate" / "provider_health_skips.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_safe():
    spec = importlib.util.spec_from_file_location("multi_model_smoke_safe", SAFE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def latest_gate_path(pattern: str = DEFAULT_GATE_GLOB) -> Path | None:
    override = os.environ.get("HERMES_CRON_HEALTH_GATE_REPORT")
    if override:
        p = Path(override)
        return p if p.exists() else None
    matches = [Path(p) for p in glob.glob(pattern)]
    return max(matches, key=lambda p: p.stat().st_mtime) if matches else None


def load_gate_decision(job_id: str = JOB_ID) -> dict[str, Any] | None:
    path = latest_gate_path()
    if not path:
        return None
    report = json.loads(path.read_text())
    for decision in report.get("decisions", []):
        if decision.get("job_id") == job_id:
            return {**decision, "gate_report": str(path), "gate_report_id": report.get("report_id")}
    return None


def skip_payload(decision: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "status": "provider_health_degraded_skip",
        "job_id": JOB_ID,
        "job_name": JOB_NAME,
        "created_at": utc_now(),
        "decision": decision,
        "external_side_effects": False,
        "model_generation_attempted": False,
        "cron_state_mutated": False,
    }
    payload["idempotency_key"] = hashlib.sha256(json.dumps({"job_id": JOB_ID, "gate_report_id": decision.get("gate_report_id"), "decision": decision.get("decision")}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    return payload


def append_skip(payload: dict[str, Any], ledger: Path | None = None) -> dict[str, Any]:
    target = ledger or Path(os.environ.get("HERMES_CRON_HEALTH_SKIP_LEDGER", str(DEFAULT_SKIP_LEDGER)))
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if target.exists():
        existing = [json.loads(line) for line in target.read_text().splitlines() if line.strip()]
        for row in existing:
            if row.get("idempotency_key") == payload.get("idempotency_key"):
                return {**row, "ledger": str(target), "deduped": True}
    with target.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return {**payload, "ledger": str(target), "deduped": False}


def should_skip_for_provider_health() -> dict[str, Any] | None:
    decision = load_gate_decision()
    if decision and decision.get("decision") == "skip_provider_health_degraded":
        return append_skip(skip_payload(decision))
    return None


def run_original() -> dict[str, Any]:
    mod = load_safe()
    return mod.run_smoke(
        script=str(SCRIPT_DIR / "multi-model-smoke.py"),
        script_args=["--timeout", "60"],
        timeout_s=300,
        log_file=str(Path.home() / ".hermes" / "logs" / "multi-model-smoke-daily-full-wrapper.jsonl"),
    )


def main() -> int:
    skip = should_skip_for_provider_health()
    payload = skip if skip else run_original()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
