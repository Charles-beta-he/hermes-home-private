#!/usr/bin/env python3
"""End-to-end local Workflow Kernel Loop orchestrator.

Runs the safe local loop:
seed -> assetization decision -> module graph plan -> optional local workflow
asset scaffold -> usage ledger -> synthesis candidates.

This file is intentionally local-only. It does not enable external dispatch,
cron, taskpool lifecycle mutation, AgentOS runtime mutation, memory writes,
publish/deploy/push, destructive actions, payments, or credential entry.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIDE_EFFECTS_DISABLED = {"external": False, "cron": False, "taskpool": False, "agentos": False}
KILL_SWITCH = "HERMES_WORKFLOW_LOOP_DISABLE"
BUDGETS = {
    "max_iterations": 3,
    "max_runtime_seconds": 120,
    "max_retries": 2,
    "max_evidence_files": 64,
}
STAGE_IDS = ("observe", "orient", "compile", "simulate", "execute", "verify", "ratchet", "monitor", "cleanup")
CONTROL_MOVES = ("discovery", "handoff", "verification", "persistence", "scheduling")
SYSTEM_PARTS = ("automations", "worktrees", "skills", "connectors", "subagents", "memory")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_script(name: str):
    path = Path.home() / ".hermes" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_id(seed: str) -> str:
    asset_decision = _load_script("workflow_asset_decision")
    return asset_decision.stable_id(seed + "|" + utc_now() + "|" + uuid.uuid4().hex, "wfl")


def root_paths(root: Path) -> dict[str, Path]:
    return {
        "runs": root / "runs",
        "assets": root / "assets",
        "module_pool": root / "module-pool",
        "registry": root / "module-pool" / "module_registry.json",
        "ledger": root / "module-pool" / "usage_ledger.jsonl",
    }


def _run_loop_once_v1(
    seed: str,
    root: Path | None = None,
    observed_repetition: int = 0,
    task_scope: str = "unknown",
) -> dict[str, Any]:
    root = root or (Path.home() / ".hermes" / "workflows" / "workflow-kernel-loop")
    paths = root_paths(root)
    asset_decision = _load_script("workflow_asset_decision")
    module_pool = _load_script("workflow_module_pool")

    ctx: dict[str, Any] = {"observed_repetition": observed_repetition}
    if task_scope == "one_off":
        ctx["task_scope"] = "one_off"
    decision = asset_decision.decide_assetization(seed, ctx)
    registry = module_pool.load_registry(paths["registry"])
    plan = module_pool.plan_workflow_from_seed(seed, registry)

    run_dir = paths["runs"] / _run_id(seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / "decision.json", decision)
    _write_json(run_dir / "module-plan.json", plan)

    asset_receipt = None
    asset_workdir = None
    if decision["decision"] in {"project_scoped_candidate", "reusable_candidate"}:
        asset = asset_decision.compile_workflow_asset(decision)
        asset["source"]["module_plan_ref"] = str(run_dir / "module-plan.json")
        asset["source"]["module_ids"] = plan.get("selected_modules", [])
        asset["source"]["missing_capability_needs"] = plan.get("missing_capability_needs", [])
        asset_receipt = asset_decision.scaffold_workspace(asset, paths["assets"])
        asset_workdir = asset_receipt["workdir"]
        _write_json(run_dir / "asset-receipt.json", asset_receipt)

    module_ids = plan.get("selected_modules") or plan.get("capability_needs") or ["intent_seed_capture"]
    event = module_pool.usage_event(
        workflow_id=decision["id"],
        module_ids=module_ids,
        outcome="success" if decision["decision"] != "no_asset" else "ignored",
        evidence_passed=decision["decision"] in {"project_scoped_candidate", "reusable_candidate"},
        human_intervention=False,
        false_trigger=False,
    )
    module_pool.append_jsonl(paths["ledger"], event)

    receipt = {
        "schema": "hermes_workflow_kernel_loop_receipt_v1",
        "status": "ok",
        "seed": seed,
        "decision": decision["decision"],
        "run_dir": str(run_dir),
        "asset_workdir": asset_workdir,
        "module_plan_ref": str(run_dir / "module-plan.json"),
        "usage_ledger": str(paths["ledger"]),
        "side_effects": dict(SIDE_EFFECTS_DISABLED),
        "created_at": utc_now(),
    }
    _write_json(run_dir / "loop-receipt.json", receipt)
    return receipt


def run_loop_once(
    seed: str,
    root: Path | None = None,
    observed_repetition: int = 0,
    task_scope: str = "unknown",
) -> dict[str, Any]:
    """Run the evidence-complete v2 kernel while preserving the v1 CLI surface."""
    v2 = _load_script("workflow_kernel_loop_v2")
    effective_root = root or (Path.home() / ".hermes" / "workflows" / "workflow-kernel-loop")
    return v2.run_loop_once(seed, effective_root, observed_repetition, task_scope)


def synthesize_from_root(root: Path | None = None) -> dict[str, Any]:
    root = root or (Path.home() / ".hermes" / "workflows" / "workflow-kernel-loop")
    paths = root_paths(root)
    module_pool = _load_script("workflow_module_pool")
    events = module_pool.read_jsonl(paths["ledger"])
    candidates = module_pool.synthesize_module_candidates(events)
    result = {
        "schema": "hermes_workflow_kernel_synthesis_result_v1",
        "status": "ok",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "side_effects": dict(SIDE_EFFECTS_DISABLED),
        "ledger": str(paths["ledger"]),
    }
    _write_json(root / "module-pool" / "synthesis-candidates.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local Workflow Kernel Loop")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_once = sub.add_parser("run-once")
    p_once.add_argument("--seed", required=True)
    p_once.add_argument("--root", default=str(Path.home() / ".hermes" / "workflows" / "workflow-kernel-loop"))
    p_once.add_argument("--observed-repetition", type=int, default=0)
    p_once.add_argument("--task-scope", choices=["unknown", "one_off"], default="unknown")
    p_synth = sub.add_parser("synthesize")
    p_synth.add_argument("--root", default=str(Path.home() / ".hermes" / "workflows" / "workflow-kernel-loop"))
    args = parser.parse_args(argv)
    if args.cmd == "run-once":
        print(json.dumps(run_loop_once(args.seed, Path(args.root), args.observed_repetition, args.task_scope), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "synthesize":
        print(json.dumps(synthesize_from_root(Path(args.root)), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
