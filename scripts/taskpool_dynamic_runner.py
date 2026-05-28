#!/usr/bin/env python3
"""Dynamic no-agent taskpool runner.

Cron may call this frequently, but actions are event-gated by taskpool state,
not by the wall clock. It emits no stdout when nothing changed.
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOME = Path.home()
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes"))).expanduser()
STATE = HERMES_HOME / "state" / "taskpool_dynamic_runner.json"
LOG = HERMES_HOME / "logs" / "taskpool_dynamic_runner.jsonl"
LOCK = HERMES_HOME / "state" / "taskpool_dynamic_runner.pid"
TICK = HERMES_HOME / "scripts" / "brain_task_dispatch_tick.py"
MM_DYNAMIC = HERMES_HOME / "scripts" / "multimodel_intervention_dynamic_step.py"


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], timeout: int = 240, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True, env=env)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
            out, err = proc.communicate()
        return with_output_tails({"cmd": cmd, "returncode": "timeout", "reason": "subprocess_timeout", "stdout": out or "", "stderr": err or ""})
    return with_output_tails({"cmd": cmd, "returncode": proc.returncode, "stdout": out or "", "stderr": err or ""})


def with_output_tails(result: dict[str, Any], stdout_limit: int = 4000, stderr_limit: int = 4000) -> dict[str, Any]:
    """Keep full output for internal parsing while exposing bounded tails for logs."""
    stdout = result.get("stdout") or ""
    stderr = result.get("stderr") or ""
    result["stdout_tail"] = stdout[-stdout_limit:]
    result["stderr_tail"] = stderr[-stderr_limit:]
    result["stdout_bytes"] = len(stdout.encode("utf-8", errors="replace"))
    result["stderr_bytes"] = len(stderr.encode("utf-8", errors="replace"))
    return result


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    compact = dict(result)
    compact["stdout"] = compact.get("stdout_tail", (compact.get("stdout") or "")[-4000:])
    compact["stderr"] = compact.get("stderr_tail", (compact.get("stderr") or "")[-4000:])
    return compact


def load_state() -> dict[str, Any]:
    try: return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception: return {}


def save_state(obj: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append(obj: dict[str, Any]) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def alive(pid: int) -> bool:
    try: os.kill(pid, 0); return True
    except Exception: return False


def acquire_lock() -> bool:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        try:
            pid = int(LOCK.read_text().strip() or "0")
            if pid and alive(pid):
                return False
        except Exception:
            pass
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    return True


def release_lock() -> None:
    try:
        if LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except Exception:
        pass



def load_taskpool_config() -> dict[str, Any]:
    cfg = HERMES_HOME / "config.yaml"
    try:
        import yaml  # type: ignore
        raw = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        taskpool = raw.get("taskpool", {}) if isinstance(raw, dict) else {}
        return taskpool if isinstance(taskpool, dict) else {}
    except Exception:
        return {}


def load_taskpool_dispatch_mode() -> str:
    taskpool = load_taskpool_config()
    return str((taskpool or {}).get("dispatch_mode") or "single").strip().lower()


def parse_json_tail(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text: return {}
    try: return json.loads(text)
    except Exception: return {}


def signature(summary: dict[str, Any]) -> str:
    payload = {
        "status": summary.get("status"),
        "next": summary.get("next_task_id"),
        "dispatchable": summary.get("dispatchable"),
        "errors": summary.get("error_count"),
        "reconcile": summary.get("reconcile_action_count"),
        "ingested": summary.get("ingested_count"),
        "mm": (summary.get("multimodel_intervention") or {}).get("task_id"),
        "mmq": (summary.get("multimodel_intervention") or {}).get("queued_count"),
        "auto_close_closed": (summary.get("auto_close_review") or {}).get("closed_count"),
        "auto_close_errors": (summary.get("auto_close_review") or {}).get("error_count"),
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def positive_int(value: Any, default: int, *, minimum: int = 1) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(minimum, parsed)


def human_escape_status() -> dict[str, Any]:
    """Read the envelope human-escape breaker before claiming new work.

    The controller also checks this after claim, but the dynamic runner is the
    outer claim trigger.  If the breaker is already active, claiming first and
    releasing later creates retry churn and can wedge on controller timeout.
    """
    try:
        script_dir = str(HERMES_HOME / "scripts")
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        from envelope_bus import human_escape_check  # type: ignore
        triggered, info = human_escape_check()
        return {"status": "OK", "triggered": bool(triggered), "info": info}
    except Exception as exc:
        return {"status": "ERROR", "triggered": True, "reason": "human_escape_check_failed", "error": str(exc)[:300]}




def _parse_iso_z(value: Any) -> float | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    # A trailing Z is UTC.  Do not parse it as a naive local timestamp: on
    # Asia/Shanghai hosts that makes a fresh ack look ~8h old and can jump the
    # recovery scaler straight to the hard max.
    if text.endswith("Z"):
        try:
            return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
        except Exception:
            pass
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    except Exception:
        return None


def recovery_cap_from_escape(*, cfg: dict[str, Any], escape_status: dict[str, Any], env: dict[str, str]) -> dict[str, Any]:
    """Return a bounded dynamic ceiling for post-escape recovery.

    Multi-model can advise scale-up, but the runtime uses deterministic gates:
    any post-ack block/failure holds the canary cap; a clean window gradually
    raises concurrency.  This never bypasses proof gates or human_escape.
    """
    base = positive_int(cfg.get("max_parallel_agents"), 3)
    configured_dynamic = positive_int(cfg.get("dynamic_max_parallel_agents"), base)
    recovery_enabled = str(cfg.get("dynamic_recovery_enabled", "true")).strip().lower() not in {"0", "false", "no", "off"}
    recovery_min = positive_int(cfg.get("dynamic_recovery_min_agents"), base)
    recovery_max = positive_int(cfg.get("dynamic_recovery_max_agents"), configured_dynamic)
    recovery_step = positive_int(cfg.get("dynamic_recovery_step_agents"), 2)
    stable_window = positive_int(cfg.get("dynamic_recovery_stable_window_seconds"), 900)
    failure_hold = positive_int(cfg.get("dynamic_recovery_failure_hold_seconds"), 1800)
    operator_ceiling = positive_int(env.get("HERMES_TASKPOOL_DYNAMIC_MAX_CAP"), recovery_max)
    hard_max = max(base, min(recovery_max, operator_ceiling))
    info = escape_status.get("info") if isinstance(escape_status.get("info"), dict) else {}
    since = info.get("since_ack") if isinstance(info.get("since_ack"), dict) else {}
    ack = info.get("ack") if isinstance(info.get("ack"), dict) else {}
    failures = int(since.get("failures") or 0)
    blocks = int(since.get("blocks") or 0)
    invalid_ts = int(since.get("invalid_timestamps") or 0)
    ack_ts = _parse_iso_z(ack.get("acked_at"))
    age = max(0, int(time.time() - ack_ts)) if ack_ts else 0
    payload = {
        "enabled": recovery_enabled,
        "base": base,
        "min": recovery_min,
        "max": recovery_max,
        "operator_ceiling": operator_ceiling,
        "hard_max": hard_max,
        "step": recovery_step,
        "stable_window_seconds": stable_window,
        "failure_hold_seconds": failure_hold,
        "since_ack_failures": failures,
        "since_ack_blocks": blocks,
        "since_ack_invalid_timestamps": invalid_ts,
        "ack_age_seconds": age,
    }
    if not recovery_enabled:
        payload.update({"ceiling": configured_dynamic, "reason": "dynamic_recovery_disabled"})
        return payload
    if bool(escape_status.get("triggered")):
        payload.update({"ceiling": recovery_min, "reason": "human_escape_active_hold_min"})
        return payload
    if failures or blocks or invalid_ts:
        payload.update({"ceiling": max(base, recovery_min), "reason": "post_ack_failure_hold"})
        return payload
    if not ack_ts:
        payload.update({"ceiling": max(base, recovery_min), "reason": "no_valid_escape_ack_hold_min"})
        return payload
    increments = age // stable_window if stable_window > 0 else 0
    ceiling = min(hard_max, max(base, recovery_min) + int(increments) * recovery_step)
    payload.update({"ceiling": ceiling, "reason": "clean_window_scaled" if ceiling > recovery_min else "clean_window_canary"})
    return payload

def compute_parallel_max_agents(env: dict[str, str]) -> dict[str, Any]:
    """Choose a safe parallel cap from the live boundary classifier.

    The config value is only the floor.  For Lark/work bursts, many tasks have
    explicit non-overlapping `parallel_boundary` values.  A read-only dry-run at
    a higher cap lets the orchestrator's own boundary logic decide how many can
    be safely co-dispatched without broadening allowlists or bypassing proof
    gates.
    """
    cfg = load_taskpool_config()
    configured = positive_int(cfg.get("max_parallel_agents"), 3)
    # Probe above the configured floor for Lark/work bursts.  The dry-run owns
    # boundary classification; the write tick only runs when it reports
    # additional non-conflicting slots.  During recovery, a deterministic
    # envelope-backed scaler raises this ceiling gradually; model review may
    # tune the policy, but not bypass it.
    escape_status = human_escape_status()
    recovery_cap = recovery_cap_from_escape(cfg=cfg, escape_status=escape_status, env=env)
    ceiling = positive_int(recovery_cap.get("ceiling"), configured)
    ceiling = max(configured, ceiling)
    probe = run(
        [sys.executable, str(HERMES_HOME / "scripts" / "brain_task_orchestrator.py"), "parallel-dispatch-dry-run", "--max-agents", str(ceiling), "--json"],
        timeout=90,
        env=env,
    )
    result: dict[str, Any] = {
        "configured": configured,
        "ceiling": ceiling,
        "selected_count": 0,
        "recommended": configured,
        "reason": "probe_unavailable",
        "probe": compact_result(probe),
        "recovery_cap": recovery_cap,
    }
    if probe.get("returncode") not in (0, "0"):
        return result
    try:
        data = json.loads(probe.get("stdout") or "{}")
    except Exception as exc:
        result["reason"] = "probe_parse_failed"
        result["parse_error"] = str(exc)
        return result
    selected_count = positive_int(data.get("selected_count"), 0, minimum=0)
    result["selected_count"] = selected_count
    result["status"] = data.get("status")
    result["dispatchable"] = bool(data.get("dispatchable"))
    # The dry-run `selected_count` is the *additional* safe batch at the probed
    # ceiling after accounting for active claimed/running tasks.  Reuse the same
    # ceiling for the write tick so those available slots remain available; using
    # only selected_count would accidentally collapse capacity when active tasks
    # already occupy part of the ceiling.
    result["recommended"] = ceiling if selected_count > 0 else configured
    result["reason"] = "boundary_classified_batch" if selected_count > 0 and ceiling > configured else "configured_cap_sufficient"
    return result


def main() -> int:
    if not acquire_lock():
        return 0
    try:
        env = os.environ.copy()
        env.setdefault("HERMES_LOCAL_BRAIN_AUTORUN", "1")
        event: dict[str, Any] = {"schema": "taskpool_dynamic_runner_v1", "ts": utc()}
        dispatch_mode = load_taskpool_dispatch_mode()
        autorun_flag = "--parallel-autorun" if dispatch_mode == "parallel" else "--autorun-step"
        event["dispatch_mode"] = dispatch_mode
        event["autorun_flag"] = autorun_flag
        escape_status = human_escape_status()
        event["human_escape"] = escape_status
        autorun_allowed = not bool(escape_status.get("triggered"))
        tick_cmd = [sys.executable, str(TICK), "--summary", "--no-state"]
        if autorun_flag == "--parallel-autorun" and autorun_allowed:
            parallel_cap = compute_parallel_max_agents(env)
            event["parallel_cap"] = {k: v for k, v in parallel_cap.items() if k != "probe"}
            event["parallel_cap_probe"] = parallel_cap.get("probe", {})
            if int(parallel_cap.get("selected_count") or 0) > 0:
                tick_cmd.insert(3, autorun_flag)
                tick_cmd.extend(["--max-agents", str(parallel_cap.get("recommended") or 3)])
            else:
                event["autorun_skipped_reason"] = "no_additional_boundary_safe_slots"
                event["summary"] = {
                    "status": "OK",
                    "dispatchable": bool(parallel_cap.get("dispatchable")),
                    "error_count": 0,
                    "next_task_id": "",
                    "reconcile_action_count": 0,
                    "ingested_count": 0,
                }
                event["autorun"] = {
                    "present": False,
                    "requested": True,
                    "claimed": False,
                    "safety": "skipped; active boundary-safe parallel slots are full or no non-conflicting task remains",
                }
                sig = signature(event["summary"])
                prev = load_state()
                event["changed"] = sig != prev.get("signature")
                event["signature"] = sig
                save_state({"updated_at": event["ts"], "signature": sig, "last_mm_probe_epoch": prev.get("last_mm_probe_epoch", 0), "last_summary": event["summary"], "last_auto_close_review": {}})
                append(event)
                if event["changed"]:
                    print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
                return 0
        else:
            if autorun_allowed:
                tick_cmd.insert(3, autorun_flag)
            else:
                event["autorun_skipped_reason"] = "human_escape_active_preclaim"
        tick = run(tick_cmd, timeout=int(os.environ.get("HERMES_TASKPOOL_DYNAMIC_TIMEOUT", "1200")), env=env)
        event["tick"] = compact_result(tick)
        summary = parse_json_tail(tick.get("stdout", ""))
        if tick.get("returncode") in (0, "0") and tick.get("stdout") and not summary:
            event.update({"status": "ERROR", "action": "summary_parse_failed", "parse_error": "tick_stdout_not_json"})
            prev_state = load_state()
            save_state({"updated_at": event["ts"], "signature": prev_state.get("signature", ""), "last_mm_probe_epoch": prev_state.get("last_mm_probe_epoch", 0), "last_summary": {}})
            append(event)
            print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        event["summary"] = {k: summary.get(k) for k in ["status", "next_task_id", "dispatchable", "error_count", "reconcile_action_count", "ingested_count"]}
        event["autorun"] = summary.get("autorun", {}) if isinstance(summary.get("autorun"), dict) else {}
        event["auto_close_review"] = summary.get("auto_close_review", {}) if isinstance(summary.get("auto_close_review"), dict) else {}
        sig = signature(summary)
        prev = load_state()
        changed = sig != prev.get("signature")
        event["changed"] = changed
        event["signature"] = sig
        should_print = changed or tick.get("returncode") not in (0, "0") or bool((summary.get("error_count") or 0)) or bool(event["autorun"].get("advanced")) or bool(event["auto_close_review"].get("closed_count")) or bool(event["auto_close_review"].get("error_count"))
        # Start/advance multimodel worker opportunistically, but never block this tick.
        mm = summary.get("multimodel_intervention") if isinstance(summary.get("multimodel_intervention"), dict) else {}
        if mm.get("intervention_required") and (changed or time.time() - float(prev.get("last_mm_probe_epoch") or 0) > 1800):
            mm_dynamic = run([sys.executable, str(MM_DYNAMIC), "--json"], timeout=60, env=env)
            event["multimodel_dynamic"] = compact_result(mm_dynamic)
            should_print = True if mm_dynamic.get("stdout") else should_print
            prev["last_mm_probe_epoch"] = time.time()
        state = {"updated_at": event["ts"], "signature": sig, "last_mm_probe_epoch": prev.get("last_mm_probe_epoch", 0), "last_summary": event["summary"], "last_auto_close_review": event["auto_close_review"]}
        save_state(state); append(event)
        if should_print:
            print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if tick.get("returncode") in (0, "0") else 2
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
