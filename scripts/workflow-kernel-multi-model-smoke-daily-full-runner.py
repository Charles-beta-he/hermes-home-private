#!/usr/bin/env python3
"""Scheduler-native workflow-kernel runner for the daily full multi-model smoke job.

Phase 43/44: daily-full scheduler-native target. It preserves the provider-health
gate behavior and supports plan-only verification through
HERMES_MULTI_MODEL_SMOKE_DAILY_PLAN_ONLY=1.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SAFE = SCRIPT_DIR / "multi-model-smoke-safe.py"
HERMES_AGENT_ROOT = Path.home() / ".hermes" / "hermes-agent"
if str(HERMES_AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_AGENT_ROOT))

from workflow_kernel import cron_wrappers as kernel_cron  # noqa: E402

JOB_ID = kernel_cron.DAILY_FULL_JOB_ID
JOB_NAME = kernel_cron.DAILY_FULL_JOB_NAME


def load_safe():
    spec = importlib.util.spec_from_file_location("multi_model_smoke_safe", SAFE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_original() -> dict:
    mod = load_safe()
    return mod.run_smoke(
        script=str(SCRIPT_DIR / "multi-model-smoke.py"),
        script_args=["--timeout", "60"],
        timeout_s=300,
        log_file=str(Path.home() / ".hermes" / "logs" / "workflow-kernel-multi-model-smoke-daily-full-runner.jsonl"),
    )


def main() -> int:
    skip = kernel_cron.daily_should_skip_for_provider_health()
    gate_decision = skip.get("decision") if skip and isinstance(skip.get("decision"), dict) else kernel_cron.load_gate_decision(JOB_ID)
    if skip:
        payload = dict(skip)
        payload["scheduler_native"] = True
        runtime_mode = "scheduler_native_provider_health_degraded_skip"
    elif os.environ.get("HERMES_MULTI_MODEL_SMOKE_DAILY_PLAN_ONLY") == "1":
        payload = {
            "status": "scheduler_native_daily_full_plan",
            "job_id": JOB_ID,
            "job_name": JOB_NAME,
            "script_args": ["--timeout", "60"],
            "model_generation_attempted": False,
            "cron_state_mutated": False,
            "scheduler_native": True,
            "provider_health_gate": {
                "gate_decision": gate_decision.get("decision") if gate_decision else None,
                "gate_report_id": gate_decision.get("report_id") if gate_decision else None,
            },
        }
        runtime_mode = "scheduler_native_plan_only"
    else:
        payload = run_original()
        payload["scheduler_native"] = True
        payload["provider_health_gate"] = {
            "gate_decision": gate_decision.get("decision") if gate_decision else None,
            "gate_report_id": gate_decision.get("report_id") if gate_decision else None,
        }
        runtime_mode = "scheduler_native_original_run"
    payload["wrapper_run_receipt"] = kernel_cron.record_wrapper_run_receipt(
        job_id=JOB_ID,
        job_name=JOB_NAME,
        payload=payload,
        gate_decision=gate_decision,
        runtime_mode=runtime_mode,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
