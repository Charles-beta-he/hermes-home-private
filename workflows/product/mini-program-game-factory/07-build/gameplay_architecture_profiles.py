#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Mapping


class ArchitectureProfileError(ValueError):
    pass


CANONICAL_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "gameplay-architecture-profiles.json"
EXPECTED_PROFILE_IDS = {
    "grid-turn",
    "board-resolver",
    "wave-path",
    "real-time-physics",
    "card-event-stack",
    "economy-time-simulation",
    "authoritative-replication",
}
REGISTRY_FIELDS = {
    "schema_version",
    "registry_id",
    "shared_shell",
    "presentation_only_fields",
    "dimensions",
    "profiles",
}
SHARED_SHELL_FIELDS = {"capabilities", "must_not_own"}
DIMENSION_FIELDS = {
    "time_model",
    "space_model",
    "state_model",
    "resolution_model",
    "authority_model",
}
PROFILE_FIELDS = {"profile_id", "profile_version", "topology", "verification_gates"}
BINDING_FIELDS = {"profile_id", "profile_version", "topology", "auxiliary_systems"}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require_exact_fields(value: Mapping[str, Any], expected: set, label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ArchitectureProfileError(
            f"{label} exact fields required; missing={missing}; extra={extra}"
        )


def _require_unique_text_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise ArchitectureProfileError(f"{label} must be a non-empty list")
    if any(not isinstance(item, str) or not item for item in value):
        raise ArchitectureProfileError(f"{label} entries must be non-empty strings")
    if len(set(value)) != len(value):
        raise ArchitectureProfileError(f"{label} contains duplicate entries")


def validate_registry(registry: Mapping[str, Any]) -> None:
    if not isinstance(registry, Mapping):
        raise ArchitectureProfileError("registry must be an object")
    _require_exact_fields(registry, REGISTRY_FIELDS, "registry")
    schema_version = registry["schema_version"]
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 1:
        raise ArchitectureProfileError("registry schema_version must be integer 1")
    if registry["registry_id"] != "mini-game-gameplay-architecture-profiles":
        raise ArchitectureProfileError("registry_id is not canonical")

    shared_shell = registry["shared_shell"]
    if not isinstance(shared_shell, Mapping):
        raise ArchitectureProfileError("shared_shell must be an object")
    _require_exact_fields(shared_shell, SHARED_SHELL_FIELDS, "shared_shell")
    _require_unique_text_list(shared_shell["capabilities"], "shared_shell capabilities")
    _require_unique_text_list(shared_shell["must_not_own"], "shared_shell must_not_own")
    if "primary_simulation_clock" not in shared_shell["must_not_own"]:
        raise ArchitectureProfileError("shared shell must not own the primary simulation clock")

    _require_unique_text_list(registry["presentation_only_fields"], "presentation_only_fields")
    if "visual_style" not in registry["presentation_only_fields"]:
        raise ArchitectureProfileError("visual_style must remain presentation-only")

    dimensions = registry["dimensions"]
    if not isinstance(dimensions, Mapping):
        raise ArchitectureProfileError("dimensions must be an object")
    _require_exact_fields(dimensions, DIMENSION_FIELDS, "dimensions")
    for name, values in dimensions.items():
        _require_unique_text_list(values, f"dimension {name}")

    profiles = registry["profiles"]
    if not isinstance(profiles, list):
        raise ArchitectureProfileError("profiles must be a list")
    seen = set()
    for profile in profiles:
        if not isinstance(profile, Mapping):
            raise ArchitectureProfileError("profile entries must be objects")
        _require_exact_fields(profile, PROFILE_FIELDS, "profile")
        profile_id = profile["profile_id"]
        if not isinstance(profile_id, str) or not profile_id:
            raise ArchitectureProfileError("profile_id must be a non-empty string")
        if profile_id in seen:
            raise ArchitectureProfileError("profile_id entries must be unique")
        seen.add(profile_id)
        version = profile["profile_version"]
        if not isinstance(version, int) or isinstance(version, bool) or version != 1:
            raise ArchitectureProfileError("profile_version must be integer 1")
        topology = profile["topology"]
        if not isinstance(topology, Mapping):
            raise ArchitectureProfileError("profile topology must be an object")
        _require_exact_fields(topology, DIMENSION_FIELDS, "profile topology")
        for dimension, selected in topology.items():
            if selected not in dimensions[dimension]:
                raise ArchitectureProfileError(
                    f"profile {profile_id} has unknown {dimension}: {selected}"
                )
        _require_unique_text_list(
            profile["verification_gates"], f"profile {profile_id} verification_gates"
        )
    if seen != EXPECTED_PROFILE_IDS:
        raise ArchitectureProfileError(
            "profile inventory must be exactly canonical; "
            f"missing={sorted(EXPECTED_PROFILE_IDS - seen)}; "
            f"extra={sorted(seen - EXPECTED_PROFILE_IDS)}"
        )


def load_canonical_registry() -> Dict[str, Any]:
    try:
        value = json.loads(CANONICAL_REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArchitectureProfileError(f"canonical architecture registry unavailable: {exc}") from exc
    validate_registry(value)
    return value


def validate_kernel_architecture(kernel: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(kernel, Mapping):
        raise ArchitectureProfileError("kernel must be an object")
    binding = kernel.get("architecture_profile")
    if not isinstance(binding, Mapping):
        raise ArchitectureProfileError("kernel architecture_profile must be an object")
    _require_exact_fields(binding, BINDING_FIELDS, "architecture profile binding")

    # Exactly-one primary architecture enforcement (address P1 false-accept of secondary declarations)
    forbidden_arch_fields = {
        "secondary_architecture_profile",
        "primary_clock_count",
        "secondary_primary_clock",
        "architecture_profiles",
        "secondary_profiles",
    }
    for bad in forbidden_arch_fields:
        if bad in kernel:
            raise ArchitectureProfileError(
                f"kernel must not declare secondary or additional primary architecture fields: {bad}"
            )

    registry = load_canonical_registry()
    profiles = {profile["profile_id"]: profile for profile in registry["profiles"]}
    profile_id = binding["profile_id"]
    if not isinstance(profile_id, str) or not profile_id:
        raise ArchitectureProfileError("architecture profile_id must be a non-empty string")
    if profile_id not in profiles:
        raise ArchitectureProfileError(f"unknown primary profile: {profile_id}")
    profile = profiles[profile_id]

    version = binding["profile_version"]
    if not isinstance(version, int) or isinstance(version, bool):
        raise ArchitectureProfileError("architecture profile version must be an integer")
    if version != profile["profile_version"]:
        raise ArchitectureProfileError("architecture profile version does not match canonical profile")

    topology = binding["topology"]
    if not isinstance(topology, Mapping):
        raise ArchitectureProfileError("architecture profile topology must be an object")
    _require_exact_fields(topology, DIMENSION_FIELDS, "architecture profile topology")
    if dict(topology) != profile["topology"]:
        raise ArchitectureProfileError("architecture profile topology does not match canonical profile")

    auxiliary = binding["auxiliary_systems"]
    if not isinstance(auxiliary, list):
        raise ArchitectureProfileError("auxiliary_systems must be a list")
    if any(not isinstance(item, str) or not item for item in auxiliary):
        raise ArchitectureProfileError("auxiliary_systems entries must be non-empty strings")
    if len(set(auxiliary)) != len(auxiliary):
        raise ArchitectureProfileError("auxiliary_systems contains duplicate entries")
    if profile_id in auxiliary:
        raise ArchitectureProfileError("auxiliary_systems cannot repeat the primary profile")
    unknown_auxiliary = sorted(set(auxiliary) - set(profiles))
    if unknown_auxiliary:
        raise ArchitectureProfileError(
            f"unknown auxiliary profile: {', '.join(unknown_auxiliary)}"
        )

    return {
        "registry_id": registry["registry_id"],
        "registry_schema_version": registry["schema_version"],
        "registry_digest": digest(registry),
        "primary_profile_id": profile_id,
        "profile_version": profile["profile_version"],
        "profile_digest": digest(profile),
        "topology": dict(profile["topology"]),
        "verification_gates": list(profile["verification_gates"]),
        "auxiliary_systems": list(auxiliary),
        "primary_clock_count": 1,
    }
