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
STATE_DIR = Path(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_STATE_DIR", str(HOME / ".hermes" / "state"))).expanduser()
LOG_DIR = Path(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_LOG_DIR", str(HOME / ".hermes" / "logs"))).expanduser()
STATE_FILE = STATE_DIR / "brain_task_dispatch_tick_state.json"
LOG_FILE = LOG_DIR / "brain_task_dispatch_tick.jsonl"
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


def append_log(event: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


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
    ):
        try:
            defaults[key] = max(0 if key != "max_parallel_agents" else 1, int(defaults.get(key) or fallback))
        except Exception:
            defaults[key] = fallback
    defaults["dispatch_mode"] = str(defaults.get("dispatch_mode") or "single").strip().lower()
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
    payload = {
        "configured": configured,
        "effective": configured,
        "dynamic_ceiling": dynamic_ceiling,
        "source": "configured_floor",
        "selected_count_at_ceiling": 0,
        "dispatchable_at_ceiling": False,
        "probe": {},
    }
    if str(taskpool_cfg.get("dispatch_mode") or "").strip().lower() != "parallel" or dynamic_ceiling <= configured:
        return payload
    probe = run_json(["parallel-dispatch-dry-run", "--max-agents", str(dynamic_ceiling), "--json"])
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
        payload["effective"] = dynamic_ceiling
        payload["source"] = "boundary_classified_dynamic_ceiling"
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


def event_next_tick_follow_through(*, worker_trigger: dict[str, Any], review_close_max_tasks: int, max_depth: int) -> dict[str, Any]:
    """Run a bounded follow-through tick after event-driven workers stop at review.

    The event-driven worker bridge is intentionally not allowed to mark brain
    tasks done. When workers produce review-ready proof, this helper performs
    only the normal proof-gated review closer and a read-only dispatch refresh.
    It does not claim new tasks, consume more handoffs, or recursively invoke
    another dispatch tick; depth is telemetry plus a hard cap so future stages
    cannot grow into an unbounded execution storm.
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
        "safety": "bounded review-close/dispatch-refresh only; no recursive claim or direct done by workers",
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
    refresh = run_json(["parallel-dispatch-dry-run", "--max-agents", "1", "--json"])
    payload["dispatch_refresh"] = refresh
    payload["next_dispatch_status"] = str(refresh.get("status") or "")
    payload["next_dispatch_selected_count"] = int(refresh.get("selected_count") or 0)
    if refresh.get("status") not in {"OK", "PASS", "SKIP"}:
        payload["status"] = "ERROR"
        payload["reason"] = "dispatch_refresh_failed"
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
    parser.add_argument("--max-agents", type=int, default=0, help="Max agents for --parallel-autorun / parallel dry-run; default from taskpool.max_parallel_agents")
    parser.add_argument("--review-close-max-tasks", type=int, default=0, help="Max review tasks scanned by auto-close-review during --autorun-step; default from taskpool.review_close_max_tasks")
    parser.add_argument("--event-next-tick-depth", type=int, default=1, help="Depth cap for event-driven follow-through after workers stop at review; 0 disables, max 3")
    parser.add_argument("--archive-handoffs", action="store_true", help="Archive old autorun/parallel handoff files beyond configured keep count")
    parser.add_argument("--multimodel-step", action="store_true", help="Opt-in expensive multi-model step; still requires HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1")
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
        "parallel_cap_source": parallel_cap.get("source"),
        "parallel_cap_probe": parallel_cap.get("probe"),
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
    errored_steps: set[str] = set()
    allowed_statuses = {"OK", "PASS", "SKIP"}  # SKIP for multimodel_step when env var not set
    evidence_spine = event.get("evidence_spine") or {}
    evidence_spine_gate = evidence_spine.get("gate_status")
    evidence_spine_status = evidence_spine.get("status")
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
        warnings.append({
            "step": "evidence_spine",
            "status": evidence_spine_status,
            "gate_status": evidence_spine_gate,
            "summary": evidence_spine.get("summary", {}),
        })
        errored_steps.add("evidence_spine")

    # D2: expensive multi-model auto-step is double-gated: explicit CLI flag + env var.
    # Ambient HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 must not turn safe summary
    # cron ticks into long-running model calls.
    if args.multimodel_step and os.environ.get("HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL") == "1" and not errors:
        multimodel_cmd = ["multimodel-intervention-step"]
        if args.multimodel_task:
            multimodel_cmd.extend(["--task", args.multimodel_task])
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

    for key in ["ingest", "reconcile", "dashboard", "task_list", "proof_check", "evidence_spine", "railway_published_retests", "multimodel_intervention", "multimodel_step", "dispatch", "parallel_dispatch"]:
        if key in errored_steps:
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
        event["autorun"] = run_json([
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
            event["event_worker_trigger"] = run_cmd_json([
                sys.executable,
                str(AGENT_TEAM_SCRIPT),
                "consume-claimed",
                "--claimed-json",
                claimed_payload,
                "--max-agents",
                str(max_parallel_agents),
            ],
                timeout=max(
                    command_timeout_seconds(),
                    float(os.environ.get("HERMES_BRAIN_DISPATCH_TICK_WORKER_TIMEOUT_SECONDS", "900")),
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
        "step_mode": "parallel_claim_and_execute" if args.parallel_autorun else ("bounded_step" if args.autorun_step else ("claim_and_handoff" if args.autorun else "none")),
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
