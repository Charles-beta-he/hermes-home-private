#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Set

from gameplay_architecture_profiles import (
    ArchitectureProfileError,
    validate_kernel_architecture,
)


class CompileError(ValueError):
    pass


CANONICAL_ROUTING_PATH = Path(__file__).resolve().parents[1] / "model-routing.json"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def require_canonical_routing(routing: Mapping[str, Any]) -> None:
    try:
        canonical = json.loads(CANONICAL_ROUTING_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompileError(f"canonical routing is unavailable: {exc}") from exc
    if digest(routing) != digest(canonical):
        raise CompileError("routing does not match canonical routing")


def route_task(
    routing: Mapping[str, Any],
    *,
    task_type: str,
    touched_fields: Iterable[str],
    confidence: float,
    platform_contract_known: bool,
    prior_gate_failures: int,
) -> str:
    require_canonical_routing(routing)
    protected: Set[str] = set(routing["protected_surfaces"])
    touched = set(touched_fields)
    escalation = routing["escalation_rules"]

    if not platform_contract_known:
        return "blocked"
    if touched & protected:
        return "high_reasoning"
    if prior_gate_failures >= int(escalation["repeated_gate_failure_count"]):
        return escalation["repeated_gate_failure_route"]
    if confidence < float(escalation["confidence_below"]):
        return "high_reasoning"

    for route_name in ("low_cost", "standard", "high_reasoning"):
        if task_type in routing["routes"][route_name]["allowed_tasks"]:
            return route_name
    return routing.get("default_route", "blocked")


def _require(mapping: Mapping[str, Any], fields: Iterable[str], section: str) -> None:
    missing = [field for field in fields if field not in mapping]
    if missing:
        raise CompileError(f"{section} missing required fields: {', '.join(missing)}")


def _require_exact(mapping: Mapping[str, Any], fields: Iterable[str], section: str) -> None:
    expected = set(fields)
    if set(mapping) != expected:
        raise CompileError(f"{section} must use the exact field inventory {sorted(expected)}")


def _require_approved(
    mapping: Mapping[str, Any], required: Iterable[str], optional: Iterable[str], section: str
) -> None:
    required_fields = set(required)
    approved_fields = required_fields | set(optional)
    if not required_fields.issubset(mapping) or not set(mapping).issubset(approved_fields):
        raise CompileError(f"{section} must use the exact field inventory from {sorted(approved_fields)}")


def _require_nonempty_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise CompileError(f"{name} must be a nonempty string")
    return value


def _require_unique_nonempty_strings(value: Any, name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise CompileError(f"{name} must be a nonempty list")
    if any(not isinstance(item, str) or not item for item in value):
        raise CompileError(f"{name} must contain only nonempty strings")
    if len(value) != len(set(value)):
        raise CompileError(f"{name} must not contain duplicates")
    return value


def _validate_kernel_values(kernel: Mapping[str, Any]) -> None:
    for field in ["kernel_id", "version", "win_condition", "lose_condition", "score_rule", "seed_policy"]:
        _require_nonempty_str(kernel[field], f"kernel.{field}")
    for field in ["state_fields", "actions", "golden_cases"]:
        _require_unique_nonempty_strings(kernel[field], f"kernel.{field}")
    tunables = kernel["tunable_parameters"]
    if not isinstance(tunables, Mapping) or not tunables:
        raise CompileError("kernel.tunable_parameters must be a nonempty object")
    for name, bounds in tunables.items():
        _require_nonempty_str(name, "kernel.tunable_parameters key")
        if not isinstance(bounds, Mapping) or set(bounds) != {"min", "max"}:
            raise CompileError(f"kernel tunable {name} must contain exactly min and max")
        low, high = bounds["min"], bounds["max"]
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in [low, high]
        ):
            raise CompileError(f"kernel tunable {name} bounds must be finite numbers")
        if low > high:
            raise CompileError(f"kernel tunable {name} min must not exceed max")


def _validate_content_values(kernel: Mapping[str, Any], content: Mapping[str, Any]) -> None:
    for field in ["content_id", "kernel_id", "theme", "locale"]:
        _require_nonempty_str(content[field], f"content.{field}")
    if "visual_style" in content:
        _require_nonempty_str(content["visual_style"], "content.visual_style")
    copy_fields = content["copy"]
    if not isinstance(copy_fields, Mapping) or not copy_fields:
        raise CompileError("content.copy must be a nonempty object")
    for key, value in copy_fields.items():
        _require_nonempty_str(key, "content.copy key")
        _require_nonempty_str(value, f"content.copy.{key}")
    parameters = content["level_parameters"]
    tunables = kernel["tunable_parameters"]
    if not isinstance(parameters, Mapping) or set(parameters) != set(tunables):
        raise CompileError("content.level_parameters must exactly match kernel tunable parameters")
    for name, value in parameters.items():
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
        ):
            raise CompileError(f"content level parameter {name} must be a finite number")
    assets = content["assets"]
    if not isinstance(assets, list):
        raise CompileError("content.assets must be a list")
    for index, asset in enumerate(assets):
        if not isinstance(asset, Mapping) or set(asset) != {"ref", "license"}:
            raise CompileError(f"content.assets[{index}] must contain exactly ref and license")
        _require_nonempty_str(asset["ref"], f"content.assets[{index}].ref")
        _require_nonempty_str(asset["license"], f"content.assets[{index}].license")


