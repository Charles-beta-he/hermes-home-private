#!/usr/bin/env python3
"""No-argument cron wrapper for the 4h multi-model smoke check.

Hermes cron script injection treats the `script` field as a path, not a shell
command. Keep all arguments here so cron does not try to open
`multi-model-smoke-safe.py --flag ...` as a single filename.

Phase 29: this multi-provider wrapper consumes the local provider-health gate
and converts `run_with_degraded_provider_exclusions` into concrete model
selection args. It does not mutate cron state; it only excludes currently
degraded providers from this wrapper invocation.
"""
from __future__ import annotations

import glob
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SAFE = SCRIPT_DIR / "multi-model-smoke-safe.py"
JOB_ID = "2c14ca2a9bd2"
JOB_NAME = "multi-model-smoke-every-4h"
DEFAULT_GATE_GLOB = str(Path.home() / ".hermes" / "hermes-agent" / "docs" / "private" / "workflow-kernel-cron-provider-health-gate" / "cron_provider_health_gate_*.json")
MODEL_PROVIDER = {
    "gpt-5.5": "openai",
    "mimo-v2.5-pro": "xiaomi",
    "deepseek-v4-pro": "deepseek",
}
BASE_ARGS = ["--skip-claude", "--timeout", "45"]


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


def script_args_for_decision(decision: dict[str, Any] | None) -> tuple[list[str], dict[str, Any]]:
    args = list(BASE_ARGS)
    degraded = []
    if decision and decision.get("decision") == "run_with_degraded_provider_exclusions":
        degraded = [str(x) for x in decision.get("degraded_endpoints") or []]
        allowed_models = [model for model, provider in MODEL_PROVIDER.items() if provider not in set(degraded)]
        for model in allowed_models:
            args.extend(["--model", model])
    return args, {
        "gate_decision": decision,
        "degraded_endpoints_excluded": degraded,
        "selected_models": [args[i + 1] for i, item in enumerate(args[:-1]) if item == "--model"],
    }


def run_original(script_args: list[str]) -> dict[str, Any]:
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
    else:
        payload = run_original(script_args)
        payload["provider_health_gate"] = gate_meta
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
