#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Mapping


class IntegrationError(ValueError):
    pass


AUTHORITY_FIELDS = {
    "may_build_cocos",
    "may_invoke_devtools",
    "may_enter_credentials",
    "may_preview_device",
    "may_submit_platform",
    "may_publish",
    "may_pay",
}
EXPECTED_PLATFORMS = {"douyin", "wechat"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _verify_embedded_digest(value: Mapping[str, Any], field: str) -> None:
    claimed = value.get(field)
    payload = dict(value)
    payload.pop(field, None)
    if not isinstance(claimed, str) or claimed != digest(payload):
        raise IntegrationError(f"{field} does not match canonical payload")


def _validate_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("engine_family") != "cocos-creator":
        raise IntegrationError("engine_family must be cocos-creator")
    if profile.get("version_line") != "3.8":
        raise IntegrationError("version_line must be pinned to 3.8")
    source_commit = profile.get("source_commit")
    if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise IntegrationError("source_commit must be a pinned 40-character Git commit")
    if profile.get("creator_cli_state") != "unavailable":
        raise IntegrationError("creator_cli_state must remain unavailable until runtime readback exists")

    authority = profile.get("authority")
    if not isinstance(authority, Mapping) or set(authority) != AUTHORITY_FIELDS:
        raise IntegrationError("authority inventory is incomplete")
    if any(value is not False for value in authority.values()):
        raise IntegrationError("authority must remain closed")

    platforms = profile.get("platforms")
    if not isinstance(platforms, list):
        raise IntegrationError("platforms must be a list")
    if {item.get("platform_id") for item in platforms if isinstance(item, Mapping)} != EXPECTED_PLATFORMS:
        raise IntegrationError("platforms must contain exactly douyin and wechat")
    for item in platforms:
        if not isinstance(item, Mapping):
            raise IntegrationError("platform entries must be objects")
        if item.get("official_contract_state") != "contract_pending":
            raise IntegrationError("official platform contract must remain pending")
        if item.get("build_state") != "build_pending" or item.get("build_target_id") is not None:
            raise IntegrationError("build target must remain unresolved and pending")


def _validate_packet(packet: Mapping[str, Any]) -> None:
    if packet.get("closure_state") != "cocos_integration_planned":
        raise IntegrationError("integration packet has an invalid closure_state")
    if packet.get("candidate_only") is not True:
        raise IntegrationError("integration packet must remain candidate_only")
    authority = packet.get("authority")
    if not isinstance(authority, Mapping) or set(authority) != AUTHORITY_FIELDS:
        raise IntegrationError("integration packet authority inventory is incomplete")
    if any(value is not False for value in authority.values()):
        raise IntegrationError("integration packet authority must remain closed")
    engine = packet.get("engine")
    if not isinstance(engine, Mapping):
        raise IntegrationError("integration packet engine is missing")
    if engine.get("family") != "cocos-creator" or engine.get("version_line") != "3.8":
        raise IntegrationError("integration packet engine must remain cocos-creator 3.8")
    if engine.get("creator_cli_state") != "unavailable":
        raise IntegrationError("integration packet cannot assert Creator CLI availability")
    platforms = packet.get("platforms")
    if not isinstance(platforms, list) or {
        item.get("platform_id") for item in platforms if isinstance(item, Mapping)
    } != EXPECTED_PLATFORMS:
        raise IntegrationError("integration packet platform inventory is invalid")
    for item in platforms:
        if (
            not isinstance(item, Mapping)
            or item.get("official_contract_state") != "contract_pending"
            or item.get("build_state") != "build_pending"
            or item.get("build_target_id") is not None
        ):
            raise IntegrationError("integration packet platform state must remain pending")
    materialization = packet.get("materialization_contract")
    if not isinstance(materialization, Mapping) or materialization.get("cocos_project_mutation") is not False:
        raise IntegrationError("integration packet cannot authorize Cocos project mutation")


def compile_cocos_integration(
    work_package: Mapping[str, Any], profile: Mapping[str, Any]
) -> Dict[str, Any]:
    _verify_embedded_digest(work_package, "compile_digest")
    _validate_profile(profile)
    if work_package.get("closure_state") != "work_package_compiled":
        raise IntegrationError("work package is not in work_package_compiled state")
    accuracy = work_package.get("accuracy_contract", {})
    if not isinstance(accuracy, Mapping) or accuracy.get("candidate_only") is not True:
        raise IntegrationError("work package must remain candidate_only")
    upstream_authority = work_package.get("authority", {})
    if not isinstance(upstream_authority, Mapping) or any(value is not False for value in upstream_authority.values()):
        raise IntegrationError("upstream authority must remain closed")

    packet: Dict[str, Any] = {
        "schema_version": 1,
        "integration_id": f"{work_package['work_package_id']}::cocos-creator-3.8",
        "closure_state": "cocos_integration_planned",
        "candidate_only": True,
        "source_compile_digest": work_package["compile_digest"],
        "engine": {
            "family": profile["engine_family"],
            "version_line": profile["version_line"],
            "source_repository": profile["source_repository"],
            "source_commit": profile["source_commit"],
            "source_license": profile["source_license"],
            "creator_cli_state": profile["creator_cli_state"],
        },
        "platforms": profile["platforms"],
        "materialization_contract": {
            "writes_local_candidate_only": True,
            "cocos_project_mutation": False,
            "generated_files": [
                "input/work-package.json",
                "generated/gameplay-kernel.json",
                "generated/content-pack.json",
                "integration-packet.json",
            ],
        },
        "required_next_receipts": [
            "creator_installation_readback",
            "exact_creator_version",
            "official_platform_contract",
            "exact_build_target",
            "creator_build_receipt",
            "devtools_import_receipt",
            "real_device_preview_receipt",
        ],
        "authority": dict(profile["authority"]),
    }
    packet["integration_digest"] = digest(packet)
    return packet


def _render(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def materialize_candidate(
    work_package: Mapping[str, Any], packet: Mapping[str, Any], output_root: Path
) -> Dict[str, Any]:
    _verify_embedded_digest(work_package, "compile_digest")
    _verify_embedded_digest(packet, "integration_digest")
    _validate_packet(packet)
    if packet.get("source_compile_digest") != work_package.get("compile_digest"):
        raise IntegrationError("integration packet is not bound to the work package")

    root = Path(output_root)
    if root.is_symlink():
        raise IntegrationError("materialization root must not be a symbolic link")
    if root.exists():
        raise IntegrationError("materialization root must not already exist")
    if not root.parent.exists() or not root.parent.is_dir() or root.parent.is_symlink():
        raise IntegrationError("materialization parent must be an existing non-symlink directory")

    files = {
        "input/work-package.json": work_package,
        "generated/gameplay-kernel.json": work_package["kernel"],
        "generated/content-pack.json": work_package["content"],
        "integration-packet.json": packet,
    }
    root.mkdir()
    file_receipts: Dict[str, Dict[str, Any]] = {}
    for relative, value in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        rendered = _render(value)
        target.write_bytes(rendered)
        file_receipts[relative] = {
            "sha256": hashlib.sha256(rendered).hexdigest(),
            "bytes": len(rendered),
        }

    manifest: Dict[str, Any] = {
        "schema_version": 1,
        "closure_state": "cocos_candidate_materialized",
        "candidate_only": True,
        "integration_digest": packet["integration_digest"],
        "source_compile_digest": work_package["compile_digest"],
        "files": file_receipts,
        "authority": dict(packet["authority"]),
    }
    manifest["manifest_digest"] = digest(manifest)
    (root / "candidate-manifest.json").write_bytes(_render(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile and materialize a local Cocos candidate bundle")
    parser.add_argument("--work-package", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    try:
        work_package = json.loads(Path(args.work_package).read_text(encoding="utf-8"))
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
        packet = compile_cocos_integration(work_package, profile)
        receipt = materialize_candidate(work_package, packet, Path(args.output_root))
    except (OSError, KeyError, TypeError, json.JSONDecodeError, IntegrationError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