def _validate_content(kernel: Mapping[str, Any], content: Mapping[str, Any], routing: Mapping[str, Any]) -> None:
    protected = set(routing["protected_surfaces"])
    illegal = sorted(protected & set(content))
    if illegal:
        raise CompileError(f"content attempts to override protected surface: {', '.join(illegal)}")
    if content["kernel_id"] != kernel["kernel_id"]:
        raise CompileError("content kernel_id does not match kernel")

    bounds = kernel["tunable_parameters"]
    parameters = content["level_parameters"]
    unknown = sorted(set(parameters) - set(bounds))
    if unknown:
        raise CompileError(f"content contains non-tunable parameters: {', '.join(unknown)}")
    missing = sorted(set(bounds) - set(parameters))
    if missing:
        raise CompileError(f"content missing tunable parameters: {', '.join(missing)}")
    for name, value in parameters.items():
        rule = bounds[name]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise CompileError(f"parameter {name} must be numeric")
        if value < rule["min"] or value > rule["max"]:
            raise CompileError(f"parameter {name} out of bounds: {value}")

    assets = content.get("assets", [])
    if not assets:
        raise CompileError("content must declare at least one asset with rights metadata")
    for asset in assets:
        if not asset.get("ref") or not asset.get("license"):
            raise CompileError("asset rights metadata is incomplete")


def compile_work_package(seed: Mapping[str, Any], routing: Mapping[str, Any]) -> Dict[str, Any]:
    _require_exact(seed, ["kernel", "content", "generation"], "seed")
    kernel = seed["kernel"]
    content = seed["content"]
    generation = seed["generation"]
    if not isinstance(kernel, Mapping) or not isinstance(content, Mapping) or not isinstance(generation, Mapping):
        raise CompileError("seed kernel, content, and generation must be objects")
    kernel_fields = [
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
    ]
    _require(kernel, kernel_fields, "kernel")
    # Exactly-one primary (defense in depth; validator will also enforce)
    forbidden_arch_fields = {
        "secondary_architecture_profile",
        "primary_clock_count",
        "secondary_primary_clock",
        "architecture_profiles",
        "secondary_profiles",
    }
    for bad in forbidden_arch_fields:
        if bad in kernel:
            raise CompileError(f"kernel must not declare secondary or additional primary architecture fields: {bad}")
    _require_exact(kernel, kernel_fields, "kernel")
    content_fields = [
        "content_id",
        "kernel_id",
        "theme",
        "locale",
        "copy",
        "level_parameters",
        "assets",
    ]
    _require(content, content_fields, "content")
    generation_fields = ["task_type", "confidence", "template_version"]
    _require_exact(generation, generation_fields, "generation")
    _require_nonempty_str(generation["task_type"], "generation.task_type")
    _require_nonempty_str(generation["template_version"], "generation.template_version")
    _validate_kernel_values(kernel)
    _validate_content_values(kernel, content)
    confidence = generation["confidence"]
    if (
        not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise CompileError("generation.confidence must be numeric in [0, 1]")
    if not kernel["golden_cases"]:
        raise CompileError("kernel requires golden cases")

    try:
        architecture_profile = validate_kernel_architecture(kernel)
    except ArchitectureProfileError as exc:
        raise CompileError(f"architecture_profile is invalid: {exc}") from exc

    _validate_content(kernel, content, routing)
    _require_approved(content, content_fields, ["visual_style"], "content")
    route = route_task(
        routing,
        task_type=generation["task_type"],
        touched_fields=set(content) - {"content_id", "kernel_id", "locale", "assets", "level_parameters"} | set(content["level_parameters"]),
        confidence=float(generation["confidence"]),
        platform_contract_known=bool(generation.get("platform_contract_known", True)),
        prior_gate_failures=int(generation.get("prior_gate_failures", 0)),
    )
    if route == "blocked":
        raise CompileError("model route is blocked")

    kernel_digest = digest(kernel)
    content_digest = digest(content)
    package: Dict[str, Any] = {
        "schema_version": 2,
        "work_package_id": f"{kernel['kernel_id']}@{kernel['version']}::{content['content_id']}",
        "closure_state": "work_package_compiled",
        "model_route": route,
        "kernel_digest": kernel_digest,
        "content_digest": content_digest,
        "architecture_profile": architecture_profile,
        "kernel": kernel,
        "content": content,
        "generation": {
            "task_type": generation["task_type"],
            "confidence": generation["confidence"],
            "template_version": generation["template_version"],
        },
        "required_gates": routing["routes"][route]["required_gates"],
        "authority": {
            "may_publish": False,
            "may_submit_platform": False,
            "may_enter_credentials": False,
            "may_pay": False,
        },
        "accuracy_contract": {
            "same_gates_for_all_models": routing["accuracy_policy"]["same_gates_for_all_models"],
            "model_self_report_is_evidence": routing["accuracy_policy"]["model_self_report_is_evidence"],
            "candidate_only": True,
        },
    }
    package["compile_digest"] = digest(package)
    return package


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a deterministic mini-game work package")
    parser.add_argument("--seed", required=True)
    parser.add_argument("--routing", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        seed = json.loads(Path(args.seed).read_text(encoding="utf-8"))
        routing = json.loads(Path(args.routing).read_text(encoding="utf-8"))
        package = compile_work_package(seed, routing)
    except (OSError, json.JSONDecodeError, CompileError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    rendered = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
