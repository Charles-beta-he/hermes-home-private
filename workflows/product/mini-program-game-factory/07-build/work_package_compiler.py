#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Set


class CompileError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def route_task(
    routing: Mapping[str, Any],
    *,
    task_type: str,
    touched_fields: Iterable[str],
    confidence: float,
    platform_contract_known: bool,
    prior_gate_failures: int,
) -> str:
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
    _require(seed, ["kernel", "content", "generation"], "seed")
    kernel = seed["kernel"]
    content = seed["content"]
    generation = seed["generation"]
    _require(
        kernel,
        [
            "kernel_id",
            "version",
            "state_fields",
            "actions",
            "win_condition",
            "lose_condition",
            "score_rule",
            "seed_policy",
            "tunable_parameters",
            "golden_cases",
        ],
        "kernel",
    )
    _require(
        content,
        ["content_id", "kernel_id", "theme", "locale", "copy", "level_parameters", "assets"],
        "content",
    )
    _require(generation, ["task_type", "confidence", "template_version"], "generation")
    if not kernel["golden_cases"]:
        raise CompileError("kernel requires golden cases")

    _validate_content(kernel, content, routing)
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
        "schema_version": 1,
        "work_package_id": f"{kernel['kernel_id']}@{kernel['version']}::{content['content_id']}",
        "closure_state": "work_package_compiled",
        "model_route": route,
        "kernel_digest": kernel_digest,
        "content_digest": content_digest,
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
            "candidate_only": route == "low_cost",
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
