#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Mapping

from gameplay_architecture_profiles import (
    ArchitectureProfileError,
    validate_kernel_architecture,
)
from work_package_compiler import (
    CANONICAL_ROUTING_PATH,
    CompileError,
    compile_work_package,
)


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
PROFILE_FIELDS = {
    "schema_version",
    "profile_id",
    "engine_family",
    "version_line",
    "source_repository",
    "source_commit",
    "source_license",
    "creator_cli_state",
    "platforms",
    "authority",
}
PLATFORM_FIELDS = {
    "platform_id",
    "runtime_api_namespace",
    "engine_source_state",
    "official_contract_state",
    "build_target_id",
    "build_state",
}
PACKET_FIELDS = {
    "schema_version",
    "integration_id",
    "closure_state",
    "candidate_only",
    "source_compile_digest",
    "engine",
    "platforms",
    "materialization_contract",
    "required_next_receipts",
    "authority",
    "integration_digest",
}
ENGINE_FIELDS = {
    "family",
    "version_line",
    "source_repository",
    "source_commit",
    "source_license",
    "creator_cli_state",
}
MATERIALIZATION_FIELDS = {
    "writes_local_candidate_only",
    "cocos_project_mutation",
    "generated_files",
}
GENERATED_FILES = [
    "input/work-package.json",
    "generated/gameplay-kernel.json",
    "generated/content-pack.json",
    "integration-packet.json",
]
REQUIRED_NEXT_RECEIPTS = [
    "creator_installation_readback",
    "exact_creator_version",
    "official_platform_contract",
    "exact_build_target",
    "creator_build_receipt",
    "devtools_import_receipt",
    "real_device_preview_receipt",
]
CANONICAL_PROFILE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "cocos" / "cocos-integration-profile.json"
EXPECTED_PLATFORMS = {"douyin", "wechat"}
WORK_PACKAGE_FIELDS = {
    "schema_version",
    "work_package_id",
    "closure_state",
    "model_route",
    "kernel_digest",
    "content_digest",
    "architecture_profile",
    "kernel",
    "content",
    "generation",
    "required_gates",
    "authority",
    "accuracy_contract",
    "compile_digest",
}
WORK_PACKAGE_AUTHORITY_FIELDS = {
    "may_publish",
    "may_submit_platform",
    "may_enter_credentials",
    "may_pay",
}
KERNEL_FIELDS = {
    "kernel_id",
    "version",
    "architecture_profile",
    "state_fields",
    "actions",
    "win_condition",
    "lose_condition",
    "score_rule",
    "seed_policy",
    "tunable_parameters",
    "golden_cases",
}


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
    if not isinstance(value, Mapping):
        raise IntegrationError(f"{field} carrier must be an object")
    claimed = value.get(field)
    payload = dict(value)
    payload.pop(field, None)
    if not isinstance(claimed, str) or claimed != digest(payload):
        raise IntegrationError(f"{field} does not match canonical payload")


def _require_nonempty_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise IntegrationError(f"{name} must be a nonempty string")
    return value


