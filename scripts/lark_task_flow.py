#!/usr/bin/env python3
from __future__ import annotations
"""One-shot Lark Task automation flow for Hermes.

Single entrypoint that preserves the automated OAuth consent click while keeping
read operations read-only:

1. run the single-flight OAuth guard (valid token => no browser; otherwise one
   guarded login flow, optionally auto-clicking the visible Lark 授权 button);
2. read the Lark task token from lark-mcp auth store without triggering another
   auth flow;
3. read either the scoped incomplete task list or one task by guid/applink URL;
4. print compact summary or JSON.

This script never writes back to Lark and never prints tokens/secrets.
"""

import argparse
import importlib.util
import json
import os
import re
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path.home() / ".hermes" / "scripts"
GUARD = SCRIPTS_DIR / "lark_oauth_guard.py"
READER = SCRIPTS_DIR / "lark_task_reader.py"
LARK_PROFILE = Path.home() / ".hermes" / "project-profiles" / "lark.json"
LARK_AUTHORITY_GRANT_ROOT = Path.home() / ".hermes" / "workflows" / "projects" / "lark" / "authority-grants"
DURABLE_RECOVERY_TRIGGER = "token_missing_invalid_or_expired_during_non_health_lark_flow"
DURABLE_RECOVERY_TTL_SECONDS = 300
ENTRYPOINT = Path(__file__).resolve()
GUID_RE = re.compile(r"guid=([0-9a-fA-F-]{32,36})|/tasks/([0-9a-fA-F-]{32,36})")


def load_reader():
    spec = importlib.util.spec_from_file_location("hermes_lark_task_reader", READER)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load reader from {READER}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def extract_guid(value: str | None) -> str:
    if not value:
        return ""
    raw = value.strip()
    if re.fullmatch(r"[0-9a-fA-F-]{32,36}", raw):
        return raw
    m = GUID_RE.search(raw)
    if not m:
        raise ValueError(f"cannot extract Lark task guid from: {value}")
    return next(g for g in m.groups() if g)


def _has_symlink_component(path: Path) -> bool:
    absolute = path.expanduser().absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if current.is_symlink():
            return True
    return False


