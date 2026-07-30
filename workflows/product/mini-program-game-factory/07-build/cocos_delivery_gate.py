#!/usr/bin/env python3
"""Fail-closed Cocos build planning and developer-tool handoff verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Optional

from cocos_project_generator import verify_generated_project

TARGETS = {"wechat": "wechatgame", "douyin": "bytedance-mini-game"}
KNOWN_CREATOR_PATHS = (
    Path("/Applications/CocosCreator.app/Contents/MacOS/CocosCreator"),
)


class DeliveryGateError(ValueError):
    pass


HANDOFF_KEYS = {
    "schema_version", "status", "platform", "project_digest",
    "serialization_creator_version", "creator_editor_version_readback",
    "creator_build_target", "build_binding", "artifact", "readbacks",
    "external_stages", "authority",
}
BUILD_BINDING_KEYS = {
    "creator_executable_path", "creator_executable_sha256",
    "build_config_path", "build_config_sha256", "creator_editor_version_readback",
}
HANDOFF_AUTHORITY_KEYS = {"may_invoke_devtools", "may_submit_platform", "may_publish"}
EXTERNAL_STAGE_KEYS = {"upload", "review", "publish", "rollback"}


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _creator_executable(explicit: Optional[Path]) -> Optional[Path]:
    candidates = [Path(explicit)] if explicit is not None else list(KNOWN_CREATOR_PATHS)
    for candidate in candidates:
        if candidate.is_symlink():
            continue
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None


def _is_creator_38_patch(version: Any) -> bool:
    return isinstance(version, str) and re.fullmatch(r"3\.8\.\d+", version) is not None


def _verify_bound_file(
    path_value: Any,
    expected_sha256: Any,
    label: str,
    *,
    executable: bool = False,
) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise DeliveryGateError(f"handoff {label} path is missing")
    path = Path(path_value)
    if not path.is_absolute():
        raise DeliveryGateError(f"handoff {label} path must be absolute")
    if path.is_symlink():
        raise DeliveryGateError(f"handoff {label} symlink is rejected")
    if not path.is_file():
        raise DeliveryGateError(f"handoff {label} does not exist")
    if executable and not os.access(path, os.X_OK):
        raise DeliveryGateError(f"handoff {label} is not executable")
    if not isinstance(expected_sha256, str) or _sha256(path) != expected_sha256:
        raise DeliveryGateError(f"handoff {label} digest mismatch")
    return path.resolve()


def _verify_build_config(path: Optional[Path], target: str, app_id: Optional[str]) -> tuple[Optional[Path], Optional[str]]:
    if path is None:
        return None, "creator_build_config_export_required"
    path = Path(path)
    if path.is_symlink():
        return None, "creator_build_config_symlink_rejected"
    if not path.is_file():
        return None, "creator_build_config_export_required"
    try:
        config = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None, "creator_build_config_invalid"
    package = config.get("packages", {}).get(target, {}) if isinstance(config, dict) else {}
    if config.get("taskName") != target or package.get("appid") != app_id:
        return None, "creator_build_config_target_or_appid_mismatch"
    return path.resolve(), None


def build_preflight(
    project_root: Path,
    platform: str,
    *,
    creator_executable: Optional[Path] = None,
    creator_editor_version_readback: Optional[str] = None,
    build_config: Optional[Path] = None,
    app_id: Optional[str] = None,
    authority_granted: bool = False,
) -> Mapping[str, Any]:
    if platform not in TARGETS:
        raise DeliveryGateError(f"unsupported platform: {platform}")
    project_root = Path(project_root).resolve()
    manifest = verify_generated_project(project_root)
    target = TARGETS[platform]
    executable = _creator_executable(creator_executable)
    blockers: list[str] = []
    if executable is None:
        blockers.append("creator_cli_unavailable")
    if not _is_creator_38_patch(creator_editor_version_readback):
        blockers.append("creator_editor_version_unverified")
    if not app_id:
        blockers.append("appid_required")
    config_path, config_error = _verify_build_config(build_config, target, app_id)
    if config_error:
        blockers.append(config_error)
    if not authority_granted:
        blockers.append("build_authority_closed")
    ready = not blockers
    command = None
    if ready:
        command = [
            str(executable),
            "--project",
            str(project_root),
            "--build",
            f"configPath={config_path};",
        ]
    return {
        "schema_version": 1,
        "closure_state": "ready_to_build" if ready else "build_preflight_blocked",
        "project_digest": manifest["project_digest"],
        "serialization_creator_version": manifest["creator_version"],
        "platform": platform,
        "creator_build_target": target,
        "creator_executable": str(executable) if executable else None,
        "creator_executable_sha256": _sha256(executable) if executable else None,
        "creator_editor_version_readback": creator_editor_version_readback,
        "build_config": str(config_path) if config_path else None,
        "build_config_sha256": _sha256(config_path) if config_path else None,
        "appid_present": bool(app_id),
        "blocking_reasons": blockers,
        "command": command,
        "authority": {"may_build": ready, "may_invoke_devtools": False, "may_publish": False},
    }


def verify_devtools_handoff(receipt: Mapping[str, Any], project_root: Path) -> Mapping[str, Any]:
    if not isinstance(receipt, Mapping) or set(receipt) != HANDOFF_KEYS:
        raise DeliveryGateError("handoff fields are incomplete or contain unknown fields")
    if receipt.get("schema_version") != 1:
        raise DeliveryGateError("handoff schema_version must be 1")
    manifest = verify_generated_project(Path(project_root))
    platform = receipt.get("platform")
    if platform not in TARGETS:
        raise DeliveryGateError("handoff platform is unsupported")
    if receipt.get("status") != "human_verified":
        raise DeliveryGateError("handoff status must be human_verified")
    if receipt.get("project_digest") != manifest["project_digest"]:
        raise DeliveryGateError("handoff project_digest mismatch")
    if receipt.get("serialization_creator_version") != manifest["creator_version"]:
        raise DeliveryGateError("handoff serialization_creator_version mismatch")
    editor_version = receipt.get("creator_editor_version_readback")
    if not _is_creator_38_patch(editor_version):
        raise DeliveryGateError("handoff creator_editor_version_readback must be an exact 3.8.x patch readback")
    build_binding = receipt.get("build_binding")
    if not isinstance(build_binding, Mapping) or set(build_binding) != BUILD_BINDING_KEYS:
        raise DeliveryGateError("handoff build_binding fields are incomplete or unknown")
    if build_binding.get("creator_editor_version_readback") != editor_version:
        raise DeliveryGateError("handoff editor version binding mismatch")
    creator_executable_path = _verify_bound_file(
        build_binding.get("creator_executable_path"),
        build_binding.get("creator_executable_sha256"),
        "creator executable",
        executable=True,
    )
    build_config_path = _verify_bound_file(
        build_binding.get("build_config_path"),
        build_binding.get("build_config_sha256"),
        "build config",
    )
    if receipt.get("creator_build_target") != TARGETS[platform]:
        raise DeliveryGateError("handoff creator_build_target mismatch")
    required_readbacks = {
        "creator_build_exit_code": 36,
        "devtools_import": True,
        "simulator_compile": True,
        "real_device_preview": True,
    }
    readbacks = receipt.get("readbacks", {})
    if not isinstance(readbacks, Mapping) or set(readbacks) != set(required_readbacks):
        raise DeliveryGateError("handoff readback fields are incomplete or unknown")
    for name, expected in required_readbacks.items():
        if readbacks.get(name) != expected:
            raise DeliveryGateError(f"handoff readback mismatch: {name} must be {expected!r}")
    artifact = receipt.get("artifact", {})
    if not isinstance(artifact, Mapping) or set(artifact) != {"path", "sha256", "bytes"}:
        raise DeliveryGateError("handoff artifact fields are incomplete or unknown")
    path_value = artifact.get("path")
    if not path_value:
        raise DeliveryGateError("handoff artifact path is missing")
    path = Path(path_value)
    if not path.is_absolute():
        raise DeliveryGateError("handoff artifact path must be absolute")
    if path.is_symlink():
        raise DeliveryGateError("handoff artifact symlink is rejected")
    if not path.is_file():
        raise DeliveryGateError("handoff artifact does not exist")
    actual_sha = _sha256(path)
    actual_bytes = path.stat().st_size
    if artifact.get("sha256") != actual_sha or artifact.get("bytes") != actual_bytes:
        raise DeliveryGateError("handoff artifact digest or size mismatch")
    authority = receipt.get("authority", {})
    if not isinstance(authority, Mapping) or set(authority) != HANDOFF_AUTHORITY_KEYS:
        raise DeliveryGateError("handoff authority fields are incomplete or unknown")
    if any(value is not False for value in authority.values()):
        raise DeliveryGateError("handoff leaves future authority open")
    external_stages = receipt.get("external_stages", {})
    if not isinstance(external_stages, Mapping) or set(external_stages) != EXTERNAL_STAGE_KEYS:
        raise DeliveryGateError("handoff external stage fields are incomplete or unknown")
    if any(value != "not_started" for value in external_stages.values()):
        raise DeliveryGateError("handoff cannot claim upload, review, publish or rollback")
    return {
        "schema_version": 1,
        "closure_state": "devtools_handoff_receipt_integrity_verified",
        "claim_boundary": "verifies receipt structure, bindings, artifact integrity, and supplied human readbacks; does not independently observe Creator, DevTools, simulator, or device execution",
        "project_digest": manifest["project_digest"],
        "serialization_creator_version": manifest["creator_version"],
        "creator_editor_version_readback": editor_version,
        "platform": platform,
        "creator_build_target": receipt["creator_build_target"],
        "build_binding": {
            "creator_executable_path": str(creator_executable_path),
            "creator_executable_sha256": build_binding["creator_executable_sha256"],
            "build_config_path": str(build_config_path),
            "build_config_sha256": build_binding["build_config_sha256"],
            "creator_editor_version_readback": editor_version,
        },
        "artifact": {"path": str(path.resolve()), "sha256": actual_sha, "bytes": actual_bytes},
        "readbacks": dict(required_readbacks),
        "authority": {"may_submit_platform": False, "may_publish": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--project", type=Path, required=True)
    preflight.add_argument("--platform", choices=sorted(TARGETS), required=True)
    preflight.add_argument("--creator", type=Path)
    preflight.add_argument("--creator-version")
    preflight.add_argument("--config", type=Path)
    preflight.add_argument("--appid")
    handoff = subparsers.add_parser("verify-handoff")
    handoff.add_argument("--project", type=Path, required=True)
    handoff.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "preflight":
        result = build_preflight(
            args.project,
            args.platform,
            creator_executable=args.creator,
            creator_editor_version_readback=args.creator_version,
            build_config=args.config,
            app_id=args.appid,
            authority_granted=False,
        )
    else:
        result = verify_devtools_handoff(json.loads(args.receipt.read_text()), args.project)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["closure_state"] != "build_preflight_blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
