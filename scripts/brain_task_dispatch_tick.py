#!/usr/bin/env python3
"""Safe local-brain task dispatch tick.

This is normally a control-plane tick, not an autonomous executor:
- ingests Obsidian inbox drafts into canonical task notes;
- reconciles stale leases/expired tasks/due retries;
- regenerates derived dashboards;
- emits a dispatch hint for the next dispatchable task;
- records a JSONL proof log.

It never executes task Markdown or arbitrary hooks.  With explicit --autorun-step,
it may run the bounded static runner and proof-gated review->done closer.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TZ = timezone(timedelta(hours=8))
SCRIPT_DIR = Path(__file__).resolve().parent
HOME = Path.home()
SCRIPT = SCRIPT_DIR / "brain_task_orchestrator.py"
AUTORUN_STEP_SCRIPT = SCRIPT_DIR / "brain_task_autorun_step.py"
AGENT_TEAM_SCRIPT = SCRIPT_DIR / "agent_team_controller.py"
MODEL_QUOTA_SCRIPT = SCRIPT_DIR / "model_quota.py"
STATE_DIR = Path(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_STATE_DIR", str(HOME / ".hermes" / "state"))).expanduser()
LOG_DIR = Path(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_LOG_DIR", str(HOME / ".hermes" / "logs"))).expanduser()
STATE_FILE = STATE_DIR / "brain_task_dispatch_tick_state.json"
LOG_FILE = LOG_DIR / "brain_task_dispatch_tick.jsonl"
API_QUOTA_CACHE_FILE = STATE_DIR / "taskpool-api-quota-cache.json"
BATCH_MERGE_PLAN_DIR = STATE_DIR / "taskpool-batch-merge-plans"
BATCH_EXECUTOR_STATE_DIR = STATE_DIR / "taskpool-batch-executor"
DEFAULT_COMMAND_TIMEOUT_SECONDS = 120.0
DEFAULT_TERMINATE_GRACE_SECONDS = 5.0


def positive_float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def command_timeout_seconds() -> float:
    return positive_float_env("HERMES_BRAIN_DISPATCH_TICK_COMMAND_TIMEOUT_SECONDS", DEFAULT_COMMAND_TIMEOUT_SECONDS)


def terminate_grace_seconds() -> float:
    return positive_float_env("HERMES_BRAIN_DISPATCH_TICK_TERMINATE_GRACE_SECONDS", DEFAULT_TERMINATE_GRACE_SECONDS)


def _timeout_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _signal_process_group(proc: subprocess.Popen[Any], sig: int) -> bool:
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, sig)
        return True
    except ProcessLookupError:
        return True
    except Exception:
        return False


def _terminate_process_tree(proc: subprocess.Popen[Any]) -> bool:
    """Terminate a timed-out command and its process group.

    Multi-model steps can spawn long-running child model calls. Killing only the
    immediate process leaves orphan consult_models.py children running. Starting
    commands in a new session and killing the process group keeps timeout
    handling fail-closed and resource-safe.
    """
    if _signal_process_group(proc, signal.SIGTERM):
        return True
    try:
        proc.terminate()
    except Exception:
        try:
            proc.kill()
        except Exception:
            return False
    return False


def _kill_process_tree(proc: subprocess.Popen[Any]) -> bool:
    if _signal_process_group(proc, signal.SIGKILL):
        return True
    try:
        proc.kill()
        return False
    except Exception:
        return False


def iso() -> str:
    return datetime.now(TZ).replace(microsecond=0).isoformat()


def run_json(args: list[str]) -> dict[str, Any]:
    cmd = [sys.executable, str(SCRIPT), *args]
    return run_cmd_json(cmd)


def run_orchestrator_json(args: list[str], *, timeout: float | None = None) -> dict[str, Any]:
    cmd = [sys.executable, str(SCRIPT), *args]
    return run_cmd_json(cmd, timeout=timeout)


def parallel_claim_timeout_seconds() -> float:
    return positive_float_env("HERMES_BRAIN_DISPATCH_TICK_PARALLEL_CLAIM_TIMEOUT_SECONDS", 300.0)


def run_parallel_claim_and_handoff(args: list[str]) -> dict[str, Any]:
    """Run the mutating parallel claim bridge with a claim-specific timeout.

    `parallel-claim-and-handoff --write` rewrites task notes and emits handoff
    artifacts. Large, repeatedly retried task notes can legitimately take longer
    than the generic per-subcommand tick timeout; timing out here is especially
    bad because the subprocess can be killed after some claims have already been
    written. Keep the timeout bounded but large enough for the claim phase, while
    worker consumption remains separately bounded/backgrounded.
    """
    return run_orchestrator_json(args, timeout=max(command_timeout_seconds(), parallel_claim_timeout_seconds()))


def run_agent_team_json(args: list[str], *, timeout: float | None = None) -> dict[str, Any]:
    cmd = [sys.executable, str(AGENT_TEAM_SCRIPT), *args]
    return run_cmd_json(cmd, timeout=timeout)


def cleanup_event_worker_timeout_claims(claimed_items: list[dict[str, Any]], *, actor: str = "hermes-parallel") -> dict[str, Any]:
    """Release a just-claimed batch when the event worker trigger times out.

    `parallel-claim-and-handoff` mutates task notes to `claimed` before the
    controller process starts workers. If that controller process is killed by
    the tick timeout, any items it had not yet promoted to `running` remain as
    claim-only wedges. Treat the timeout as no trustworthy worker proof and move
    every still claim-bound item from the batch back to retry with structured
    evidence; already-finished/review items are skipped by the lifecycle gate.
    """
    released: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in claimed_items:
        if not isinstance(item, dict):
            skipped.append({"task_id": "", "reason": "invalid_claim_payload"})
            continue
        task_id = str(item.get("task_id") or item.get("id") or "").strip()
        if not task_id or task_id in seen:
            skipped.append({"task_id": task_id, "reason": "missing_or_duplicate_task_id"})
            continue
        seen.add(task_id)
        result = run_json([
            "transition",
            task_id,
            "--to",
            "retry",
            "--actor",
            actor,
            "--authority",
            "claim-and-handoff",
            "--reason",
            "event worker trigger timed out; killed worker group; release claim-bound batch for proof-gated retry",
            "--evidence",
            "command:brain_task_dispatch_tick event_worker_trigger_timeout_cleanup",
            "--delay-minutes",
            "5",
            "--force",
            "--json",
        ])
        entry = {"task_id": task_id, "transition": result, "to_status": "retry" if result.get("ok") else "unchanged"}
        if result.get("ok"):
            released.append(entry)
        else:
            skipped.append(entry)
    return {
        "status": "OK" if not skipped else "WARN",
        "reason": "event_worker_trigger_timeout_cleanup",
        "attempted_count": len(seen),
        "released_count": len(released),
        "released": released,
        "skipped": skipped,
        "safety": "timeout cleanup prevents claimed-without-running wedges; no task marked done",
    }


def run_cmd_json(cmd: list[str], timeout: float | None = None) -> dict[str, Any]:
    timeout = float(timeout if timeout is not None else command_timeout_seconds())
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process_group_terminated = _terminate_process_tree(proc)
        process_group_killed = False
        try:
            out, err = proc.communicate(timeout=terminate_grace_seconds())
        except subprocess.TimeoutExpired:
            process_group_killed = _kill_process_tree(proc)
            out, err = proc.communicate()
        return {
            "status": "ERROR",
            "cmd": cmd,
            "returncode": "timeout",
            "timeout_seconds": timeout,
            "terminate_grace_seconds": terminate_grace_seconds(),
            "stdout": _timeout_output(out)[-4000:],
            "stderr": _timeout_output(err)[-4000:],
            "reason": "subprocess_timeout",
            "process_group_terminated": process_group_terminated,
            "process_group_killed": process_group_killed,
        }
    out = (out or "").strip()
    err = (err or "").strip()
    try:
        data = json.loads(out) if out else {"status": "OK"}
    except Exception as exc:
        data = {"status": "ERROR", "cmd": cmd, "returncode": proc.returncode, "stdout": out, "stderr": err, "parse_error": str(exc)}
    if not isinstance(data, dict):
        data = {"status": "ERROR", "cmd": cmd, "returncode": proc.returncode, "stdout": out, "stderr": err, "parse_error": "json payload is not an object"}
    data.setdefault("cmd", cmd)
    data.setdefault("returncode", proc.returncode)
    if proc.returncode != 0:
        data.setdefault("reported_status", data.get("status"))
        data["status"] = "ERROR"
        data.setdefault("stdout", out)
        data.setdefault("stderr", err)
    return data


def load_state() -> dict[str, Any]:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _compact_for_tick_log(value: Any, *, depth: int = 0) -> Any:
    """Return a bounded JSONL-safe projection for dispatch tick logs.

    Full tick events can contain every task body plus evidence-spine payloads;
    appending those on every cron tick turns a health log into a multi-GB hot
    file.  Keep operational counters/statuses in JSONL and let detailed proof
    remain in task notes, handoff files, and explicit artifacts.
    """
    if depth > 5:
        return "<max_depth>"
    if isinstance(value, str):
        if len(value) > 1200:
            return value[:1200] + f"...<truncated {len(value) - 1200} chars>"
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        limit = 30
        items = [_compact_for_tick_log(item, depth=depth + 1) for item in value[:limit]]
        if len(value) > limit:
            items.append({"truncated_count": len(value) - limit})
        return items
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            k = str(key)
            if k in {"body", "description", "prompt", "stdout", "stderr"}:
                out[k] = _compact_for_tick_log(item, depth=depth + 1)
                continue
            if k in {"claims", "evidence"} and isinstance(item, list) and depth <= 2:
                out[k + "_count"] = len(item)
                continue
            if k == "rows" and isinstance(item, list):
                rows: list[Any] = []
                for row in item[:20]:
                    if isinstance(row, dict):
                        rows.append({
                            rk: _compact_for_tick_log(row.get(rk), depth=depth + 1)
                            for rk in ("id", "title", "status", "priority", "lane", "project", "claimed_by", "claim_expires_at", "stale_claim")
                            if rk in row
                        })
                    else:
                        rows.append(_compact_for_tick_log(row, depth=depth + 1))
                if len(item) > 20:
                    rows.append({"truncated_count": len(item) - 20})
                out[k] = rows
                continue
            out[k] = _compact_for_tick_log(item, depth=depth + 1)
        return out
    return str(value)


def append_log(event: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = event if os.environ.get("HERMES_BRAIN_DISPATCH_TICK_FULL_LOG", "").strip().lower() in {"1", "true", "yes", "on"} else _compact_for_tick_log(event)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _add_readiness_blocker(blockers: list[dict[str, Any]], reason: str, *, actual: Any = None, required: Any = None, severity: str = "blocker") -> None:
    item: dict[str, Any] = {"reason": reason, "severity": severity}
    if actual is not None:
        item["actual"] = actual
    if required is not None:
        item["required"] = required
    blockers.append(item)


def concurrency_readiness_snapshot(
    *,
    requested_agents: int,
    selected_count: int,
    active_count: int,
    resource_probe: dict[str, Any],
    claim_state: dict[str, Any] | None = None,
    boundary_warning_count: int = 0,
    runtime_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a read-only fail-closed verdict for future concurrency raises.

    This is an observability/guard contract only.  It does not mutate config,
    task lifecycle state, dispatch selection, or provider cache.  It answers:
    "would it be safe to consider a persistent cap raise to requested_agents?"
    """
    requested = max(1, _safe_int(requested_agents, 1))
    selected = max(0, _safe_int(selected_count, 0))
    active = max(0, _safe_int(active_count, 0))
    rp: dict[str, Any] = resource_probe if isinstance(resource_probe, dict) else {}
    api_probe_raw = rp.get("api_probe")
    api_probe: dict[str, Any] = api_probe_raw if isinstance(api_probe_raw, dict) else {}
    quality_probe_raw = rp.get("quality_probe")
    quality_probe: dict[str, Any] = quality_probe_raw if isinstance(quality_probe_raw, dict) else {}
    claims: dict[str, Any] = claim_state if isinstance(claim_state, dict) else {}
    cfg: dict[str, Any] = dict(runtime_cfg or {})

    resource_ceiling = max(1, _safe_int(rp.get("effective_resource_ceiling") or cfg.get("dynamic_max_parallel_agents") or cfg.get("max_parallel_agents"), 1))
    quality_slots = max(1, _safe_int(rp.get("quality_slots") or quality_probe.get("quality_slots") or resource_ceiling, resource_ceiling))
    api_slots = max(1, _safe_int(rp.get("api_slots") or api_probe.get("api_slots") or resource_ceiling, resource_ceiling))
    soft_unknown_count = max(0, _safe_int(api_probe.get("soft_unknown_count"), 0))
    hard_blocker_count = max(0, _safe_int(api_probe.get("hard_blocker_count"), 0))
    stale_claim_count = max(0, _safe_int(claims.get("stale_claim_count"), 0))
    handoff_backlog_count = max(0, _safe_int(claims.get("handoff_backlog_count"), 0))
    review_total = max(0, _safe_int(claims.get("review_total"), 0))
    boundary_warnings = max(0, _safe_int(boundary_warning_count, 0))
    confidence = str(api_probe.get("confidence_gate_status") or "").strip().upper()

    handoff_threshold = max(1, _safe_int(cfg.get("concurrency_handoff_backlog_threshold") or cfg.get("handoff_archive_threshold"), 100))
    review_threshold = max(1, _safe_int(cfg.get("concurrency_review_backlog_threshold"), 10))
    blockers: list[dict[str, Any]] = []
    if selected < requested:
        _add_readiness_blocker(blockers, "selected_count_below_requested", actual=selected, required=requested)
    if resource_ceiling < requested:
        _add_readiness_blocker(blockers, "resource_ceiling_below_requested", actual=resource_ceiling, required=requested)
    if quality_slots < requested:
        _add_readiness_blocker(blockers, "quality_slots_below_requested", actual=quality_slots, required=requested)
    if api_slots < requested:
        _add_readiness_blocker(blockers, "api_slots_below_requested", actual=api_slots, required=requested)
    if confidence == "FAIL_CLOSED":
        _add_readiness_blocker(blockers, "api_confidence_fail_closed", actual=confidence, required="PASS")
    if hard_blocker_count > 0:
        _add_readiness_blocker(blockers, "provider_hard_blockers_present", actual=hard_blocker_count, required=0)
    if requested >= 6 and soft_unknown_count > 0:
        _add_readiness_blocker(blockers, "provider_soft_unknowns_present", actual=soft_unknown_count, required=0)
    if stale_claim_count > 0:
        _add_readiness_blocker(blockers, "stale_claims_present", actual=stale_claim_count, required=0)
    if boundary_warnings > 0:
        _add_readiness_blocker(blockers, "boundary_warnings_present", actual=boundary_warnings, required=0)
    if handoff_backlog_count > handoff_threshold:
        _add_readiness_blocker(blockers, "handoff_backlog_high", actual=handoff_backlog_count, required=f"<={handoff_threshold}")
    if review_total > review_threshold:
        _add_readiness_blocker(blockers, "review_backlog_high", actual=review_total, required=f"<={review_threshold}")

    safe_now_ceiling = max(1, min(selected or 1, resource_ceiling, quality_slots, api_slots))
    return {
        "schema": "taskpool_concurrency_readiness_v1",
        "status": "PASS" if not blockers else "FAIL_CLOSED",
        "raise_allowed": not blockers,
        "read_only": True,
        "requested_agents": requested,
        "safe_now_ceiling": safe_now_ceiling,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "inputs": {
            "selected_count": selected,
            "active_count": active,
            "resource_ceiling": resource_ceiling,
            "quality_slots": quality_slots,
            "api_slots": api_slots,
            "api_confidence_gate_status": confidence,
            "soft_unknown_count": soft_unknown_count,
            "hard_blocker_count": hard_blocker_count,
            "stale_claim_count": stale_claim_count,
            "handoff_backlog_count": handoff_backlog_count,
            "handoff_backlog_threshold": handoff_threshold,
            "review_total": review_total,
            "review_threshold": review_threshold,
            "boundary_warning_count": boundary_warnings,
            "max_parallel_agents": cfg.get("max_parallel_agents"),
            "dynamic_max_parallel_agents": cfg.get("dynamic_max_parallel_agents"),
            "failure_rate": quality_probe.get("failure_rate"),
        },
        "safety": "read-only pre-raise gate; does not mutate config, task lifecycle, provider cache, or dispatch selection",
    }


