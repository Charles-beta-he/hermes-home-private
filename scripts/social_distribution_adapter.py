#!/usr/bin/env python3
"""Governed social distribution dry-run adapter for Hermes/Solo Pipeline.

This script intentionally stays at an external CLI/API boundary for OSS tools:
- MatrixMedia (GPL-2.0): call `matrixmedia cli ...`, never copy source.
- Postiz/Postiz app (Postiz app AGPL): call `postiz ...` / API boundary, never copy source.

Default behavior is dry-run / draft planning only. Public publishing is blocked unless a
future, separately audited human-approval executor is added.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional

MEDIA_TYPES = {"image", "video"}
SAFE_MODES = {"dry-run", "draft", "fill", "preview"}
PUBLISH_MODES = {"publish"}
MATRIXMEDIA_PLATFORM_ALIASES = {
    "douyin": "dy",
    "dy": "dy",
    "toutiao": "tt",
    "tt": "tt",
    "kuaishou": "ks",
    "ks": "ks",
    "bilibili": "blbl",
    "blbl": "blbl",
    "baijiahao": "bjh",
    "bjh": "bjh",
    "shipinhao": "sph",
    "sph": "sph",
    "wechat_channels": "sph",
    "xhs": "xhs",
    "xiaohongshu": "xhs",
}


def _default_media_exists(path: str) -> bool:
    return Path(path).expanduser().exists()


def _default_command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def validate_publish_package(
    package: Mapping[str, Any],
    *,
    media_exists: Callable[[str], bool] = _default_media_exists,
    allow_publish: bool = False,
) -> Dict[str, Any]:
    """Validate platform-neutral publish package safety and shape."""
    errors: List[str] = []
    warnings: List[str] = []

    title = str(package.get("title") or "").strip()
    if not title:
        errors.append("missing_title")

    media = _as_list(package.get("media"))
    if not media:
        errors.append("missing_media")
    for idx, item in enumerate(media):
        if not isinstance(item, Mapping):
            errors.append(f"media_{idx}_not_object")
            continue
        media_type = item.get("type")
        path = str(item.get("path") or "")
        if media_type not in MEDIA_TYPES:
            errors.append(f"media_{idx}_unsupported_type")
        if not path:
            errors.append(f"media_{idx}_missing_path")
        elif not media_exists(path):
            errors.append(f"media_{idx}_path_missing:{path}")

    targets = _as_list(package.get("targets"))
    if not targets:
        errors.append("missing_targets")
    for idx, target in enumerate(targets):
        if not isinstance(target, Mapping):
            errors.append(f"target_{idx}_not_object")
            continue
        if not target.get("adapter"):
            errors.append(f"target_{idx}_missing_adapter")
        if not target.get("platform"):
            errors.append(f"target_{idx}_missing_platform")
        mode = str(target.get("mode") or "dry-run")
        if mode in PUBLISH_MODES and not allow_publish:
            errors.append("publish_requires_explicit_approval")
        elif mode not in SAFE_MODES and mode not in PUBLISH_MODES:
            errors.append(f"target_{idx}_unsupported_mode:{mode}")
        if mode != "publish" and target.get("auto_publish") is True:
            errors.append("auto_publish_flag_forbidden_in_safe_mode")

    if package.get("license_boundary") in (None, ""):
        warnings.append("license_boundary_not_declared_defaulting_external_cli")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


class MatrixMediaAdapter:
    """Plan MatrixMedia CLI calls without executing public publish."""

    name = "matrixmedia"

    def __init__(self, binary: str = "matrixmedia") -> None:
        self.binary = binary

    def plan(
        self,
        package: Mapping[str, Any],
        target: Mapping[str, Any],
        *,
        media_exists: Callable[[str], bool] = _default_media_exists,
        command_exists: Callable[[str], bool] = _default_command_exists,
    ) -> Dict[str, Any]:
        validation = validate_publish_package(package, media_exists=media_exists)
        platform = MATRIXMEDIA_PLATFORM_ALIASES.get(str(target.get("platform") or "").lower(), str(target.get("platform") or ""))
        mode = str(target.get("mode") or "dry-run")
        account = str(target.get("account") or target.get("phone") or "")
        media_path = _first_media_path(package, preferred_type="video")
        tags = package.get("tags") or []
        if isinstance(tags, str):
            tag_arg = tags
        else:
            tag_arg = ",".join(str(t).lstrip("#") for t in tags)

        mapped_payload = {
            "platform": platform,
            "title": package.get("title"),
            "body": package.get("body", ""),
            "tags": tag_arg,
            "media_path": media_path,
            "cover": package.get("cover"),
            "account": account,
            "publish_at": target.get("publish_at") or target.get("publishAt"),
        }

        publish_preview = [
            self.binary,
            "cli",
            "publish",
            "-p",
            platform,
            "--phone",
            account,
            "-f",
            str(media_path),
            "-t",
            str(package.get("title") or ""),
        ]
        if tag_arg:
            publish_preview.extend(["--tags", tag_arg])
        if mapped_payload["publish_at"]:
            publish_preview.extend(["--publish-at", str(mapped_payload["publish_at"])])
        # MatrixMedia does not document a universal dry-run flag today; this preview
        # command is not executed. Keep the marker in the evidence bundle so a human
        # can see this was a non-executing plan, not a publish invocation.
        publish_preview.append("--dry-run")

        login_check = {
            "command_preview": [self.binary, "cli", "accounts", "-p", platform, "--json"],
            "status": "unknown_binary_missing" if not command_exists(self.binary) else "not_executed_dry_run",
            "human_login_required_for_non_douyin": platform != "dy",
        }
        return {
            "ok": validation["ok"] and mode in SAFE_MODES,
            "adapter": self.name,
            "platform": platform,
            "mode": mode,
            "will_publish": False,
            "license_boundary": "external_cli_only_gpl2_no_source_copy",
            "validation": validation,
            "login_check": login_check,
            "mapped_payload": mapped_payload,
            "commands": {"publish_preview": publish_preview},
        }


class PostizAdapter:
    """Plan Postiz CLI/API-boundary calls without publishing."""

    name = "postiz"

    def __init__(self, binary: str = "postiz") -> None:
        self.binary = binary

    def plan(
        self,
        package: Mapping[str, Any],
        target: Mapping[str, Any],
        *,
        media_exists: Callable[[str], bool] = _default_media_exists,
        command_exists: Callable[[str], bool] = _default_command_exists,
    ) -> Dict[str, Any]:
        validation = validate_publish_package(package, media_exists=media_exists)
        mode = str(target.get("mode") or "draft")
        integration_id = str(target.get("integration_id") or target.get("integrationId") or "")
        content = str(package.get("body") or package.get("title") or "")
        media_arg = ",".join(str(m.get("path")) for m in _as_list(package.get("media")) if isinstance(m, Mapping) and m.get("path"))
        command = [self.binary, "posts:create", "-c", content, "-t", "draft", "-i", integration_id]
        if media_arg:
            command.extend(["-m", media_arg])
        if target.get("schedule_at"):
            command.extend(["-s", str(target["schedule_at"])])
        return {
            "ok": validation["ok"] and mode in SAFE_MODES and bool(integration_id),
            "adapter": self.name,
            "platform": str(target.get("platform") or "postiz"),
            "mode": mode,
            "will_publish": False,
            "license_boundary": "external_cli_or_api_only_postiz_app_agpl_no_source_copy",
            "validation": validation,
            "login_check": {
                "command_preview": [self.binary, "auth:status"],
                "status": "unknown_binary_missing" if not command_exists(self.binary) else "not_executed_dry_run",
            },
            "mapped_payload": {
                "content": content,
                "integration_id": integration_id,
                "media": media_arg,
                "post_type": "draft",
            },
            "commands": {"create_draft_preview": command},
        }


def _first_media_path(package: Mapping[str, Any], preferred_type: Optional[str] = None) -> str:
    media = _as_list(package.get("media"))
    if preferred_type:
        for item in media:
            if isinstance(item, Mapping) and item.get("type") == preferred_type and item.get("path"):
                return str(item["path"])
    for item in media:
        if isinstance(item, Mapping) and item.get("path"):
            return str(item["path"])
    return ""


def adapter_for(target: Mapping[str, Any]):
    adapter = str(target.get("adapter") or "").lower()
    if adapter == "matrixmedia":
        return MatrixMediaAdapter(binary=str(target.get("binary") or "matrixmedia"))
    if adapter == "postiz":
        return PostizAdapter(binary=str(target.get("binary") or "postiz"))
    raise ValueError(f"unsupported_adapter:{adapter}")


def dry_run(package: Mapping[str, Any]) -> Dict[str, Any]:
    validation = validate_publish_package(package)
    results: List[Dict[str, Any]] = []
    if validation["ok"]:
        for target in _as_list(package.get("targets")):
            try:
                results.append(adapter_for(target).plan(package, target))
            except Exception as exc:  # keep evidence readable; caller gets ok=false
                results.append({"ok": False, "adapter": target.get("adapter"), "error": str(exc)})
    return {
        "ok": validation["ok"] and all(r.get("ok") for r in results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "safety": {
            "default_public_publish": "blocked_without_explicit_approval",
            "human_control_boundary": "human_only_no_secret_entry",
            "source_license_policy": "use_external_cli_api_mcp_boundary_for_gpl_agpl",
        },
        "package_validation": validation,
        "results": results,
    }


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit("package JSON must be an object")
    return data


def command_dry_run(args: argparse.Namespace) -> int:
    package = _load_json(Path(args.package).expanduser())
    result = dry_run(package)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes governed social distribution dry-run adapter")
    sub = parser.add_subparsers(dest="command", required=True)
    dry = sub.add_parser("dry-run", help="Validate a publish-package and emit adapter command previews without publishing")
    dry.add_argument("--package", required=True, help="Path to publish-package.json")
    dry.add_argument("--out", help="Optional output evidence JSON path")
    dry.set_defaults(func=command_dry_run)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
