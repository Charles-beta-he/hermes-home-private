#!/usr/bin/env python3
"""No-argument cron wrapper for the 4h multi-model smoke check.

Phase 31: provider-health gate consumption has moved into the workflow kernel
compatibility shim. This wrapper remains the opt-in cron entrypoint and keeps
all arguments explicit so Hermes cron treats `script` as a path, not a shell
command.
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

JOB_ID = kernel_cron.EVERY4H_JOB_ID
JOB_NAME = kernel_cron.EVERY4H_JOB_NAME
DEFAULT_GATE_GLOB = kernel_cron.DEFAULT_GATE_GLOB
MODEL_PROVIDER = kernel_cron.EVERY4H_MODEL_PROVIDER
BASE_ARGS = kernel_cron.EVERY4H_BASE_ARGS
latest_gate_path = kernel_cron.latest_gate_path


def load_gate_decision(job_id: str = JOB_ID) -> dict | None:
    return kernel_cron.load_gate_decision(job_id)


def script_args_for_decision(decision: dict | None) -> tuple[list[str], dict]:
    return kernel_cron.every4h_script_args_for_decision(decision)


def load_safe():
    spec = importlib.util.spec_from_file_location("multi_model_smoke_safe", SAFE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def run_original(script_args: list[str]) -> dict:
    mod = load_safe()
    return mod.run_smoke(
        script=str(SCRIPT_DIR / "multi-model-smoke.py"),
        script_args=script_args,
        timeout_s=210,
        log_file=str(Path.home() / ".hermes" / "logs" / "multi-model-smoke-every4h-wrapper.jsonl"),
    )


def main() -> int:
    decision = load_gate_decision()
    script_args, gate_meta = script_args_for_decision(decision)
    if os.environ.get("HERMES_MULTI_MODEL_SMOKE_EVERY4H_PLAN_ONLY") == "1":
        payload = {"status": "provider_health_exclusion_plan", "job_id": JOB_ID, "job_name": JOB_NAME, "script_args": script_args, "model_generation_attempted": False, "cron_state_mutated": False, **gate_meta}
        runtime_mode = "plan_only"
    else:
        payload = run_original(script_args)
        payload["provider_health_gate"] = gate_meta
        runtime_mode = "provider_exclusion_or_original_run"
    payload["wrapper_run_receipt"] = kernel_cron.record_wrapper_run_receipt(
        job_id=JOB_ID,
        job_name=JOB_NAME,
        payload=payload,
        gate_decision=decision,
        runtime_mode=runtime_mode,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
