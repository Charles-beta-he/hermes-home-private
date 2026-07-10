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
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path.home() / ".hermes" / "scripts"
GUARD = SCRIPTS_DIR / "lark_oauth_guard.py"
READER = SCRIPTS_DIR / "lark_task_reader.py"
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


def run_guard(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [sys.executable, str(GUARD), "--json", "--timeout", str(args.auth_timeout)]
    if getattr(args, "health_check", False):
        cmd.append("--status-only")
    else:
        cmd.append("--cleanup-stale")
    if args.force_refresh:
        cmd.append("--force-refresh")
    if args.no_open:
        cmd.append("--no-open")
    if args.auto_authorize:
        cmd.append("--auto-authorize")
    if args.auto_authorize_timeout is not None:
        cmd += ["--auto-authorize-timeout", str(args.auto_authorize_timeout)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=args.auth_timeout + 20)
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "action": "guard_timeout",
            "timeout_seconds": args.auth_timeout + 20,
            "stdout_tail": ((exc.stdout or "")[-500:] if isinstance(exc.stdout, str) else ""),
            "stderr_tail": ((exc.stderr or "")[-500:] if isinstance(exc.stderr, str) else ""),
        }
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "action": "invalid_guard_json",
            "stdout_tail": result.stdout[-500:],
            "stderr_tail": result.stderr[-500:],
        }
    if result.returncode != 0 or not payload.get("ok"):
        payload.setdefault("ok", False)
        payload.setdefault("returncode", result.returncode)
    return payload


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
    p.add_argument("--no-open", action="store_true", help="Status-only/no browser; incompatible with auto-authorize when refresh is needed")
    p.add_argument("--force-refresh", action="store_true")
    p.add_argument("--auth-timeout", type=int, default=120)
    p.add_argument("--auto-authorize-timeout", type=int, default=25)
    p.set_defaults(auto_authorize=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.health_check:
        args.auth_only = True
        args.no_open = True
        args.auto_authorize = False
        args.force_refresh = False
        args.auth_timeout = min(args.auth_timeout, 5)
    try:
        guid = extract_guid(args.guid or args.url)
        auth = run_guard(args)
        if not auth.get("ok"):
            result = {"ok": False, "stage": "auth", "auth": auth}
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 1
        if args.auth_only:
            print(json.dumps({"ok": True, "stage": "auth", "auth": auth}, ensure_ascii=False, indent=2, sort_keys=True))
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
    except Exception as exc:
        print(json.dumps({"ok": False, "stage": "error", "error": str(exc)}, ensure_ascii=False, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