def _require_list_of_nonempty_str(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise IntegrationError(f"{name} must be a list of strings")
    for item in value:
        if not isinstance(item, str) or not item:
            raise IntegrationError(f"{name} items must be nonempty strings")
    return value


def _require_mapping_with_exact_keys(value: Any, expected: set[str], name: str) -> None:
    if not isinstance(value, Mapping):
        raise IntegrationError(f"{name} must be an object")
    if set(value.keys()) != expected:
        raise IntegrationError(f"{name} must use the exact field inventory {sorted(expected)}")


def _assert_no_untrusted_symlink_ancestor(parent: Path) -> None:
    absolute_parent = parent.absolute()
    anchors = [Path.cwd().absolute(), Path.home().absolute(), Path(tempfile.gettempdir()).absolute()]
    eligible = []
    for anchor in anchors:
        try:
            absolute_parent.relative_to(anchor)
        except ValueError:
            continue
        eligible.append(anchor)
    if not eligible:
        raise IntegrationError("materialization parent is outside trusted local roots")
    anchor = max(eligible, key=lambda value: len(value.parts))
    cursor = anchor
    for part in absolute_parent.relative_to(anchor).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise IntegrationError("materialization ancestor chain must not contain a symbolic link")


def _validate_profile(profile: Mapping[str, Any]) -> None:
    _require_mapping_with_exact_keys(profile, PROFILE_FIELDS, "profile")
    schema_version = profile.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 1:
        raise IntegrationError("profile schema_version must be integer 1")
    _require_nonempty_str(profile.get("profile_id"), "profile.profile_id")
    if profile.get("engine_family") != "cocos-creator":
        raise IntegrationError("engine_family must be cocos-creator")
    if profile.get("version_line") != "3.8":
        raise IntegrationError("version_line must be pinned to 3.8")
    source_commit = profile.get("source_commit")
    _require_nonempty_str(profile.get("source_repository"), "profile.source_repository")
    _require_nonempty_str(profile.get("source_license"), "profile.source_license")
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
        _require_mapping_with_exact_keys(item, PLATFORM_FIELDS, "platform")
        _require_nonempty_str(item.get("runtime_api_namespace"), "platform.runtime_api_namespace")
        if item.get("engine_source_state") != "observed_at_pinned_commit":
            raise IntegrationError("platform engine source state must remain pinned")
        if item.get("official_contract_state") != "contract_pending":
            raise IntegrationError("official platform contract must remain pending")
        if item.get("build_state") != "build_pending" or item.get("build_target_id") is not None:
            raise IntegrationError("build target must remain unresolved and pending")

    try:
        canonical_profile = json.loads(CANONICAL_PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrationError(f"canonical Cocos profile is unavailable: {exc}") from exc
    if dict(profile) != canonical_profile:
        raise IntegrationError("profile does not match canonical Cocos integration profile")


def _validate_work_package(work_package: Mapping[str, Any]) -> None:
    if set(work_package) != WORK_PACKAGE_FIELDS:
        raise IntegrationError("work package must use the exact schema v2 field inventory")
    schema_version = work_package.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 2:
        raise IntegrationError("work package schema_version must be integer 2")

    kernel = work_package.get("kernel")
    content = work_package.get("content")
    if not isinstance(kernel, Mapping) or not isinstance(content, Mapping):
        raise IntegrationError("work package kernel and content must be objects")
    _require_mapping_with_exact_keys(kernel, KERNEL_FIELDS, "kernel")
    if work_package.get("kernel_digest") != digest(kernel):
        raise IntegrationError("work package kernel_digest does not match kernel")
    if work_package.get("content_digest") != digest(content):
        raise IntegrationError("work package content_digest does not match content")

    try:
        canonical_architecture = validate_kernel_architecture(kernel)
    except ArchitectureProfileError as exc:
        raise IntegrationError(f"work package architecture_profile is invalid: {exc}") from exc
    if work_package.get("architecture_profile") != canonical_architecture:
        raise IntegrationError(
            "work package architecture_profile does not match canonical kernel binding"
        )

    authority = work_package.get("authority")
    if not isinstance(authority, Mapping) or set(authority) != WORK_PACKAGE_AUTHORITY_FIELDS:
        raise IntegrationError("work package authority must use the exact closed inventory")
    if any(value is not False for value in authority.values()):
        raise IntegrationError("work package authority must remain closed")

    # Hostile type and semantic validation for v2 contract (address REJECT P1)
    _require_nonempty_str(work_package.get("work_package_id"), "work_package_id")
    _require_nonempty_str(work_package.get("model_route"), "model_route")

    gen = work_package.get("generation")
    if not isinstance(gen, Mapping):
        raise IntegrationError("generation must be an object")
    _require_mapping_with_exact_keys(gen, {"task_type", "confidence", "template_version"}, "generation")
    _require_nonempty_str(gen["task_type"], "generation.task_type")
    confidence = gen["confidence"]
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise IntegrationError("generation.confidence must be numeric in [0, 1]")
    _require_nonempty_str(gen["template_version"], "generation.template_version")

    required_gates = _require_list_of_nonempty_str(
        work_package.get("required_gates"), "required_gates"
    )
    if not required_gates:
        raise IntegrationError("required_gates must not be empty")

    acc = work_package.get("accuracy_contract")
    if not isinstance(acc, Mapping):
        raise IntegrationError("accuracy_contract must be an object")
    _require_mapping_with_exact_keys(
        acc,
        {"same_gates_for_all_models", "model_self_report_is_evidence", "candidate_only"},
        "accuracy_contract",
    )
    if acc.get("candidate_only") is not True:
        raise IntegrationError("accuracy_contract.candidate_only must be True")
    if acc.get("model_self_report_is_evidence") is not False:
        raise IntegrationError("accuracy_contract.model_self_report_is_evidence must be False")
    if acc.get("same_gates_for_all_models") is not True:
        raise IntegrationError("accuracy_contract.same_gates_for_all_models must be True")

    # Exactly-one primary architecture: reject secondary or extra primary declarations in kernel
    forbidden_arch_fields = {
        "secondary_architecture_profile",
        "primary_clock_count",
        "secondary_primary_clock",
        "architecture_profiles",
        "secondary_profiles",
    }
    if any(k in kernel for k in forbidden_arch_fields):
        raise IntegrationError("kernel must not declare secondary or additional primary architecture fields")

    try:
        routing = json.loads(CANONICAL_ROUTING_PATH.read_text(encoding="utf-8"))
        expected = compile_work_package(
            {
                "kernel": dict(kernel),
                "content": dict(content),
                "generation": dict(gen),
            },
            routing,
        )
    except (OSError, json.JSONDecodeError, CompileError, KeyError, TypeError, ValueError) as exc:
        raise IntegrationError(f"work package cannot be canonically replayed: {exc}") from exc
    if dict(work_package) != expected:
        raise IntegrationError("work package does not match canonical compiler output")


def _validate_packet(packet: Mapping[str, Any]) -> None:
    _require_mapping_with_exact_keys(packet, PACKET_FIELDS, "integration packet")
    schema_version = packet.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 1:
        raise IntegrationError("integration packet schema_version must be integer 1")
    _require_nonempty_str(packet.get("integration_id"), "integration packet integration_id")
    source_digest = packet.get("source_compile_digest")
    if not isinstance(source_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", source_digest):
        raise IntegrationError("integration packet source_compile_digest must be a sha256 digest")
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
        raise IntegrationError("integration packet engine must be an object")
    _require_mapping_with_exact_keys(engine, ENGINE_FIELDS, "integration packet engine")
    if engine.get("family") != "cocos-creator" or engine.get("version_line") != "3.8":
        raise IntegrationError("integration packet engine must remain cocos-creator 3.8")
    _require_nonempty_str(engine.get("source_repository"), "integration packet engine.source_repository")
    _require_nonempty_str(engine.get("source_license"), "integration packet engine.source_license")
    source_commit = engine.get("source_commit")
    if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise IntegrationError("integration packet engine source_commit must be pinned")
    if engine.get("creator_cli_state") != "unavailable":
        raise IntegrationError("integration packet cannot assert Creator CLI availability")
    platforms = packet.get("platforms")
    if not isinstance(platforms, list) or len(platforms) != 2 or {
        item.get("platform_id") for item in platforms if isinstance(item, Mapping)
    } != EXPECTED_PLATFORMS:
        raise IntegrationError("integration packet platform inventory is invalid")
    for item in platforms:
        if not isinstance(item, Mapping):
            raise IntegrationError("integration packet platform entries must be objects")
        _require_mapping_with_exact_keys(item, PLATFORM_FIELDS, "integration packet platform")
        if (
            item.get("engine_source_state") != "observed_at_pinned_commit"
            or item.get("official_contract_state") != "contract_pending"
            or item.get("build_state") != "build_pending"
            or item.get("build_target_id") is not None
        ):
            raise IntegrationError("integration packet platform state must remain pending")
        _require_nonempty_str(
            item.get("runtime_api_namespace"), "integration packet platform.runtime_api_namespace"
        )
    materialization = packet.get("materialization_contract")
    if not isinstance(materialization, Mapping):
        raise IntegrationError("integration packet materialization_contract must be an object")
    _require_mapping_with_exact_keys(
        materialization, MATERIALIZATION_FIELDS, "integration packet materialization_contract"
    )
    if materialization.get("writes_local_candidate_only") is not True:
        raise IntegrationError("integration packet must remain local-candidate-only")
    if materialization.get("cocos_project_mutation") is not False:
        raise IntegrationError("integration packet cannot authorize Cocos project mutation")
    if materialization.get("generated_files") != GENERATED_FILES:
        raise IntegrationError("integration packet generated file inventory is not canonical")
    if packet.get("required_next_receipts") != REQUIRED_NEXT_RECEIPTS:
        raise IntegrationError("integration packet required receipt inventory is not canonical")


def compile_cocos_integration(
    work_package: Mapping[str, Any], profile: Mapping[str, Any]
) -> Dict[str, Any]:
    _verify_embedded_digest(work_package, "compile_digest")
    _validate_work_package(work_package)
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
            "generated_files": list(GENERATED_FILES),
        },
        "required_next_receipts": list(REQUIRED_NEXT_RECEIPTS),
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
    _validate_work_package(work_package)
    _verify_embedded_digest(packet, "integration_digest")
    _validate_packet(packet)
    try:
        canonical_profile = json.loads(CANONICAL_PROFILE_PATH.read_text(encoding="utf-8"))
        expected_packet = compile_cocos_integration(work_package, canonical_profile)
    except (OSError, json.JSONDecodeError, IntegrationError) as exc:
        raise IntegrationError(f"integration packet cannot be canonically replayed: {exc}") from exc
    if dict(packet) != expected_packet:
        raise IntegrationError("integration packet does not match canonical compiler output")
    if packet.get("source_compile_digest") != work_package.get("compile_digest"):
        raise IntegrationError("integration packet is not bound to the work package")

    root = Path(output_root)
    if root.is_symlink():
        raise IntegrationError("materialization root must not be a symbolic link")
    if root.exists():
        raise IntegrationError("materialization root must not already exist")
    if not root.parent.exists() or not root.parent.is_dir() or root.parent.is_symlink():
        raise IntegrationError("materialization parent must be an existing non-symlink directory")
    _assert_no_untrusted_symlink_ancestor(root.parent)

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