def build_claim_state_telemetry(event: dict[str, Any], *, requested_event_next_tick_depth: int = 0) -> dict[str, Any]:
    task_list_raw = event.get("task_list")
    task_list: dict[str, Any] = task_list_raw if isinstance(task_list_raw, dict) else {}
    rows_raw = task_list.get("rows")
    rows: list[dict[str, Any]] = [row for row in rows_raw if isinstance(row, dict)] if isinstance(rows_raw, list) else []
    parallel_dispatch_raw = event.get("parallel_dispatch")
    parallel_dispatch: dict[str, Any] = parallel_dispatch_raw if isinstance(parallel_dispatch_raw, dict) else {}
    evidence_spine_raw = event.get("evidence_spine")
    evidence_spine: dict[str, Any] = evidence_spine_raw if isinstance(evidence_spine_raw, dict) else {}
    handoff_backlog_raw = event.get("handoff_backlog")
    handoff_backlog: dict[str, Any] = handoff_backlog_raw if isinstance(handoff_backlog_raw, dict) else {}
    backlog_dirs_raw = handoff_backlog.get("dirs")
    backlog_dirs: dict[str, Any] = backlog_dirs_raw if isinstance(backlog_dirs_raw, dict) else {}

    claim_bound_rows = [row for row in rows if str(row.get("status") or "") in {"claimed", "running"}]
    claimed_total = sum(1 for row in rows if str(row.get("status") or "") == "claimed")
    running_total = sum(1 for row in rows if str(row.get("status") or "") == "running")
    review_total = sum(1 for row in rows if str(row.get("status") or "") == "review")
    pending_total = sum(1 for row in rows if str(row.get("status") or "") == "pending")
    stale_claim_count = sum(1 for row in claim_bound_rows if bool(row.get("stale_claim")))
    unsafe_unknown_claim_count = sum(
        1
        for row in claim_bound_rows
        if not str(row.get("claimed_by") or "").strip()
        or not str(row.get("claim_expires_at") or "").strip()
        or not str(row.get("run_id") or "").strip()
    )
    claimed_running_ratio = round(claimed_total / max(running_total, 1), 2) if claimed_total else 0.0
    parallel_selected_count = int(parallel_dispatch.get("selected_count") or 0)
    handoff_backlog_count = sum(
        int(entry.get("count") or 0)
        for entry in backlog_dirs.values()
        if isinstance(entry, dict)
    )
    proof_gate_status = str(evidence_spine.get("gate_status") or "")
    execution_starvation = bool(
        claimed_total > 0
        and claimed_running_ratio >= 2.0
        and parallel_selected_count == 0
        and proof_gate_status == "PASS"
    )

    telemetry_ready = bool(
        task_list.get("status") == "OK"
        and parallel_dispatch.get("status") in {"OK", "PASS"}
        and handoff_backlog.get("schema") == "taskpool_handoff_backlog_v1"
        and bool(proof_gate_status)
    )
    gate_reasons: list[str] = []
    if not telemetry_ready:
        gate_reasons.append("telemetry_incomplete")
    if unsafe_unknown_claim_count > 0:
        gate_reasons.append("unsafe_unknown_claims_present")
    if proof_gate_status != "PASS":
        gate_reasons.append("proof_gate_not_pass")
    if requested_event_next_tick_depth > 3:
        gate_reasons.append("event_next_tick_depth_gt_3")
    if execution_starvation:
        gate_reasons.append("execution_starvation")
    raise_allowed = not gate_reasons
    gate_status = "PASS" if raise_allowed else ("FAIL" if not telemetry_ready else "DENY")

    return {
        "claimed_total": claimed_total,
        "running_total": running_total,
        "review_total": review_total,
        "pending_total": pending_total,
        "stale_claim_count": stale_claim_count,
        "unsafe_unknown_claim_count": unsafe_unknown_claim_count,
        "claimed_running_ratio": claimed_running_ratio,
        "execution_starvation": execution_starvation,
        "parallel_selected_count": parallel_selected_count,
        "handoff_backlog_count": handoff_backlog_count,
        "proof_gate_status": proof_gate_status,
        "concurrency_raise_gate": {
            "status": gate_status,
            "raise_allowed": raise_allowed,
            "reasons": gate_reasons,
            "telemetry_ready": telemetry_ready,
            "requested_event_next_tick_depth": requested_event_next_tick_depth,
            "read_only": True,
            "safety": "fail-closed telemetry gate; advisory only in this patch and does not mutate dispatch behavior",
        },
    }