def _read_regular_file_no_symlinks(path: Path, max_bytes: int = 1_048_576) -> bytes:
    """Read one regular-file inode through an O_NOFOLLOW directory walk."""
    absolute = path.expanduser().absolute()
    parts = absolute.parts
    fd = os.open(absolute.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in parts[1:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=fd,
            )
            os.close(fd)
            fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
                raise ValueError("authority artifact is not a bounded regular file")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(file_fd, min(65_536, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError("authority artifact exceeds size limit")
            after = os.fstat(file_fd)
            if (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            ) != (
                after.st_dev,
                after.st_ino,
                after.st_mode,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("authority artifact changed while reading")
            return b"".join(chunks)
        finally:
            os.close(file_fd)
    finally:
        os.close(fd)


def oauth_recovery_auto_authorized(
    profile_path: Path = LARK_PROFILE,
    allowed_grant_root: Path = LARK_AUTHORITY_GRANT_ROOT,
) -> bool:
    """Fail closed unless the profile points to the exact bounded active grant."""
    try:
        profile_bytes = _read_regular_file_no_symlinks(profile_path)
        profile = json.loads(profile_bytes.decode("utf-8"))
        if not isinstance(profile, dict):
            return False
        automation_policy = profile.get("automation_policy")
        if not isinstance(automation_policy, dict):
            return False
        policy = automation_policy.get("lark_oauth_recovery")
        if not isinstance(policy, dict):
            return False
        if (
            profile.get("schema") != "profile_policy_contract_v1"
            or profile.get("project") != "lark"
            or _has_symlink_component(profile_path)
            or policy.get("status") != "enabled"
            or policy.get("trigger") != DURABLE_RECOVERY_TRIGGER
            or policy.get("ordinary_selfcheck_may_execute") is not False
            or policy.get("task_read_authorized") is not False
            or policy.get("lark_write_authorized") is not False
        ):
            return False
        grant_ref = policy.get("authority_grant_ref")
        if not isinstance(grant_ref, str) or not grant_ref.strip():
            return False
        grant_path = Path(grant_ref).expanduser()
        configured_root = allowed_grant_root.expanduser().absolute()
        if (
            not grant_path.is_absolute()
            or grant_path.parent != configured_root
            or _has_symlink_component(configured_root)
            or _has_symlink_component(grant_path)
            or not grant_path.is_file()
        ):
            return False
        resolved_root = configured_root.resolve()
        resolved_grant = grant_path.resolve()
        resolved_grant.relative_to(resolved_root)
        if resolved_grant.parent != resolved_root:
            return False
        grant_bytes = _read_regular_file_no_symlinks(resolved_grant)
        grant = json.loads(grant_bytes.decode("utf-8"))
        if not isinstance(grant, dict):
            return False
        subject = grant.get("subject")
        expected_profile_ref = str(profile_path.expanduser().absolute())
        return bool(
            isinstance(subject, dict)
            and subject.get("profile_id") == "lark"
            and subject.get("profile_id") == profile.get("project")
            and subject.get("profile_ref") == expected_profile_ref
            and grant.get("schema") == "lark_oauth_recovery_authority_grant_v1"
            and grant.get("grant_id") == grant_path.stem
            and grant.get("status") == "active"
            and grant.get("action") == "auto_singleflight_oauth_recovery"
            and grant.get("scope") == "oauth_recovery_only"
            and grant.get("trigger") == DURABLE_RECOVERY_TRIGGER
            and grant.get("allowed_entrypoints") == [str(ENTRYPOINT)]
            and grant.get("ordinary_selfcheck_may_execute") is False
            and grant.get("no_task_read") is True
            and grant.get("no_lark_write") is True
            and grant.get("no_secret_entry") is True
            and grant.get("no_password_or_otp_entry") is True
            and grant.get("no_external_message_send") is True
            and grant.get("max_concurrent_recoveries") == 1
            and grant.get("max_oauth_pages_per_execution") == 1
            and grant.get("per_execution_authorization_ttl_seconds") == DURABLE_RECOVERY_TTL_SECONDS
            and grant.get("expires_at") is None
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False


def _terminate_process_group(
    proc: subprocess.Popen[str], grace_seconds: float = 2, deadline: float | None = None,
) -> None:
    """Terminate the guard group and always reap its direct child leader."""
    pgid = proc.pid
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    # Preserve at least half of the cleanup budget for SIGKILL + final reap.
    remaining = grace_seconds if deadline is None else max(
        0.0, min(grace_seconds / 2, deadline - time.monotonic())
    )
    if remaining > 0:
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            pass
    # The group may outlive its leader. Probe the process group itself before
    # deciding that SIGTERM completed cleanup.
    group_alive = True
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        group_alive = False
    except PermissionError:
        # We cannot prove the group is gone, so retain fail-closed escalation.
        pass
    if group_alive:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    remaining = grace_seconds if deadline is None else max(0.0, min(grace_seconds, deadline - time.monotonic()))
    if remaining > 0:
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            # Post-timeout status-only readback verifies listener/lock state.
            pass
    else:
        proc.poll()
    for stream in (proc.stdout, proc.stderr):
        if stream is not None:
            stream.close()


def _run_guard_process(cmd: list[str], timeout_seconds: float) -> subprocess.CompletedProcess[str] | None:
    """Run the guard in a process group so timeout cleanup includes descendants."""
    deadline = time.monotonic() + max(0.05, timeout_seconds)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    cleanup_budget = min(4.0, max(0.1, max(0.05, timeout_seconds) * 0.25))
    try:
        remaining = max(0.01, deadline - time.monotonic())
        cleanup_budget = min(cleanup_budget, max(0.01, remaining * 0.25))
        stdout, stderr = proc.communicate(timeout=max(0.01, remaining - cleanup_budget))
    except subprocess.TimeoutExpired:
        _terminate_process_group(proc, grace_seconds=cleanup_budget, deadline=deadline)
        return None
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


def _post_timeout_guard_readback(timeout_seconds: float) -> dict[str, Any]:
    """Bounded status-only readback after killing a timed-out guard group."""
    cmd = [
        sys.executable,
        str(GUARD),
        "--json",
        "--status-only",
        "--no-open",
        "--no-auto-authorize",
        "--timeout",
        "1",
    ]
    if timeout_seconds <= 0:
        return {"ok": False, "action": "post_timeout_readback_skipped_deadline"}
    result = _run_guard_process(cmd, timeout_seconds)
    if result is None:
        return {"ok": False, "action": "post_timeout_readback_failed"}
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "action": "post_timeout_readback_failed"}
    if not isinstance(payload, dict):
        return {"ok": False, "action": "post_timeout_readback_failed"}
    return sanitize_guard_payload(payload)


def run_guard(args: argparse.Namespace) -> dict[str, Any]:
    total_timeout = min(max(args.auth_timeout, 1), DURABLE_RECOVERY_TTL_SECONDS)
    deadline = time.monotonic() + total_timeout
    child_timeout = max(1, total_timeout - 20)
    cmd = [sys.executable, str(GUARD), "--json", "--bound-defaults", "--timeout", str(child_timeout)]
    if getattr(args, "health_check", False):
        cmd.append("--status-only")
    else:
        cmd.append("--cleanup-stale")
    if args.force_refresh:
        cmd.append("--force-refresh")
    if args.no_open:
        cmd.append("--no-open")
    if args.auto_authorize:
        cmd += [
            "--authorized-auto-authorize-profile", str(LARK_PROFILE),
            "--authorized-auto-authorize-grant-root", str(LARK_AUTHORITY_GRANT_ROOT),
            "--auto-authorize-timeout", str(args.auto_authorize_timeout),
        ]
    else:
        cmd.append("--no-auto-authorize")
    process_timeout = min(max(1, child_timeout + 5), max(1, total_timeout - 1))
    readback_timeout = max(1, total_timeout - process_timeout)
    result = _run_guard_process(cmd, min(process_timeout, max(0.05, deadline - time.monotonic())))
    if result is None:
        remaining = max(0.0, deadline - time.monotonic())
        readback = _post_timeout_guard_readback(min(5, readback_timeout, remaining))
        timeout_result: dict[str, Any] = {
            "ok": False,
            "action": "guard_timeout",
            "timeout_seconds": total_timeout,
        }
        token_status = readback.get("token_status")
        if isinstance(token_status, dict) and isinstance(token_status.get("valid"), bool):
            timeout_result["token_status"] = {"valid": token_status["valid"]}
        for field in ("lock_active_after", "port_busy_after"):
            if isinstance(readback.get(field), bool):
                timeout_result[field] = readback[field]
        return timeout_result
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "action": "invalid_guard_json",
        }
    if not isinstance(payload, dict):
        return {"ok": False, "action": "invalid_guard_payload"}
    if result.returncode != 0 or not payload.get("ok"):
        payload.setdefault("ok", False)
        payload.setdefault("returncode", result.returncode)
    return sanitize_guard_payload(payload)


def sanitize_guard_payload(payload: dict[str, Any]) -> dict[str, Any]:
    allowed_fields = {
        "ok", "action", "port", "port_busy", "lock_active", "status_only",
        "planned_action", "opened", "returncode", "timeout_seconds",
        "lock_active_after", "port_busy_after",
    }
    safe = {key: payload[key] for key in allowed_fields if key in payload}
    token_status = payload.get("token_status")
    if isinstance(token_status, dict) and isinstance(token_status.get("valid"), bool):
        safe["token_status"] = {"valid": token_status["valid"]}
    return safe


def guard_post_action_verified(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("ok") is True
        and payload.get("action") in {"token_valid", "token_became_valid", "login_success"}
        and isinstance(payload.get("token_status"), dict)
        and payload["token_status"].get("valid") is True
        and payload.get("lock_active_after") is False
        and payload.get("port_busy_after") is False
    )


def read_one_task(reader: Any, token: str, guid: str, include_comments: bool, include_docs: bool, download_images: bool, image_cache_dir: str) -> dict[str, Any]:
    client = reader.LarkClient()
    data = client.get(f"/task/v2/tasks/{guid}", token)
    if data.get("code") != 0:
        raise RuntimeError(f"Lark task detail API error {data.get('code')}: {data.get('msg')}")
    body = data.get("data") or {}
    task = body.get("task") or body.get("item") or body
    if not isinstance(task, dict) or not task:
        raise RuntimeError(f"Lark task detail response missing task object for guid={guid}")
    enriched = reader.enrich_tasks_with_tasklists([task], token, client=client)[0]
    return reader.payload_from_task(
        token,
        enriched,
        client=client,
        include_comments=include_comments,
        include_docs=include_docs,
        download_images=download_images,
        image_cache_dir=image_cache_dir,
    )


def summarize(payloads: list[dict[str, Any]]) -> str:
    lines = [f"tasks={len(payloads)}"]
    for i, p in enumerate(payloads, 1):
        desc = (p.get("description") or p.get("comments") or "").replace("\n", " ")[:180]
        image_records = p.get("comment_images") or []
        image_summary = ""
        if image_records:
            ok = sum(1 for img in image_records if img.get("status") in {"downloaded", "cached"})
            image_summary = f" | images={ok}/{len(image_records)}"
        lines.append(f"{i}. {p.get('summary')} | guid={p.get('lark_task_guid')} | scope={p.get('lark_task_scope')}{image_summary} | desc={desc}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Unified Lark Task auth+read flow; read-only, no writeback.")
    p.add_argument("--guid", help="Read one task by guid")
    p.add_argument("--url", help="Read one task by Lark applink URL containing guid=")
    p.add_argument("--preferred-scope", action="append", dest="preferred_scopes", help="Preferred Lark task scope/tasklist; default comes from reader")
    p.add_argument("--scope-mode", choices=sorted(load_reader().VALID_SCOPE_MODES), default=None, help="For list mode: prefer/only/off")
    p.add_argument("--no-comments", action="store_true")
    p.add_argument("--no-docs", action="store_true")
    p.add_argument("--download-images", action="store_true")
    p.add_argument("--image-cache-dir", default=str(load_reader().DEFAULT_IMAGE_CACHE_DIR))
    p.add_argument("--summary", action="store_true", help="Print compact human-readable summary instead of JSON")
    p.add_argument("--auth-only", action="store_true", help="Only run/verify OAuth guard; do not read tasks")
    p.add_argument(
        "--health-check",
        action="store_true",
        help="Status-only OAuth/token check: never opens a browser, auto-authorizes, or reads tasks",
    )
    p.add_argument("--no-auto-authorize", dest="auto_authorize", action="store_false", help="Open auth URL but do not auto-click visible 授权 button")
    p.add_argument("--no-open", action="store_true", help="Do not open a browser; this does not make the flow status-only")
    p.add_argument("--force-refresh", action="store_true")
    p.add_argument("--auth-timeout", type=int, default=120)
    p.add_argument("--auto-authorize-timeout", type=int, default=25)
    p.set_defaults(auto_authorize=oauth_recovery_auto_authorized())
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.auto_authorize:
        if args.force_refresh or not args.auth_only:
            args.auto_authorize = False
        else:
            args.auth_timeout = min(max(args.auth_timeout, 1), DURABLE_RECOVERY_TTL_SECONDS)
            args.auto_authorize_timeout = min(max(args.auto_authorize_timeout, 1), args.auth_timeout)
    if args.health_check:
        args.auth_only = True
        args.no_open = True
        args.auto_authorize = False
        args.force_refresh = False
        args.auth_timeout = min(args.auth_timeout, 5)
    try:
        guid = extract_guid(args.guid or args.url)
        auth = run_guard(args)
        zero_side_effect_boundary = {
            "auto_authorize_enabled": bool(args.auto_authorize),
            "task_read_executed": False,
            "lark_write_executed": False,
        }
        if not auth.get("ok"):
            result = {
                "ok": False,
                "stage": "auth",
                "auth": auth,
                "side_effect_boundary": zero_side_effect_boundary,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 1
        if not guard_post_action_verified(auth):
            result = {
                "ok": False,
                "stage": "auth",
                "auth": {"ok": False, "action": "guard_post_action_unverified"},
                "side_effect_boundary": zero_side_effect_boundary,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 1
        if args.auth_only:
            print(json.dumps({
                "ok": True,
                "stage": "auth",
                "auth": auth,
                "side_effect_boundary": zero_side_effect_boundary,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        reader = load_reader()
        token = reader.get_token(auto_auth=False)
        if guid:
            payloads = [read_one_task(reader, token, guid, not args.no_comments, not args.no_docs, args.download_images, args.image_cache_dir)]
        else:
            payloads = reader.collect_tasks(
                token=token,
                preferred_scopes=args.preferred_scopes,
                scope_mode=args.scope_mode,
                include_comments=not args.no_comments,
                include_docs=not args.no_docs,
                auto_auth=False,
                auto_authorize=False,
                download_images=args.download_images,
                image_cache_dir=args.image_cache_dir,
            )
        if args.summary:
            print(summarize(payloads))
        else:
            print(json.dumps({"ok": True, "stage": "read", "auth_action": auth.get("action"), "tasks": payloads}, ensure_ascii=False, indent=2))
        return 0
    except Exception:
        print(json.dumps({"ok": False, "stage": "error", "error_code": "unhandled_flow_error"}, ensure_ascii=False, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