def load_taskpool_runtime_config() -> dict[str, Any]:
    """Best-effort config reader for dispatch concurrency/health knobs."""
    cfg_path = Path(os.environ.get("HERMES_CONFIG", str(HOME / ".hermes" / "config.yaml"))).expanduser()
    defaults = {
        "dispatch_mode": "single",
        # Floor only.  Parallel mode can raise the effective cap after a
        # read-only boundary dry-run so Lark/work bursts use their existing
        # parallel_boundary classification instead of being pinned to 3.
        "max_parallel_agents": 3,
        "dynamic_max_parallel_agents": 24,
        "review_close_max_tasks": 50,
        "handoff_archive_threshold": 100,
        "handoff_archive_keep": 50,
        "continuation_backlog_threshold": 100,
        # Hooks below only run under explicit --parallel-autorun / worker follow-through.
        "drain_claimed_first": True,
        "event_refill_enabled": False,
        "batch_merge_conflict_threshold": 3,
        "api_quota_cache_ttl_seconds": 45,
        "quality_slots_enabled": True,
        "quality_slots_min_samples": 3,
        "quality_slots_window": 80,
        "stale_claim_reclaim_enabled": False,
        "stale_claim_reclaim_dry_run": True,
        "stale_claim_reclaim_max_tasks": 20,
        "batch_merge_manifest_enabled": True,
        "batch_executor_enabled": False,
        "batch_executor_dry_run": True,
        "batch_executor_require_approval": True,
        "batch_executor_max_tasks_per_batch": 8,
        "batch_executor_per_batch_parallelism": 1,
        "batch_executor_skip_when_regular_selected": True,
        "batch_executor_require_headroom": True,
    }
    try:
        import yaml  # type: ignore
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        taskpool = raw.get("taskpool", {}) if isinstance(raw, dict) else {}
        if isinstance(taskpool, dict):
            defaults.update({k: v for k, v in taskpool.items() if k in defaults})
    except Exception:
        pass
    for key, fallback in (
        ("max_parallel_agents", 3),
        ("dynamic_max_parallel_agents", 24),
        ("review_close_max_tasks", 50),
        ("handoff_archive_threshold", 100),
        ("handoff_archive_keep", 50),
        ("continuation_backlog_threshold", 100),
        ("batch_merge_conflict_threshold", 3),
        ("api_quota_cache_ttl_seconds", 45),
        ("quality_slots_min_samples", 3),
        ("quality_slots_window", 80),
        ("stale_claim_reclaim_max_tasks", 20),
        ("batch_executor_max_tasks_per_batch", 8),
        ("batch_executor_per_batch_parallelism", 1),
    ):
        try:
            defaults[key] = max(0 if key != "max_parallel_agents" else 1, int(defaults.get(key) or fallback))
        except Exception:
            defaults[key] = fallback
    defaults["dispatch_mode"] = str(defaults.get("dispatch_mode") or "single").strip().lower()
    defaults["drain_claimed_first"] = str(defaults.get("drain_claimed_first", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["event_refill_enabled"] = str(defaults.get("event_refill_enabled", "false")).strip().lower() in {"1", "true", "yes", "on"}
    defaults["quality_slots_enabled"] = str(defaults.get("quality_slots_enabled", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["stale_claim_reclaim_enabled"] = str(defaults.get("stale_claim_reclaim_enabled", "false")).strip().lower() in {"1", "true", "yes", "on"}
    defaults["stale_claim_reclaim_dry_run"] = str(defaults.get("stale_claim_reclaim_dry_run", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["batch_merge_manifest_enabled"] = str(defaults.get("batch_merge_manifest_enabled", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["batch_executor_enabled"] = str(defaults.get("batch_executor_enabled", "false")).strip().lower() in {"1", "true", "yes", "on"}
    defaults["batch_executor_dry_run"] = str(defaults.get("batch_executor_dry_run", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["batch_executor_require_approval"] = str(defaults.get("batch_executor_require_approval", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["batch_executor_skip_when_regular_selected"] = str(defaults.get("batch_executor_skip_when_regular_selected", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["batch_executor_require_headroom"] = str(defaults.get("batch_executor_require_headroom", "true")).strip().lower() not in {"0", "false", "no", "off"}
    defaults["dynamic_max_parallel_agents"] = max(
        int(defaults.get("max_parallel_agents") or 3),
        int(defaults.get("dynamic_max_parallel_agents") or 24),
    )
    return defaults


def resolve_parallel_agent_cap(*, requested_max_agents: int, taskpool_cfg: dict[str, Any]) -> dict[str, Any]:
    """Resolve the effective parallel cap from live boundary-safe capacity.

    `taskpool.max_parallel_agents` is a floor, not a hard global worker ceiling.
    In parallel mode the existing task metadata (`parallel_boundary`,
    `parallel_group`, `conflict_group`) is the source of truth.  We therefore
    probe the orchestrator at a configurable ceiling and let its fail-closed
    boundary selector decide how many additional tasks can safely run now.
    """
    configured = int(taskpool_cfg.get("max_parallel_agents") or 3)
    if requested_max_agents > 0:
        return {
            "configured": configured,
            "effective": max(1, int(requested_max_agents)),
            "dynamic_ceiling": int(taskpool_cfg.get("dynamic_max_parallel_agents") or configured),
            "source": "cli",
            "selected_count_at_ceiling": None,
            "dispatchable_at_ceiling": None,
            "probe": {},
        }
    dynamic_ceiling = int(taskpool_cfg.get("dynamic_max_parallel_agents") or configured)
    env_ceiling_raw = os.environ.get("HERMES_TASKPOOL_DYNAMIC_MAX_CAP", "")
    if env_ceiling_raw:
        try:
            dynamic_ceiling = max(dynamic_ceiling, int(env_ceiling_raw))
        except Exception:
            pass
    dynamic_ceiling = max(configured, dynamic_ceiling, 1)
    resource_probe = resource_capacity_probe(
        dynamic_ceiling=dynamic_ceiling,
        quality_enabled=bool(taskpool_cfg.get("quality_slots_enabled")),
        quality_window=int(taskpool_cfg.get("quality_slots_window") or 80),
        quality_min_samples=int(taskpool_cfg.get("quality_slots_min_samples") or 3),
        api_cache_ttl_seconds=int(taskpool_cfg.get("api_quota_cache_ttl_seconds") or 45),
    )
    resource_ceiling = int(resource_probe.get("effective_resource_ceiling") or dynamic_ceiling)
    # Resource pressure is a safety cap, not merely telemetry.  It may lower
    # effective concurrency below the configured floor; explicit --max-agents
    # remains the only manual override path.
    probe_ceiling = max(1, min(dynamic_ceiling, resource_ceiling))
    payload = {
        "configured": configured,
        "effective": probe_ceiling,
        "dynamic_ceiling": dynamic_ceiling,
        "resource_ceiling": resource_ceiling,
        "resource_probe": resource_probe,
        "source": "resource_capped_configured_floor",
        "selected_count_at_ceiling": 0,
        "dispatchable_at_ceiling": False,
        "probe": {},
    }
    if str(taskpool_cfg.get("dispatch_mode") or "").strip().lower() != "parallel":
        return payload
    probe = run_json(["parallel-dispatch-dry-run", "--max-agents", str(probe_ceiling), "--json"])
    payload["probe"] = {
        "status": probe.get("status"),
        "max_agents": probe.get("max_agents"),
        "selected_count": probe.get("selected_count"),
        "dispatchable": probe.get("dispatchable"),
        "skipped_reason_counts": _count_skipped_reasons(probe.get("skipped") or []),
    }
    try:
        selected_count = int(probe.get("selected_count") or 0)
    except Exception:
        selected_count = 0
    payload["selected_count_at_ceiling"] = selected_count
    payload["dispatchable_at_ceiling"] = bool(probe.get("dispatchable"))
    if probe.get("status") in {"OK", "PASS"}:
        payload["effective"] = probe_ceiling
        payload["source"] = "resource_and_boundary_classified_dynamic_ceiling"
    return payload


def _count_skipped_reasons(skipped: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not isinstance(skipped, list):
        return counts
    for item in skipped:
        if not isinstance(item, dict):
            continue
        reason = str(item.get("reason") or "unknown")
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _rows_from_task_list(task_list: Any) -> list[dict[str, Any]]:
    if not isinstance(task_list, dict):
        return []
    rows = task_list.get("rows")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def api_quota_cache_ttl_seconds(default: int = 45) -> int:
    raw = os.environ.get("HERMES_TASKPOOL_API_CACHE_TTL_SECONDS", "")
    if raw:
        try:
            return max(0, int(raw))
        except Exception:
            return default
    return default


def _safe_api_probe_for_cache(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "schema", "status", "api_slots", "env_api_cap", "hard_blocker_count",
        "soft_unknown_count", "hard_blockers", "soft_unknowns", "pass_count",
        "failure_count", "confidence_gate_status", "reason", "safety",
    }
    return {k: payload.get(k) for k in allowed if k in payload}


def load_api_quota_cache(*, dynamic_ceiling: int, env_api_cap: int, ttl_seconds: int) -> dict[str, Any] | None:
    if ttl_seconds <= 0 or os.environ.get("HERMES_TASKPOOL_API_CACHE", "1").strip().lower() in {"0", "false", "no", "off"}:
        return None
    cache = _read_json_file(API_QUOTA_CACHE_FILE)
    if not cache or int(cache.get("dynamic_ceiling") or 0) != int(dynamic_ceiling or 0) or int(cache.get("env_api_cap") or 0) != int(env_api_cap or 0):
        return None
    expires_at = parse_ts(cache.get("expires_at"))
    if not expires_at or expires_at <= utc_now():
        return None
    payload = cache.get("payload") if isinstance(cache.get("payload"), dict) else {}
    if not payload:
        return None
    payload = dict(payload)
    payload["cache"] = {"hit": True, "expires_at": cache.get("expires_at"), "observed_at": cache.get("observed_at"), "ttl_seconds": ttl_seconds}
    return payload


def save_api_quota_cache(*, dynamic_ceiling: int, env_api_cap: int, ttl_seconds: int, payload: dict[str, Any]) -> None:
    if ttl_seconds <= 0 or os.environ.get("HERMES_TASKPOOL_API_CACHE", "1").strip().lower() in {"0", "false", "no", "off"}:
        return
    now = utc_now()
    safe = _safe_api_probe_for_cache(payload)
    try:
        _write_json_file(API_QUOTA_CACHE_FILE, {
            "schema": "taskpool_api_quota_cache_v1",
            "observed_at": now.isoformat().replace("+00:00", "Z"),
            "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z"),
            "dynamic_ceiling": int(dynamic_ceiling or 0),
            "env_api_cap": int(env_api_cap or 0),
            "payload": safe,
            "safety": "sanitized api quota cache; raw command output and environment never persisted",
        })
    except Exception:
        pass


def _recent_tick_events(log_file: Path, *, window: int) -> list[dict[str, Any]]:
    """Read recent tick events without loading an oversized JSONL log.

    Historical dispatch logs can grow to many GB because full tick events include
    task bodies and evidence snapshots.  The quality-capacity probe only needs a
    small tail window, so this function performs a bounded reverse byte scan
    instead of Path.read_text() over the whole file.
    """
    max_lines = max(1, int(window or 1))
    max_bytes = int(os.environ.get("HERMES_TASKPOOL_LOG_TAIL_MAX_BYTES", "8388608") or 8388608)
    chunk_size = 64 * 1024
    try:
        size = log_file.stat().st_size
        with log_file.open("rb") as f:
            pos = size
            chunks: list[bytes] = []
            newline_count = 0
            bytes_read = 0
            while pos > 0 and newline_count <= max_lines and bytes_read < max_bytes:
                read_size = min(chunk_size, pos, max_bytes - bytes_read)
                pos -= read_size
                f.seek(pos)
                chunk = f.read(read_size)
                chunks.append(chunk)
                newline_count += chunk.count(b"\n")
                bytes_read += read_size
    except Exception:
        return []
    data = b"".join(reversed(chunks)) if 'chunks' in locals() else b""
    lines = data.splitlines()[-max_lines:]
    events: list[dict[str, Any]] = []
    for raw in lines:
        try:
            obj = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def quality_capacity_probe(*, dynamic_ceiling: int, worker_jobs: dict[str, Any] | None = None, log_file: Path = LOG_FILE, window: int = 80, min_samples: int = 3) -> dict[str, Any]:
    events = _recent_tick_events(log_file, window=window)
    samples = 0
    failures = 0
    reasons: list[str] = []
    for event in events:
        if event.get("event_worker_trigger") or event.get("autorun") or event.get("parallel_dispatch"):
            samples += 1
        if event.get("status") == "ERROR":
            failures += 1
            reasons.append("tick_error")
        for err in event.get("errors") or []:
            if not isinstance(err, dict):
                continue
            step = str(err.get("step") or "")
            if step in {"event_worker_trigger", "parallel_autorun", "drain_first", "event_next_tick", "proof_check"}:
                failures += 1
                reasons.append(step)
    if worker_jobs and str(worker_jobs.get("status") or "").upper() in {"OK", "PASS"}:
        for job in worker_jobs.get("jobs") or []:
            if not isinstance(job, dict) or job.get("alive"):
                continue
            if job.get("returncode") not in {None, 0, "0"}:
                samples += 1
                failures += 1
                reasons.append("worker_returncode_nonzero")
    neutral_slots = max(1, int(dynamic_ceiling or 1))
    if samples < max(1, int(min_samples or 1)):
        return {
            "schema": "taskpool_quality_capacity_v1",
            "status": "NEUTRAL",
            "quality_slots": neutral_slots,
            "sample_count": samples,
            "failure_count": failures,
            "reason": "insufficient_history",
            "safety": "insufficient quality history is neutral and never punitive",
        }
    failure_rate = failures / max(samples, 1)
    slots = neutral_slots
    if failure_rate >= 0.50:
        slots = max(1, neutral_slots // 2)
    elif failure_rate >= 0.25:
        slots = max(1, int(neutral_slots * 0.75))
    return {
        "schema": "taskpool_quality_capacity_v1",
        "status": "OK",
        "quality_slots": slots,
        "sample_count": samples,
        "failure_count": failures,
        "failure_rate": round(failure_rate, 3),
        "reasons": sorted(set(reasons))[:12],
        "safety": "quality cap only reduces concurrency; it does not bypass proof, acceptance, dependency, or boundary gates",
    }


def api_quota_capacity_probe(*, dynamic_ceiling: int, cache_ttl_seconds: int | None = None) -> dict[str, Any]:
    """Return a conservative API/provider quota slot cap.

    The model_quota confidence gate is strict for budget handoff, but taskpool
    dispatch should not collapse to one slot merely because a provider is
    unobservable or stale.  This probe therefore lowers concurrency only on
    hard blocker evidence (exhausted/rate_limited/malformed/unavailable) or an
    explicit HERMES_TASKPOOL_API_CAP override; unknown/unobservable remains
    visible telemetry.
    """
    env_api_cap_raw = os.environ.get("HERMES_TASKPOOL_API_CAP", "")
    env_api_cap = 0
    if env_api_cap_raw:
        try:
            env_api_cap = max(1, int(env_api_cap_raw))
        except Exception:
            env_api_cap = 0
    ttl_seconds = api_quota_cache_ttl_seconds(int(cache_ttl_seconds if cache_ttl_seconds is not None else 45))
    cached = load_api_quota_cache(dynamic_ceiling=int(dynamic_ceiling or 1), env_api_cap=env_api_cap, ttl_seconds=ttl_seconds)
    if cached is not None:
        return cached
    payload: dict[str, Any] = {
        "schema": "taskpool_api_quota_capacity_v1",
        "status": "UNKNOWN",
        "api_slots": max(1, min(int(dynamic_ceiling or 1), env_api_cap or int(dynamic_ceiling or 1))),
        "env_api_cap": env_api_cap,
        "hard_blocker_count": 0,
        "soft_unknown_count": 0,
        "hard_blockers": [],
        "soft_unknowns": [],
        "cache": {"hit": False, "ttl_seconds": ttl_seconds},
        "safety": "only hard quota/provider blockers reduce taskpool concurrency; unknown/unobservable is telemetry",
    }
    if not MODEL_QUOTA_SCRIPT.exists():
        payload["status"] = "SKIP"
        payload["reason"] = "model_quota_script_missing"
        save_api_quota_cache(dynamic_ceiling=int(dynamic_ceiling or 1), env_api_cap=env_api_cap, ttl_seconds=ttl_seconds, payload=payload)
        return payload
    gate = run_cmd_json([sys.executable, str(MODEL_QUOTA_SCRIPT), "confidence-gate", "--json"], timeout=min(command_timeout_seconds(), 30.0))
    payload["confidence_gate_status"] = gate.get("status")
    if gate.get("status") not in {"PASS", "FAIL_CLOSED"}:
        payload["status"] = "SKIP"
        payload["reason"] = "confidence_gate_unavailable"
        # Do not echo stdout/stderr here: provider errors may include sensitive
        # environment or auth context. Keep only controlled machine fields.
        payload["confidence_gate_error"] = {k: gate.get(k) for k in ["status", "reason", "returncode"] if gate.get(k)}
        save_api_quota_cache(dynamic_ceiling=int(dynamic_ceiling or 1), env_api_cap=env_api_cap, ttl_seconds=ttl_seconds, payload=payload)
        return payload
    hard_statuses = {"exhausted", "rate_limited", "malformed", "unavailable"}
    hard: list[dict[str, Any]] = []
    soft: list[dict[str, Any]] = []
    for item in gate.get("failures") or []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "unknown")
        entry = {
            "model": item.get("model"),
            "provider": item.get("provider"),
            "status": status,
            "reasons": item.get("reasons") or [],
            "reset_at": item.get("reset_at"),
        }
        if status in hard_statuses:
            hard.append(entry)
        else:
            soft.append(entry)
    cap = int(dynamic_ceiling or 1)
    if hard:
        cap = max(1, cap - len(hard))
    if env_api_cap:
        cap = min(cap, env_api_cap)
    payload.update({
        "status": "OK",
        "api_slots": max(1, min(int(dynamic_ceiling or 1), cap)),
        "hard_blocker_count": len(hard),
        "soft_unknown_count": len(soft),
        "hard_blockers": hard[:8],
        "soft_unknowns": soft[:8],
        "pass_count": gate.get("pass_count"),
        "failure_count": gate.get("failure_count"),
    })
    save_api_quota_cache(dynamic_ceiling=int(dynamic_ceiling or 1), env_api_cap=env_api_cap, ttl_seconds=ttl_seconds, payload=payload)
    return payload


def resource_capacity_probe(*, dynamic_ceiling: int, quality_enabled: bool = True, quality_window: int = 80, quality_min_samples: int = 3, api_cache_ttl_seconds: int | None = None) -> dict[str, Any]:
    """Return an advisory resource ceiling for dynamic taskpool dispatch.

    Boundary/quality gates still decide which tasks may run together.  This
    probe only caps how many slots the machine/API/quality feedback should let
    the scheduler ask for in this tick.
    """
    cpu_count = os.cpu_count() or 1
    try:
        load_1m = float(os.getloadavg()[0])
    except Exception:
        load_1m = 0.0
    try:
        disk = shutil.disk_usage(str(HOME))
        disk_free_gb = round(disk.free / (1024 ** 3), 2)
    except Exception:
        disk_free_gb = 0.0
    env_cap_raw = os.environ.get("HERMES_TASKPOOL_RESOURCE_CAP", "")
    env_cap = 0
    if env_cap_raw:
        try:
            env_cap = max(1, int(env_cap_raw))
        except Exception:
            env_cap = 0
    api_probe = api_quota_capacity_probe(dynamic_ceiling=int(dynamic_ceiling or 1), cache_ttl_seconds=api_cache_ttl_seconds)
    worker_jobs = worker_jobs_status()
    if quality_enabled:
        quality_probe = quality_capacity_probe(
            dynamic_ceiling=int(dynamic_ceiling or 1),
            worker_jobs=worker_jobs if isinstance(worker_jobs, dict) else None,
            window=int(os.environ.get("HERMES_TASKPOOL_QUALITY_WINDOW", str(quality_window)) or quality_window),
            min_samples=int(os.environ.get("HERMES_TASKPOOL_QUALITY_MIN_SAMPLES", str(quality_min_samples)) or quality_min_samples),
        )
    else:
        quality_probe = {
            "schema": "taskpool_quality_capacity_v1",
            "status": "DISABLED",
            "quality_slots": max(1, int(dynamic_ceiling or 1)),
            "safety": "quality slots disabled by config; neutral cap",
        }
    machine_slots = max(1, min(int(dynamic_ceiling or 1), cpu_count * 2))
    pressure_reasons: list[str] = []
    if load_1m and load_1m > cpu_count * 1.5:
        machine_slots = max(1, machine_slots // 2)
        pressure_reasons.append("loadavg_high")
    if disk_free_gb and disk_free_gb < 2.0:
        machine_slots = 1
        pressure_reasons.append("disk_free_low")
    api_slots = env_cap or int(api_probe.get("api_slots") or dynamic_ceiling or machine_slots or 1)
    quality_slots = int(quality_probe.get("quality_slots") or dynamic_ceiling or machine_slots or 1)
    effective = max(1, min(int(dynamic_ceiling or 1), machine_slots, api_slots, quality_slots))
    return {
        "schema": "taskpool_resource_capacity_v1",
        "dynamic_ceiling": int(dynamic_ceiling or 0),
        "effective_resource_ceiling": effective,
        "machine_slots": machine_slots,
        "api_slots": api_slots,
        "api_probe": api_probe,
        "quality_slots": quality_slots,
        "quality_probe": quality_probe,
        "cpu_count": cpu_count,
        "load_1m": round(load_1m, 2),
        "disk_free_gb": disk_free_gb,
        "pressure_reasons": pressure_reasons,
        "env_cap": env_cap,
        "safety": "resource/API/quality cap only; boundary/dependency/quality gates remain hard constraints",
    }


def worker_jobs_status() -> dict[str, Any]:
    return run_agent_team_json(["worker-jobs"], timeout=max(command_timeout_seconds(), 30.0))


def alive_worker_task_ids(worker_jobs: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for job in worker_jobs.get("jobs") or []:
        if not isinstance(job, dict) or not job.get("alive"):
            continue
        for task_id in job.get("task_ids") or []:
            text = str(task_id or "").strip()
            if text:
                ids.add(text)
    return ids


def claimed_rows_without_alive_worker(rows: list[dict[str, Any]], worker_jobs: dict[str, Any]) -> list[dict[str, Any]]:
    status = str(worker_jobs.get("status") or "").upper()
    covered = alive_worker_task_ids(worker_jobs) if status in {"OK", "PASS"} else set()
    drainable: list[dict[str, Any]] = []
    allowed_actors = {"hermes-parallel", "hermes-parallel-follow-through"}
    for row in rows:
        if str(row.get("status") or "") != "claimed":
            continue
        task_id = str(row.get("id") or row.get("task_id") or "").strip()
        actor = str(row.get("claimed_by") or "").strip()
        # Drain-first is a recovery hook for Hermes-owned parallel claims.
        # Claims from humans or other actors stay untouched.  Stale reclaim for
        # foreign actors belongs to the dedicated stale-claim cleanup path, not
        # this throughput-oriented drain hook.
        if actor not in allowed_actors:
            continue
        if not (row.get("claimed_by") and row.get("claim_expires_at") and row.get("run_id")):
            continue
        if task_id and task_id not in covered:
            drainable.append(row)
    return drainable


def trigger_claimed_drain_first(*, task_list: dict[str, Any], max_agents: int, foreground: bool) -> dict[str, Any]:
    """Drain historical claimed tasks before claiming more pending work.

    This runs only under explicit parallel autorun.  It prevents already-claimed
    tasks from occupying leases/boundaries without a worker owner.  It does not
    mark tasks done; the agent-team child still owns claimed->running->review.
    """
    # Re-read rows after the caller snapshot so the worker coverage check and
    # claim status are as close together as possible.  This still remains
    # idempotent because agent_team_controller re-checks row status before
    # transitioning claimed -> running.
    fresh_task_list = run_json(["list", "--json"])
    rows = _rows_from_task_list(fresh_task_list if fresh_task_list.get("status") == "OK" else task_list)
    worker_jobs = worker_jobs_status()
    if str(worker_jobs.get("status") or "").upper() not in {"OK", "PASS"}:
        return {
            "status": "SKIP",
            "reason": "worker_jobs_unavailable",
            "worker_jobs": worker_jobs,
            "drained_count": 0,
            "safety": "fail-closed; do not drain claimed without live-worker coverage data",
        }
    drainable = claimed_rows_without_alive_worker(rows, worker_jobs)
    if not drainable:
        return {
            "status": "SKIP",
            "reason": "no_uncovered_claimed_tasks",
            "worker_jobs": {"status": worker_jobs.get("status"), "alive_count": worker_jobs.get("alive_count"), "job_count": worker_jobs.get("job_count")},
            "drained_count": 0,
            "safety": "no side effects; claimed tasks are either absent or already covered by live workers",
        }
    claimed_payload = json.dumps(drainable, ensure_ascii=False)
    cmd = [
        "consume-claimed",
        "--claimed-json",
        claimed_payload,
        "--max-agents",
        str(max(1, max_agents)),
        "--batch-id",
        f"drain-first-{iso()}",
    ]
    if not foreground:
        cmd.append("--background")
    trigger = run_agent_team_json(
        cmd,
        timeout=max(command_timeout_seconds(), 60.0 if not foreground else float(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_WORKER_TIMEOUT_SECONDS", "900"))),
    )
    return {
        "status": trigger.get("status", "OK"),
        "reason": "drain_first_triggered",
        "drainable_count": len(drainable),
        "drained_task_ids": [str(row.get("id") or row.get("task_id") or "") for row in drainable],
        "worker_trigger": trigger,
        "safety": "drain-first only consumes existing claimed tasks; no pending task is claimed here and workers cannot mark done",
    }


def boundary_merge_candidates(parallel_dispatch: dict[str, Any], *, threshold: int = 3) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for item in parallel_dispatch.get("skipped") or []:
        if not isinstance(item, dict) or item.get("reason") != "parallel_boundary_conflict":
            continue
        key = str(item.get("boundary_key") or "unknown")
        buckets.setdefault(key, []).append(item)
    candidates: list[dict[str, Any]] = []
    for key, items in sorted(buckets.items(), key=lambda pair: len(pair[1]), reverse=True):
        if len(items) < threshold:
            continue
        candidates.append({
            "boundary_key": key,
            "conflict_count": len(items),
            "sample_task_ids": [str(x.get("id") or "") for x in items[:8]],
            "recommended_action": "merge_planner_review",
            "merge_policy": "propose_only",
            "safety": "candidate only; batch coordinator must prove compatible goals and per-task acceptance before execution",
        })
    return candidates


def hermes_owned_stale_claim_candidates(*, task_list: dict[str, Any], worker_jobs: dict[str, Any], now: datetime | None = None, max_tasks: int = 20) -> list[dict[str, Any]]:
    rows = _rows_from_task_list(task_list)
    covered = alive_worker_task_ids(worker_jobs) if str(worker_jobs.get("status") or "").upper() in {"OK", "PASS"} else set()
    allowed_actors = {"hermes-parallel", "hermes-parallel-follow-through"}
    now_dt = (now or utc_now()).astimezone(timezone.utc)
    candidates: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("status") or "") != "claimed":
            continue
        task_id = str(row.get("id") or row.get("task_id") or "").strip()
        actor = str(row.get("claimed_by") or "").strip()
        if not task_id or actor not in allowed_actors or task_id in covered:
            continue
        if not row.get("run_id"):
            continue
        expires_at = parse_ts(row.get("claim_expires_at"))
        if not expires_at or expires_at > now_dt:
            continue
        candidates.append({
            "task_id": task_id,
            "claimed_by": actor,
            "run_id": row.get("run_id"),
            "claim_expires_at": row.get("claim_expires_at"),
            "age_seconds_after_expiry": max(0, int((now_dt - expires_at).total_seconds())),
        })
        if len(candidates) >= max(1, int(max_tasks or 1)):
            break
    return candidates


def reclaim_stale_hermes_claims(*, task_list: dict[str, Any], dry_run: bool = True, max_tasks: int = 20, reclaim_enabled: bool = False) -> dict[str, Any]:
    if not dry_run and not reclaim_enabled:
        return {"status": "SKIP", "reason": "apply_requires_explicit_reclaim_enabled", "reclaimed_count": 0, "candidates": [], "safety": "apply mode is gated by stale_claim_reclaim_enabled"}
    worker_jobs = worker_jobs_status()
    if str(worker_jobs.get("status") or "").upper() not in {"OK", "PASS"}:
        return {"status": "SKIP", "reason": "worker_jobs_unavailable", "reclaimed_count": 0, "candidates": [], "safety": "fail-closed without worker coverage data"}
    candidates = hermes_owned_stale_claim_candidates(task_list=task_list, worker_jobs=worker_jobs, max_tasks=max_tasks)
    if dry_run or not candidates:
        return {
            "status": "OK",
            "mode": "dry_run" if dry_run else "apply",
            "reason": "propose_only" if dry_run else "no_stale_hermes_claims",
            "candidate_count": len(candidates),
            "reclaimed_count": 0,
            "candidates": candidates,
            "safety": "Hermes-owned expired claims only; dry-run does not mutate tasks" if dry_run else "no side effects; no candidates",
        }
    reclaimed: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for item in candidates:
        task_id = item["task_id"]
        actor = str(item.get("claimed_by") or "hermes-parallel")
        # Revalidate immediately before mutation: the original candidate list is
        # only a snapshot and may race with a worker or a human reclaim.
        fresh_list = run_json(["list", "--json"])
        fresh_jobs = worker_jobs_status()
        if fresh_list.get("status") != "OK" or str(fresh_jobs.get("status") or "").upper() not in {"OK", "PASS"}:
            skipped.append({"task_id": task_id, "reason": "fresh_revalidation_unavailable"})
            continue
        fresh_candidates = hermes_owned_stale_claim_candidates(
            task_list=fresh_list,
            worker_jobs=fresh_jobs,
            max_tasks=max_tasks,
        )
        if task_id not in {str(x.get("task_id") or "") for x in fresh_candidates}:
            skipped.append({"task_id": task_id, "reason": "revalidation_failed_or_claim_changed"})
            continue
        result = run_json([
            "transition", task_id,
            "--to", "retry",
            "--actor", actor,
            "--authority", "stale-claim-reclaim",
            "--reason", "expired Hermes-owned parallel claim with no alive worker coverage; release for retry",
            "--evidence", "command:brain_task_dispatch_tick stale_hermes_claim_reclaim",
            "--delay-minutes", "5",
            "--force",
            "--json",
        ])
        entry = {"task_id": task_id, "transition": {k: result.get(k) for k in ["status", "ok", "reason"] if k in result}}
        if result.get("ok"):
            reclaimed.append(entry)
        else:
            skipped.append(entry)
    return {
        "status": "OK" if not skipped else "WARN",
        "mode": "apply",
        "candidate_count": len(candidates),
        "reclaimed_count": len(reclaimed),
        "reclaimed": reclaimed,
        "skipped": skipped,
        "safety": "only expired Hermes-owned claims without live worker coverage are moved to retry; no done transitions",
    }


def write_batch_merge_manifest(*, decision: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    candidates = decision.get("batch_merge_candidates") or []
    if not isinstance(candidates, list) or not candidates:
        return {"status": "SKIP", "reason": "no_batch_merge_candidates", "written": False}
    BATCH_MERGE_PLAN_DIR.mkdir(parents=True, exist_ok=True)
    manifest_id = datetime.now(TZ).strftime("%Y%m%dT%H%M%S%z")
    path = BATCH_MERGE_PLAN_DIR / f"batch-merge-plan-{manifest_id}.json"
    payload = {
        "schema": "taskpool_batch_merge_plan_v1",
        "generated_at": iso(),
        "mode": "propose_only",
        "manifest_id": manifest_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "selected_task_ids": [str(x.get("id") or x.get("task_id") or "") for x in ((event.get("parallel_dispatch") or {}).get("selected") or []) if isinstance(x, dict)][:32],
        "required_before_execution": [
            "prove goal compatibility for every child task",
            "map per-task acceptance criteria to individual proof artifacts",
            "prove touched-file/worktree compatibility",
            "define rollback plan",
            "obtain explicit human approval before any merged code execution",
        ],
        "non_goals": ["no source edits", "no lifecycle transitions", "no merged acceptance shortcut", "no done transitions"],
        "safety": "artifact only; dispatcher never executes batch merge plans",
    }
    _write_json_file(path, payload)
    return {"status": "OK", "written": True, "path": str(path), "candidate_count": len(candidates), "mode": "propose_only"}




def _latest_batch_manifest_path() -> Path | None:
    try:
        files = sorted(BATCH_MERGE_PLAN_DIR.glob("batch-merge-plan-*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    except Exception:
        return None
    return files[0] if files else None


def _batch_manifest_task_ids(manifest: dict[str, Any], *, max_tasks: int) -> list[str]:
    seen: set[str] = set()
    task_ids: list[str] = []
    candidates = manifest.get("candidates") if isinstance(manifest.get("candidates"), list) else []
    # The executor consumes one boundary bucket at a time.  This keeps the batch
    # lease scoped and avoids mixing unrelated conflict groups into one worker.
    for cand in candidates[:1]:
        if not isinstance(cand, dict):
            continue
        for raw in cand.get("sample_task_ids") or cand.get("task_ids") or []:
            task_id = str(raw or "").strip()
            if task_id and task_id not in seen:
                seen.add(task_id)
                task_ids.append(task_id)
            if len(task_ids) >= max(1, int(max_tasks or 1)):
                return task_ids
    return task_ids


def _fresh_rows_by_id(task_list: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in _rows_from_task_list(task_list):
        task_id = str(row.get("id") or row.get("task_id") or "").strip()
        if task_id:
            rows[task_id] = row
    return rows


def execute_batch_merge_manifest(
    *,
    manifest_path: str | Path | None,
    enabled: bool,
    dry_run: bool,
    require_approval: bool,
    max_tasks: int,
    per_batch_parallelism: int,
    regular_selected_count: int = 0,
    active_count: int = 0,
    resource_ceiling: int = 0,
    skip_when_regular_selected: bool = True,
    require_headroom: bool = False,
    worker_background: bool = True,
    allow_latest_manifest: bool = False,
) -> dict[str, Any]:
    """Thin batch coordinator: claim a manifest bucket into existing task workers.

    This is intentionally not a new execution or acceptance path.  It only
    changes orchestration granularity: pending tasks from one manifest bucket are
    claimed with a batch run id and then handed to agent_team_controller, which
    still advances every child task independently to review/retry.  The executor
    never writes source, never marks done, and never merges acceptance.
    """
    payload: dict[str, Any] = {
        "schema": "taskpool_batch_executor_v1",
        "status": "SKIP",
        "enabled": bool(enabled),
        "dry_run": bool(dry_run),
        "require_approval": bool(require_approval),
        "require_headroom": bool(require_headroom),
        "active_count": int(active_count or 0),
        "resource_ceiling": int(resource_ceiling or 0),
        "claimed_count": 0,
        "worker_started": False,
        "safety": "thin coordinator only; per-task worker/proof/acceptance gates remain authoritative; no done transitions",
    }
    if not enabled:
        payload["reason"] = "disabled"
        return payload
    if skip_when_regular_selected and int(regular_selected_count or 0) > 0:
        payload["reason"] = "regular_parallel_dispatch_has_selected_tasks"
        payload["regular_selected_count"] = int(regular_selected_count or 0)
        return payload
    headroom = max(0, int(resource_ceiling or 0) - int(active_count or 0)) if int(resource_ceiling or 0) > 0 else 0
    payload["headroom"] = headroom
    if require_headroom and headroom <= 0:
        payload["reason"] = "no_parallel_headroom_for_batch_executor"
        return payload
    if manifest_path:
        path = Path(manifest_path).expanduser()
    elif allow_latest_manifest:
        path = _latest_batch_manifest_path()
    else:
        payload["reason"] = "no_current_tick_manifest"
        return payload
    if not path or not path.exists():
        payload["reason"] = "no_manifest"
        return payload
    manifest = _read_json_file(path)
    if manifest.get("schema") != "taskpool_batch_merge_plan_v1":
        payload.update({"status": "ERROR", "reason": "invalid_manifest_schema", "path": str(path)})
        return payload
    payload["path"] = str(path)
    payload["manifest_id"] = str(manifest.get("manifest_id") or path.stem)
    approved = bool(manifest.get("execution_approved") or manifest.get("operator_approved")) or os.environ.get("HERMES_TASKPOOL_BATCH_EXECUTOR_APPROVED", "").strip().lower() in {"1", "true", "yes", "on"}
    if require_approval and not approved:
        payload["reason"] = "manifest_not_execution_approved"
        return payload
    effective_max_tasks = max(1, min(int(max_tasks or 1), headroom if require_headroom and headroom > 0 else int(max_tasks or 1)))
    payload["effective_max_tasks"] = effective_max_tasks
    task_ids = _batch_manifest_task_ids(manifest, max_tasks=effective_max_tasks)
    payload["candidate_task_ids"] = task_ids
    if not task_ids:
        payload["reason"] = "manifest_has_no_task_ids"
        return payload
    fresh = run_json(["list", "--json"])
    if fresh.get("status") != "OK":
        payload.update({"status": "SKIP", "reason": "fresh_task_list_unavailable", "task_list_status": fresh.get("status")})
        return payload
    rows_by_id = _fresh_rows_by_id(fresh)
    eligible: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for task_id in task_ids:
        row = rows_by_id.get(task_id)
        if not row:
            skipped.append({"task_id": task_id, "reason": "missing_from_fresh_list"})
            continue
        status = str(row.get("status") or "")
        if status not in {"pending", "retry"}:
            skipped.append({"task_id": task_id, "reason": f"not_pending_or_retry:{status}"})
            continue
        if row.get("dispatchable") is not True:
            skipped.append({"task_id": task_id, "reason": "not_explicitly_dispatchable"})
            continue
        eligible.append(row)
    payload["eligible_count"] = len(eligible)
    payload["skipped"] = skipped
    if dry_run or not eligible:
        payload.update({"status": "OK", "mode": "dry_run" if dry_run else "apply", "reason": "dry_run" if dry_run else "no_eligible_tasks", "eligible_task_ids": [str(r.get("id") or r.get("task_id") or "") for r in eligible]})
        return payload
    batch_id = f"batch-executor-{payload['manifest_id']}-{datetime.now(TZ).strftime('%Y%m%dT%H%M%S%f%z')}"
    actor = "hermes-batch-coordinator"
    claimed: list[dict[str, Any]] = []
    claim_errors: list[dict[str, Any]] = []
    for row in eligible[: effective_max_tasks]:
        task_id = str(row.get("id") or row.get("task_id") or "")
        claim = run_json([
            "claim", task_id,
            "--actor", actor,
            "--ttl-minutes", "60",
            "--run-id", batch_id,
            "--reason", "batch coordinator claim; execution remains per-task proof-gated",
            "--json",
        ])
        if claim.get("status") in {"OK", "PASS"} or claim.get("ok"):
            claimed_row = dict(row)
            claimed_row.update({"id": task_id, "task_id": task_id, "claimed_by": actor, "run_id": batch_id, "claim_source": "batch-coordinator", "batch_manifest_id": payload["manifest_id"]})
            claimed.append(claimed_row)
        else:
            claim_errors.append({"task_id": task_id, "status": claim.get("status"), "reason": claim.get("reason")})
    payload["claimed_count"] = len(claimed)
    payload["claim_errors"] = claim_errors
    if not claimed:
        payload.update({"status": "WARN", "mode": "apply", "reason": "no_tasks_claimed"})
        return payload
    BATCH_EXECUTOR_STATE_DIR.mkdir(parents=True, exist_ok=True)
    _write_json_file(BATCH_EXECUTOR_STATE_DIR / f"{batch_id}.json", {
        "schema": "taskpool_batch_executor_lease_v1",
        "batch_id": batch_id,
        "manifest_id": payload["manifest_id"],
        "manifest_path": str(path),
        "created_at": iso(),
        "task_ids": [str(x.get("id") or x.get("task_id") or "") for x in claimed],
        "actor": actor,
        "safety": "lease only; child tasks still own proof and acceptance independently",
    })
    worker_cmd = [
        sys.executable, str(AGENT_TEAM_SCRIPT), "consume-claimed",
        "--claimed-json", json.dumps(claimed, ensure_ascii=False),
        "--max-agents", str(max(1, int(per_batch_parallelism or 1))),
        "--batch-id", batch_id,
    ]
    if worker_background:
        worker_cmd.append("--background")
    worker = run_cmd_json(worker_cmd, timeout=max(command_timeout_seconds(), 60.0))
    payload["worker_trigger"] = worker
    payload["worker_started"] = worker.get("status") in {"ok", "OK", "PASS"}
    if not payload["worker_started"]:
        payload["worker_failure_cleanup"] = cleanup_event_worker_timeout_claims(claimed, actor=actor)
        payload.update({"status": "ERROR", "mode": "apply", "reason": "worker_trigger_failed"})
        return payload
    payload.update({"status": "OK", "mode": "apply", "reason": "claimed_and_worker_triggered", "batch_id": batch_id, "claimed_task_ids": [str(x.get("id") or x.get("task_id") or "") for x in claimed]})
    return payload

def scheduler_decision_snapshot(*, event: dict[str, Any], resource_probe: dict[str, Any], threshold: int) -> dict[str, Any]:
    raw_parallel_dispatch = event.get("parallel_dispatch")
    parallel_dispatch: dict[str, Any] = raw_parallel_dispatch if isinstance(raw_parallel_dispatch, dict) else {}
    task_list = event.get("task_list") if isinstance(event.get("task_list"), dict) else {}
    rows = _rows_from_task_list(task_list)
    raw_active_accounting = parallel_dispatch.get("active_accounting") if isinstance(parallel_dispatch, dict) else None
    active_accounting = raw_active_accounting if isinstance(raw_active_accounting, dict) else {}
    if active_accounting.get("sanitized_claimed_running") is not None:
        active_count = int(active_accounting.get("sanitized_claimed_running") or 0)
        raw_active_count = int(active_accounting.get("raw_claimed_running") or active_count)
    else:
        active_count = sum(1 for row in rows if str(row.get("status") or "") in {"claimed", "running"})
        raw_active_count = active_count
    selected_count = int(parallel_dispatch.get("selected_count") or 0)
    skipped_counts = _count_skipped_reasons(parallel_dispatch.get("skipped") or [])
    resource_ceiling = int(resource_probe.get("effective_resource_ceiling") or 1)
    reasons: list[str] = []
    if selected_count > 0:
        action = "claim_and_consume_selected"
        reasons.append("boundary_safe_slots_available")
    elif active_count >= resource_ceiling:
        action = "wait_for_running_or_claimed_completion"
        reasons.append("resource_ceiling_reached")
    elif skipped_counts.get("parallel_boundary_conflict", 0) > 0:
        action = "boundary_refinement_or_batch_merge"
        reasons.append("boundary_conflict_with_resource_headroom")
    elif not bool(parallel_dispatch.get("dispatchable")):
        action = "idle_no_dispatchable_task"
        reasons.append("no_dispatchable_task")
    else:
        action = "wait_classified_blocker"
        reasons.append("selected_zero_unknown_blocker")
    candidates = boundary_merge_candidates(parallel_dispatch, threshold=threshold)
    return {
        "schema": "taskpool_dynamic_scheduler_decision_v1",
        "active_count": active_count,
        "raw_active_count": raw_active_count,
        "active_accounting_mode": active_accounting.get("mode") or "raw_task_list",
        "resource_ceiling": resource_ceiling,
        "selected_count": selected_count,
        "skipped_reason_counts": skipped_counts,
        "action": action,
        "reasons": reasons,
        "batch_merge_candidates": candidates,
        "batch_merge_candidate_count": len(candidates),
        "safety": "advisory unless under explicit autorun; acceptance remains per-task and proof-gated",
    }


def continuation_backlog_status(*, backlog_warning_threshold: int = 100) -> dict[str, Any]:
    try:
        hermes_agent_dir = Path(os.environ.get("HERMES_AGENT_DIR", str(HOME / ".hermes" / "hermes-agent"))).expanduser()
        if str(hermes_agent_dir) not in sys.path:
            sys.path.insert(0, str(hermes_agent_dir))
        from agent.continuation import continuation_status
        return continuation_status(
            root=HOME / ".hermes" / "state" / "continuations",
            backlog_warning_threshold=backlog_warning_threshold,
        )
    except Exception as exc:
        return {
            "schema": "hermes_continuation_status_v1",
            "status": "ERROR",
            "error": str(exc),
            "active_count": 0,
            "counts": {},
            "by_scope": {},
            "backlog_warning": "",
        }


def handoff_backlog_status(*, archive: bool = False, threshold: int = 100, keep: int = 50) -> dict[str, Any]:
    autorun_state_dir = Path(
        os.environ.get("HERMES_BRAIN_AUTORUN_STATE_DIR", str(HOME / ".hermes" / "state"))
    ).expanduser()
    roots = {
        "autorun": autorun_state_dir / "auto_run_handoffs",
        "parallel": autorun_state_dir / "parallel_handoffs",
    }
    status: dict[str, Any] = {
        "schema": "taskpool_handoff_backlog_v1",
        "threshold": threshold,
        "keep": keep,
        "archive_requested": archive,
        "archived_count": 0,
        "dirs": {},
    }
    archive_root = autorun_state_dir / "archived_handoffs"
    for name, root in roots.items():
        files = sorted(root.glob("*.md"), key=lambda p: p.stat().st_mtime if p.exists() else 0) if root.exists() else []
        was_over_threshold = bool(threshold and len(files) > threshold)
        entry = {
            "path": str(root),
            "count": len(files),
            "count_before": len(files),
            "over_threshold_before": was_over_threshold,
            "over_threshold": was_over_threshold,
            "archived": 0,
        }
        if archive and was_over_threshold:
            to_archive = files[: max(0, len(files) - keep)]
            target = archive_root / name / datetime.now(TZ).strftime("%Y%m%d%H%M%S")
            target.mkdir(parents=True, exist_ok=True)
            for src in to_archive:
                try:
                    shutil.move(str(src), str(target / src.name))
                    entry["archived"] += 1
                    status["archived_count"] += 1
                except Exception:
                    pass
            entry["archive_dir"] = str(target)
            entry["count_after"] = len(list(root.glob("*.md"))) if root.exists() else 0
            entry["over_threshold"] = bool(threshold and int(entry["count_after"]) > threshold)
        status["dirs"][name] = entry
    status["warning"] = "handoff_backlog_high" if any(v.get("over_threshold") for v in status["dirs"].values()) else ""
    return status


def event_next_tick_follow_through(*, worker_trigger: dict[str, Any], review_close_max_tasks: int, max_depth: int, refill_enabled: bool = False, max_agents: int = 1, worker_foreground: bool = False) -> dict[str, Any]:
    """Run a bounded follow-through tick after event-driven workers stop at review.

    The event-driven worker bridge is intentionally not allowed to mark brain
    tasks done. When workers produce review-ready proof, this helper performs
    the normal proof-gated review closer and dispatch refresh.  If explicitly
    enabled by taskpool config it may run exactly one bounded refill
    claim+consume round.  Depth remains capped so follow-through cannot grow
    into an unbounded execution storm.
    """
    requested = bool(worker_trigger.get("next_tick_requested"))
    try:
        depth_limit = max(0, min(3, int(max_depth)))
    except Exception:
        depth_limit = 1
    payload: dict[str, Any] = {
        "status": "SKIP",
        "requested": requested,
        "depth_limit": depth_limit,
        "depth_used": 0,
        "executed_steps": [],
        "skip_reasons": [],
        "closed_count": 0,
        "next_dispatch_selected_count": 0,
        "next_dispatch_status": "",
        "reason": "not_requested" if not requested else "depth_limit_zero",
        "refill_enabled": bool(refill_enabled),
        "safety": "bounded review-close/dispatch-refresh/refill only; no direct done by workers; max one refill round per depth",
    }
    if not requested or depth_limit <= 0:
        payload["skip_reasons"].append(str(payload["reason"]))
        return payload
    payload["depth_used"] = 1
    payload["executed_steps"].append("auto-close-review")
    close = run_json(["auto-close-review", "--max-tasks", str(review_close_max_tasks), "--json"])
    payload["auto_close_review"] = close
    payload["closed_count"] = int(close.get("closed_count") or 0)
    if close.get("status") not in {"OK", "PASS"}:
        payload["status"] = "ERROR"
        payload["reason"] = "auto_close_review_failed"
        return payload
    payload["executed_steps"].append("parallel-dispatch-dry-run")
    refresh = run_json(["parallel-dispatch-dry-run", "--max-agents", str(max(1, int(max_agents or 1))), "--json"])
    payload["dispatch_refresh"] = refresh
    payload["next_dispatch_status"] = str(refresh.get("status") or "")
    payload["next_dispatch_selected_count"] = int(refresh.get("selected_count") or 0)
    if refresh.get("status") not in {"OK", "PASS", "SKIP"}:
        payload["status"] = "ERROR"
        payload["reason"] = "dispatch_refresh_failed"
        return payload
    if refill_enabled and int(refresh.get("selected_count") or 0) > 0:
        payload["executed_steps"].append("parallel-claim-and-handoff")
        refill = run_json([
            "parallel-claim-and-handoff",
            "--max-agents",
            str(max(1, int(max_agents or 1))),
            "--write",
            "--actor",
            "hermes-parallel-follow-through",
            "--json",
        ])
        payload["refill"] = refill
        if refill.get("status") not in {"OK", "PASS"}:
            payload["status"] = "ERROR"
            payload["reason"] = "refill_claim_failed"
            return payload
        if refill.get("claimed"):
            payload["executed_steps"].append("consume-claimed")
            worker_cmd = [
                "consume-claimed",
                "--claimed-json",
                json.dumps(refill.get("claimed_tasks") or [], ensure_ascii=False),
                "--max-agents",
                str(max(1, int(max_agents or 1))),
                "--batch-id",
                str(refill.get("batch_id") or ""),
            ]
            if not worker_foreground:
                worker_cmd.append("--background")
            worker = run_agent_team_json(
                worker_cmd,
                timeout=max(command_timeout_seconds(), 60.0 if not worker_foreground else float(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_WORKER_TIMEOUT_SECONDS", "900"))),
            )
            payload["refill_worker_trigger"] = worker
            if worker.get("status") not in {"ok", "OK", "PASS", "SKIP"}:
                payload["refill_worker_failure_cleanup"] = cleanup_event_worker_timeout_claims(
                    refill.get("claimed_tasks") or [],
                    actor="hermes-parallel-follow-through",
                )
                # Backward-compatible alias for the timeout-specific diagnostic.
                if worker.get("reason") == "subprocess_timeout":
                    payload["refill_worker_timeout_cleanup"] = payload["refill_worker_failure_cleanup"]
                payload["status"] = "ERROR"
                payload["reason"] = "refill_worker_trigger_failed"
                return payload
    payload["status"] = "OK"
    payload["reason"] = "bounded_follow_through_complete"
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe local-brain task dispatch tick")
    parser.add_argument("--print-always", action="store_true", help="Always print the event JSON")
    parser.add_argument("--summary", action="store_true", help="Always print a compact JSON summary suitable for cron no_agent heartbeat delivery")
    parser.add_argument("--no-state", action="store_true", help="Do not suppress repeated notifications")
    parser.add_argument("--autorun", action="store_true", help="Opt-in bridge: run auto-claim-and-handoff after all safe tick gates pass")
    parser.add_argument("--autorun-step", action="store_true", help="Opt-in bounded runner: claim, run static allowlisted command IDs, and stop at review")
    parser.add_argument("--parallel-autorun", action="store_true", help="Opt-in parallel bridge: claim a non-conflicting batch and emit per-task handoffs")
    parser.add_argument("--parallel-worker-foreground", action="store_true", help="Debug only: wait synchronously for agent_team_controller consume-claimed instead of spawning durable worker job")
    parser.add_argument("--max-agents", type=int, default=0, help="Max agents for --parallel-autorun / parallel dry-run; default from taskpool.max_parallel_agents")
    parser.add_argument("--review-close-max-tasks", type=int, default=0, help="Max review tasks scanned by auto-close-review during --autorun-step; default from taskpool.review_close_max_tasks")
    parser.add_argument("--event-next-tick-depth", type=int, default=1, help="Depth cap for event-driven follow-through after workers stop at review; 0 disables, max 3")
    parser.add_argument("--archive-handoffs", action="store_true", help="Archive old autorun/parallel handoff files beyond configured keep count")
    parser.add_argument("--multimodel-step", action="store_true", help="Opt-in expensive multi-model step; still requires HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1")
    parser.add_argument("--multimodel-foreground", action="store_true", help="Wait synchronously for --multimodel-step instead of spawning durable background job")
    parser.add_argument("--multimodel-task", default="", help="Optional task id to scope --multimodel-step; used by task_added event hooks")
    args = parser.parse_args()
    taskpool_cfg = load_taskpool_runtime_config()
    parallel_cap = resolve_parallel_agent_cap(requested_max_agents=int(args.max_agents or 0), taskpool_cfg=taskpool_cfg)
    max_parallel_agents = int(parallel_cap.get("effective") or taskpool_cfg.get("max_parallel_agents") or 3)
    review_close_max_tasks = int(args.review_close_max_tasks or taskpool_cfg.get("review_close_max_tasks") or 50)

    event: dict[str, Any] = {"status": "OK", "generated_at": iso(), "script": str(Path(__file__).expanduser())}
    event["taskpool_runtime"] = {
        "dispatch_mode": taskpool_cfg.get("dispatch_mode"),
        "max_parallel_agents": max_parallel_agents,
        "configured_max_parallel_agents": parallel_cap.get("configured"),
        "dynamic_max_parallel_agents": parallel_cap.get("dynamic_ceiling"),
        "resource_ceiling": parallel_cap.get("resource_ceiling"),
        "resource_probe": parallel_cap.get("resource_probe", {}),
        "parallel_cap_source": parallel_cap.get("source"),
        "parallel_cap_probe": parallel_cap.get("probe"),
        "drain_claimed_first_enabled": bool(taskpool_cfg.get("drain_claimed_first")),
        "event_refill_enabled": bool(taskpool_cfg.get("event_refill_enabled")),
        "batch_merge_conflict_threshold": int(taskpool_cfg.get("batch_merge_conflict_threshold") or 3),
        "batch_merge_manifest_enabled": bool(taskpool_cfg.get("batch_merge_manifest_enabled")),
        "batch_executor_enabled": bool(taskpool_cfg.get("batch_executor_enabled")),
        "batch_executor_dry_run": bool(taskpool_cfg.get("batch_executor_dry_run")),
        "batch_executor_require_approval": bool(taskpool_cfg.get("batch_executor_require_approval")),
        "batch_executor_max_tasks_per_batch": int(taskpool_cfg.get("batch_executor_max_tasks_per_batch") or 8),
        "batch_executor_per_batch_parallelism": int(taskpool_cfg.get("batch_executor_per_batch_parallelism") or 1),
        "batch_executor_skip_when_regular_selected": bool(taskpool_cfg.get("batch_executor_skip_when_regular_selected")),
        "batch_executor_require_headroom": bool(taskpool_cfg.get("batch_executor_require_headroom")),
        "quality_slots_enabled": bool(taskpool_cfg.get("quality_slots_enabled")),
        "stale_claim_reclaim_enabled": bool(taskpool_cfg.get("stale_claim_reclaim_enabled")),
        "stale_claim_reclaim_dry_run": bool(taskpool_cfg.get("stale_claim_reclaim_dry_run")),
        "review_close_max_tasks": review_close_max_tasks,
        "parallel_requested": bool(args.parallel_autorun),
    }
    event["handoff_backlog"] = handoff_backlog_status(
        archive=bool(args.archive_handoffs),
        threshold=int(taskpool_cfg.get("handoff_archive_threshold") or 100),
        keep=int(taskpool_cfg.get("handoff_archive_keep") or 50),
    )
    event["continuation"] = continuation_backlog_status(
        backlog_warning_threshold=int(taskpool_cfg.get("continuation_backlog_threshold") or 100),
    )
    event["ingest"] = run_json(["ingest-inbox", "--write", "--json"])
    event["reconcile"] = run_json(["reconcile", "--write", "--promote-due-retry", "--json"])
    event["dashboard"] = run_json(["dashboard", "--write", "--json"])
    event["task_list"] = run_json(["list", "--json"])
    event["proof_check"] = run_json(["proof-check", "--json"])
    event["evidence_spine"] = run_json(["evidence-spine", "--json"])
    event["railway_published_retests"] = run_json(["release-railway-published-retests", "--max-tasks", "5", "--json"])
    event["multimodel_intervention"] = run_json(["multimodel-intervention-dry-run", "--json"])

    errors = []
    warnings = []
    nonblocking_steps: set[str] = set()
    errored_steps: set[str] = set()
    allowed_statuses = {"OK", "PASS", "SKIP"}  # SKIP for multimodel_step when env var not set
    evidence_spine = event.get("evidence_spine") or {}
    evidence_spine_gate = evidence_spine.get("gate_status")
    evidence_spine_status = evidence_spine.get("status")
    # Self-heal: a passing proof-check is the authoritative correctness signal for the
    # tick. When proof-check PASSes but evidence-spine reports ERROR, treat the spine
    # failure as governance/observability debt (WARN) rather than a dispatch-blocking
    # error, so the tick does not exit with code 2 on otherwise-safe work.
    proof_check_status = str((event.get("proof_check") or {}).get("status") or "")
    if proof_check_status == "PASS" and evidence_spine_status == "ERROR" and evidence_spine_gate != "WARN":
        evidence_spine_gate = "WARN"
    if evidence_spine_gate == "FAIL":
        errors.append({
            "step": "evidence_spine",
            "status": evidence_spine_status,
            "gate_status": evidence_spine_gate,
            "summary": evidence_spine.get("summary", {}),
        })
        errored_steps.add("evidence_spine")
    elif evidence_spine_gate == "WARN":
        # Evidence-spine WARN is governance/observability debt. It must remain visible,
        # but it must not block a bounded dispatch tick for otherwise safe work.
        # Do not add it to errored_steps: that set drives the top-level ERROR status.
        # Do skip the generic status checker below, because the raw subcommand may
        # still say status=ERROR while the lifecycle gate has downgraded it to WARN.
        nonblocking_steps.add("evidence_spine")
        warnings.append({
            "step": "evidence_spine",
            "status": evidence_spine_status,
            "gate_status": evidence_spine_gate,
            "summary": evidence_spine.get("summary", {}),
        })

    # D2: expensive multi-model auto-step is double-gated: explicit CLI flag + env var.
    # Ambient HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 must not turn safe summary
    # cron ticks into long-running model calls.
    if args.multimodel_step and os.environ.get("HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL") == "1" and not errors:
        multimodel_cmd = ["multimodel-intervention-step"]
        if args.multimodel_task:
            multimodel_cmd.extend(["--task", args.multimodel_task])
        if not args.multimodel_foreground:
            multimodel_cmd.append("--background")
        multimodel_cmd.append("--json")
        event["multimodel_step"] = run_json(multimodel_cmd)
        if event["multimodel_step"].get("status") not in allowed_statuses:
            errors.append({"step": "multimodel_step", "status": event["multimodel_step"].get("status"), "stderr": event["multimodel_step"].get("stderr"), "stdout": event["multimodel_step"].get("stdout"), "reason": event["multimodel_step"].get("reason")})
    elif args.multimodel_step and not errors:
        event["multimodel_step"] = {
            "status": "SKIP",
            "reason": "autorun_multimodel_disabled",
            "env_flag": "HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL",
            "safety": "set HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 to enable",
        }
    event["dispatch"] = run_json(["dispatch-dry-run", "--json"])
    event["parallel_dispatch"] = run_json([
        "parallel-dispatch-dry-run",
        "--max-agents",
        str(max_parallel_agents),
        "--json",
    ])

    event["scheduler_decision"] = scheduler_decision_snapshot(
        event=event,
        resource_probe=parallel_cap.get("resource_probe", {}) if isinstance(parallel_cap.get("resource_probe"), dict) else {},
        threshold=int(taskpool_cfg.get("batch_merge_conflict_threshold") or 3),
    )
    if bool(taskpool_cfg.get("batch_merge_manifest_enabled")):
        event["batch_merge_manifest"] = write_batch_merge_manifest(decision=event["scheduler_decision"], event=event)
    else:
        event["batch_merge_manifest"] = {"status": "SKIP", "reason": "disabled", "written": False}
    if args.parallel_autorun or bool(taskpool_cfg.get("stale_claim_reclaim_enabled")):
        reclaim_enabled = bool(taskpool_cfg.get("stale_claim_reclaim_enabled"))
        event["stale_claim_reclaim"] = reclaim_stale_hermes_claims(
            task_list=event.get("task_list", {}) if isinstance(event.get("task_list"), dict) else {},
            dry_run=(True if not reclaim_enabled else bool(taskpool_cfg.get("stale_claim_reclaim_dry_run"))),
            max_tasks=int(taskpool_cfg.get("stale_claim_reclaim_max_tasks") or 20),
            reclaim_enabled=reclaim_enabled,
        )

    event["batch_executor"] = execute_batch_merge_manifest(
        manifest_path=(event.get("batch_merge_manifest") or {}).get("path") if isinstance(event.get("batch_merge_manifest"), dict) else None,
        enabled=bool(args.parallel_autorun and taskpool_cfg.get("batch_executor_enabled")),
        dry_run=bool(taskpool_cfg.get("batch_executor_dry_run")),
        require_approval=bool(taskpool_cfg.get("batch_executor_require_approval")),
        max_tasks=int(taskpool_cfg.get("batch_executor_max_tasks_per_batch") or 8),
        per_batch_parallelism=int(taskpool_cfg.get("batch_executor_per_batch_parallelism") or 1),
        regular_selected_count=int((event.get("scheduler_decision") or {}).get("selected_count") or 0),
        active_count=int((event.get("scheduler_decision") or {}).get("active_count") or 0),
        resource_ceiling=int((event.get("scheduler_decision") or {}).get("resource_ceiling") or max_parallel_agents),
        skip_when_regular_selected=bool(taskpool_cfg.get("batch_executor_skip_when_regular_selected")),
        require_headroom=bool(taskpool_cfg.get("batch_executor_require_headroom")),
        worker_background=not bool(args.parallel_worker_foreground),
    )
    if event["batch_executor"].get("status") not in {"OK", "PASS", "SKIP", "ok"}:
        errors.append({"step": "batch_executor", "status": event["batch_executor"].get("status"), "reason": event["batch_executor"].get("reason"), "worker_trigger": event["batch_executor"].get("worker_trigger")})
        errored_steps.add("batch_executor")

    for key in ["ingest", "reconcile", "dashboard", "task_list", "proof_check", "evidence_spine", "railway_published_retests", "multimodel_intervention", "multimodel_step", "dispatch", "parallel_dispatch"]:
        if key in errored_steps or key in nonblocking_steps:
            continue
        item = event.get(key, {})
        if item and item.get("status") not in allowed_statuses:
            errors.append({"step": key, "status": item.get("status"), "stderr": item.get("stderr"), "stdout": item.get("stdout")})
            errored_steps.add(key)
    event["errors"] = errors
    event["warnings"] = warnings
    if errors:
        event["status"] = "ERROR"
    elif warnings:
        event["status"] = "WARN"

    if args.parallel_autorun and not errors:
        if bool(taskpool_cfg.get("drain_claimed_first")):
            event["drain_first"] = trigger_claimed_drain_first(
                task_list=event.get("task_list", {}) if isinstance(event.get("task_list"), dict) else {},
                max_agents=max_parallel_agents,
                foreground=bool(args.parallel_worker_foreground),
            )
            if event["drain_first"].get("status") not in {"OK", "PASS", "SKIP", "ok"}:
                errors.append({"step": "drain_first", "status": event["drain_first"].get("status"), "reason": event["drain_first"].get("reason"), "worker_trigger": event["drain_first"].get("worker_trigger")})
                event["status"] = "ERROR"
                event["errors"] = errors
        if errors:
            event["autorun"] = {"status": "SKIP", "reason": "drain_first_failed", "claimed": False}
        else:
            event["autorun"] = run_parallel_claim_and_handoff([
                "parallel-claim-and-handoff",
                "--max-agents",
                str(max_parallel_agents),
                "--write",
                "--actor",
                "hermes-parallel",
                "--json",
            ])
        if event["autorun"].get("status") not in {"OK", "PASS"}:
            errors.append({"step": "parallel_autorun", "status": event["autorun"].get("status"), "stderr": event["autorun"].get("stderr"), "stdout": event["autorun"].get("stdout"), "reason": event["autorun"].get("reason")})
            event["status"] = "ERROR"
            event["errors"] = errors
        elif event["autorun"].get("claimed"):
            claimed_payload = json.dumps(event["autorun"].get("claimed_tasks") or [], ensure_ascii=False)
            worker_cmd = [
                sys.executable,
                str(AGENT_TEAM_SCRIPT),
                "consume-claimed",
                "--claimed-json",
                claimed_payload,
                "--max-agents",
                str(max_parallel_agents),
                "--batch-id",
                str(event["autorun"].get("batch_id") or ""),
            ]
            if not args.parallel_worker_foreground:
                worker_cmd.append("--background")
            event["event_worker_trigger"] = run_cmd_json(
                worker_cmd,
                timeout=max(
                    command_timeout_seconds(),
                    60.0 if not args.parallel_worker_foreground else float(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_WORKER_TIMEOUT_SECONDS", "900")),
                ),
            )
            if event["event_worker_trigger"].get("status") not in {"ok", "OK", "PASS", "SKIP"}:
                if event["event_worker_trigger"].get("reason") == "subprocess_timeout":
                    event["event_worker_timeout_cleanup"] = cleanup_event_worker_timeout_claims(
                        event["autorun"].get("claimed_tasks") or [],
                        actor="hermes-parallel",
                    )
                errors.append({"step": "event_worker_trigger", "status": event["event_worker_trigger"].get("status"), "stderr": event["event_worker_trigger"].get("stderr"), "stdout": event["event_worker_trigger"].get("stdout"), "reason": event["event_worker_trigger"].get("reason"), "timeout_cleanup": event.get("event_worker_timeout_cleanup")})
                event["status"] = "ERROR"
                event["errors"] = errors
            else:
                event["event_next_tick"] = event_next_tick_follow_through(
                    worker_trigger=event["event_worker_trigger"],
                    review_close_max_tasks=review_close_max_tasks,
                    max_depth=args.event_next_tick_depth,
                    refill_enabled=bool(taskpool_cfg.get("event_refill_enabled")),
                    max_agents=max_parallel_agents,
                    worker_foreground=bool(args.parallel_worker_foreground),
                )
                if event["event_next_tick"].get("status") not in {"OK", "PASS", "SKIP"}:
                    errors.append({"step": "event_next_tick", "status": event["event_next_tick"].get("status"), "reason": event["event_next_tick"].get("reason")})
                    event["status"] = "ERROR"
                    event["errors"] = errors
        event["post_autorun_dispatch"] = run_json(["parallel-dispatch-dry-run", "--max-agents", str(max_parallel_agents), "--json"])
    elif args.autorun_step and not errors:
        event["autorun"] = run_cmd_json([sys.executable, str(AUTORUN_STEP_SCRIPT), "--json"])
        if event["autorun"].get("status") not in {"OK", "PASS"}:
            errors.append({"step": "autorun_step", "status": event["autorun"].get("status"), "stderr": event["autorun"].get("stderr"), "stdout": event["autorun"].get("stdout")})
            event["status"] = "ERROR"
            event["errors"] = errors
        if not errors:
            event["auto_close_review"] = run_json(["auto-close-review", "--max-tasks", str(review_close_max_tasks), "--json"])
            if event["auto_close_review"].get("status") not in {"OK", "PASS"}:
                errors.append({"step": "auto_close_review", "status": event["auto_close_review"].get("status"), "stderr": event["auto_close_review"].get("stderr"), "stdout": event["auto_close_review"].get("stdout")})
                event["status"] = "ERROR"
                event["errors"] = errors
        event["post_autorun_dispatch"] = run_json(["dispatch-dry-run", "--json"])
    elif args.autorun and not errors:
        event["autorun"] = run_json(["auto-claim-and-handoff", "--json"])
        if event["autorun"].get("status") not in {"OK", "PASS"}:
            errors.append({"step": "autorun", "status": event["autorun"].get("status"), "stderr": event["autorun"].get("stderr"), "stdout": event["autorun"].get("stdout")})
            event["status"] = "ERROR"
            event["errors"] = errors

    next_task = (event.get("dispatch") or {}).get("next") or {}
    next_id = next_task.get("id") or ""
    event["claim_state"] = build_claim_state_telemetry(
        event,
        requested_event_next_tick_depth=int(getattr(args, "event_next_tick_depth", 0) or 0),
    )
    skipped_counts_for_readiness = _count_skipped_reasons((event.get("parallel_dispatch") or {}).get("skipped") or []) if isinstance(event.get("parallel_dispatch"), dict) else {}
    event["concurrency_readiness"] = {
        str(target): concurrency_readiness_snapshot(
            requested_agents=target,
            selected_count=int((event.get("scheduler_decision") or {}).get("selected_count") or 0),
            active_count=int((event.get("scheduler_decision") or {}).get("active_count") or 0),
            resource_probe=parallel_cap.get("resource_probe", {}) if isinstance(parallel_cap.get("resource_probe"), dict) else {},
            claim_state=event.get("claim_state", {}) if isinstance(event.get("claim_state"), dict) else {},
            boundary_warning_count=int(skipped_counts_for_readiness.get("parallel_boundary_conflict") or 0),
            runtime_cfg=taskpool_cfg,
        )
        for target in (4, 6, 8)
    }
    event["next_task_id"] = next_id
    event["dispatchable"] = bool((event.get("dispatch") or {}).get("dispatchable"))
    event["reconcile_action_count"] = int((event.get("reconcile") or {}).get("action_count") or 0)
    event["ingested_count"] = int((event.get("ingest") or {}).get("created_count") or 0)
    event["railway_retest_released_count"] = int((event.get("railway_published_retests") or {}).get("released_count") or 0)
    mm_selected_id = str((event.get("multimodel_intervention") or {}).get("selected_task_id") or "")
    event["multimodel_intervention_required"] = bool((event.get("multimodel_intervention") or {}).get("intervention_required"))
    event["multimodel_intervention_task_id"] = mm_selected_id
    event["log_file"] = str(LOG_FILE)
    event["state_file"] = str(STATE_FILE)

    previous = load_state() if not args.no_state else {}
    changed = next_id and next_id != previous.get("last_notified_task_id")
    mm_changed = mm_selected_id and mm_selected_id != previous.get("last_multimodel_intervention_task_id")
    noteworthy = bool(errors or event["reconcile_action_count"] or event["ingested_count"] or event["railway_retest_released_count"] or changed or mm_changed)
    stdout_policy = "summary" if args.summary else ("print_always" if args.print_always else "noteworthy_only")
    will_print = bool(args.summary or args.print_always or noteworthy)
    print_reason = "summary" if args.summary else ("print_always" if args.print_always else ("noteworthy" if noteworthy else "suppressed_no_change"))
    recovery_command = f"python3 {Path(__file__).expanduser()} --print-always --no-state"
    dispatch_hint = {
        "task_id": next_id,
        "title": next_task.get("title", ""),
        "lane": next_task.get("lane", ""),
        "priority": next_task.get("priority", ""),
        "project": next_task.get("project", ""),
        "claim_command": (event.get("dispatch") or {}).get("claim_command", ""),
        "safety": "hint_only",
    }
    autorun_raw = event.get("autorun") if isinstance(event.get("autorun"), dict) else {}
    auto_close_raw = event.get("auto_close_review") if isinstance(event.get("auto_close_review"), dict) else {}
    event_next_tick_raw = event.get("event_next_tick") if isinstance(event.get("event_next_tick"), dict) else {}
    mm_raw = event.get("multimodel_intervention") if isinstance(event.get("multimodel_intervention"), dict) else {}
    evidence_spine_raw = event.get("evidence_spine") if isinstance(event.get("evidence_spine"), dict) else {}
    mm_selected = mm_raw.get("selected") if isinstance(mm_raw.get("selected"), dict) else {}
    trigger_reasons = mm_selected.get("trigger_reasons", [])
    advisory_reasons = mm_selected.get("advisory_reasons", [])
    cert_reasons = mm_selected.get("certification_reasons", [])
    if not advisory_reasons and not cert_reasons and trigger_reasons:
        strong = {"p0_evolution_blast_radius", "loop_non_convergence", "stale_claim"}
        advisory_reasons = [r for r in trigger_reasons if r not in strong]
        cert_reasons = [r for r in trigger_reasons if r in strong]
    recommended_tier = "T3_certification" if cert_reasons else ("T2_advisory" if len(trigger_reasons) >= 3 else "T1_advisory")
    multimodel_summary = {
        "intervention_required": bool(mm_raw.get("intervention_required")),
        "task_id": str(mm_raw.get("selected_task_id") or ""),
        "queued_count": int(mm_raw.get("queued_count") or 0),
        "criteria": mm_raw.get("criteria", []),
        "trigger_reasons": trigger_reasons,
        "advisory_reasons": advisory_reasons,
        "certification_reasons": cert_reasons,
        "recommended_tier": recommended_tier,
        "advisory_only": bool(advisory_reasons) and not bool(cert_reasons),
        "gate_command_template": mm_selected.get("gate_command_template", ""),
        "convergence": mm_raw.get("convergence", {}),
        "safety": mm_raw.get("safety", ""),
    }
    autorun_summary = {
        "requested": bool(args.autorun or args.autorun_step or args.parallel_autorun),
        "step_mode": "parallel_claim_and_async_worker" if (args.parallel_autorun and not args.parallel_worker_foreground) else ("parallel_claim_and_execute_foreground" if args.parallel_autorun else ("bounded_step" if args.autorun_step else ("claim_and_handoff" if args.autorun else "none"))),
        "present": "autorun" in event,
        "status": autorun_raw.get("status"),
        "eligible": bool(autorun_raw.get("eligible")),
        "claimed": bool(autorun_raw.get("claimed")),
        "advanced": bool(autorun_raw.get("advanced")),
        "task_id": autorun_raw.get("task_id") or autorun_raw.get("task") or "",
        "to_status": autorun_raw.get("to_status", ""),
        "reasons": autorun_raw.get("reasons", []),
        "proof_hash": autorun_raw.get("proof_hash", ""),
        "handoff": autorun_raw.get("handoff", ""),
        "claim_expires_at": autorun_raw.get("claim_expires_at", ""),
        "claimed_count": int(autorun_raw.get("claimed_count") or 0),
        "batch_id": autorun_raw.get("batch_id", ""),
        "worker_trigger": event.get("event_worker_trigger", {}) if isinstance(event.get("event_worker_trigger"), dict) else {},
        "worker_timeout_cleanup": event.get("event_worker_timeout_cleanup", {}) if isinstance(event.get("event_worker_timeout_cleanup"), dict) else {},
        "event_next_tick": event_next_tick_raw,
        "safety": autorun_raw.get("safety", ""),
    }
    summary_payload = {
        "schema": "brain_task_dispatch_tick_summary_v1",
        "generated_at": event["generated_at"],
        "status": event["status"],
        "dispatchable": event["dispatchable"],
        "next_task_id": event["next_task_id"],
        "reconcile_action_count": event["reconcile_action_count"],
        "ingested_count": event["ingested_count"],
        "railway_retest_released_count": event["railway_retest_released_count"],
        "error_count": len(errors),
        "errors": errors,
        "warning_count": len(warnings),
        "warnings": warnings,
        "evidence_spine": {
            "status": evidence_spine_raw.get("status"),
            "gate_status": evidence_spine_raw.get("gate_status"),
            "summary": evidence_spine_raw.get("summary", {}),
            "safety": evidence_spine_raw.get("safety", ""),
        },
        "taskpool_runtime": event.get("taskpool_runtime", {}),
        "handoff_backlog": event.get("handoff_backlog", {}),
        "continuation": event.get("continuation", {}),
        "claim_state": event.get("claim_state", {}),
        "concurrency_readiness": event.get("concurrency_readiness", {}),
        "scheduler_decision": event.get("scheduler_decision", {}),
        "batch_merge_manifest": event.get("batch_merge_manifest", {}),
        "batch_executor": event.get("batch_executor", {}),
        "stale_claim_reclaim": event.get("stale_claim_reclaim", {}),
        "drain_first": event.get("drain_first", {}),
        "parallel_dispatch": event.get("parallel_dispatch", {}),
        "railway_published_retests": event.get("railway_published_retests", {}),
        "multimodel_intervention": multimodel_summary,
        "multimodel_step": (event.get("multimodel_step") or {}) if isinstance(event.get("multimodel_step"), dict) else {},
        "auto_close_review": {
            "status": auto_close_raw.get("status"),
            "closed_count": int(auto_close_raw.get("closed_count") or 0),
            "skipped_count": int(auto_close_raw.get("skipped_count") or 0),
            "error_count": int(auto_close_raw.get("error_count") or 0),
            "closed": auto_close_raw.get("closed", []),
            "skipped": auto_close_raw.get("skipped", []),
            "safety": auto_close_raw.get("safety", ""),
        },
        "stdout_policy": "summary",
        "log_file": str(LOG_FILE),
        "state_file": str(STATE_FILE),
        "dispatch_hint": dispatch_hint,
        "recovery_command": recovery_command,
    }
    if args.autorun or args.autorun_step or args.parallel_autorun:
        summary_payload["autorun"] = autorun_summary
    event["observability"] = {
        "schema": "brain_task_dispatch_tick_observability_v1",
        "stdout_policy": stdout_policy,
        "printed": will_print,
        "print_reason": print_reason,
        "noteworthy": noteworthy,
        "summary_available": True,
        "log_file": str(LOG_FILE),
        "state_file": str(STATE_FILE),
        "recovery_command": recovery_command,
        "no_agent_note": "Default no-change ticks may intentionally emit empty stdout; use --summary for heartbeat or --print-always for full JSON.",
    }

    append_log(event)
    save_state({
        "updated_at": event["generated_at"],
        "last_notified_task_id": next_id,
        "last_status": event["status"],
        "last_dispatchable": event["dispatchable"],
        "last_multimodel_intervention_task_id": mm_selected_id,
        "last_multimodel_intervention_required": event["multimodel_intervention_required"],
        "last_log_file": str(LOG_FILE),
        "last_stdout_policy": stdout_policy,
        "last_print_reason": print_reason,
    })

    if args.summary:
        print(json.dumps(summary_payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif args.print_always or noteworthy:
        print(json.dumps(event, ensure_ascii=False, indent=2))
    return 0 if event["status"] in {"OK", "WARN"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
