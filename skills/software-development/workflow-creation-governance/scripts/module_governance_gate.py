#!/usr/bin/env python3
"""Deterministic static gate for Hermes reusable runtime modules."""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

SCHEMA = "hermes_module_governance_v1"
REQUIRED_SECTIONS = (
    "module",
    "artifacts",
    "credentials",
    "runtime",
    "verification",
    "lifecycle",
    "git",
)
EXACT_VERSION = re.compile(r"^v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
FORBIDDEN_SECRET_KEYS = {
    "token",
    "password",
    "api_key",
    "apikey",
    "secret",
    "secret_value",
    "credential_value",
    "private_key",
}


def _gate(name: str, ok: bool, findings: List[str]) -> Dict[str, Any]:
    return {"name": name, "ok": ok, "findings": findings}


def _find_secret_fields(value: Any, prefix: str = "") -> List[str]:
    findings: List[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if str(key).lower() in FORBIDDEN_SECRET_KEYS and child not in (None, "", "[REDACTED]"):
                findings.append(f"plaintext secret field forbidden: {path}")
            findings.extend(_find_secret_fields(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_secret_fields(child, f"{prefix}[{index}]"))
    return findings


def _required_fields(section: Dict[str, Any], names: Tuple[str, ...]) -> List[str]:
    return [f"missing field: {name}" for name in names if not section.get(name)]


def _validate_skill(path: Path) -> List[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read Skill: {exc}"]
    if not content.startswith("---\n"):
        return ["Skill frontmatter must start at byte zero"]
    closing = content.find("\n---\n", 4)
    if closing < 0:
        return ["Skill frontmatter closing delimiter is missing"]
    frontmatter = content[4:closing]
    body = content[closing + 5 :].strip()
    findings = []
    if not re.search(r"(?m)^name:\s*\S+", frontmatter):
        findings.append("Skill frontmatter name is missing")
    if not re.search(r"(?m)^description:\s*\S+", frontmatter):
        findings.append("Skill frontmatter description is missing")
    if not body:
        findings.append("Skill body is empty")
    return findings


def _validate_route_evals(path: Path) -> List[str]:
    minimums = {"positive": 3, "neighbor": 2, "forbidden": 2, "no-load": 1}
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        return [f"cannot read route evals: {exc}"]
    counts: Dict[str, int] = {}
    for row in rows:
        bucket = (row.get("bucket") or "").strip()
        counts[bucket] = counts.get(bucket, 0) + 1
    return [
        f"route eval bucket {bucket} requires {minimum}, found {counts.get(bucket, 0)}"
        for bucket, minimum in minimums.items()
        if counts.get(bucket, 0) < minimum
    ]


def validate_manifest(manifest_path: Path, root: Path) -> Dict[str, Any]:
    manifest_path = Path(manifest_path)
    root = Path(root)
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "schema": SCHEMA,
            "manifest": str(manifest_path),
            "gates": [_gate("manifest", False, [str(exc)])],
            "failed_gates": ["manifest"],
        }

    gates: List[Dict[str, Any]] = []
    schema_findings = [] if data.get("schema") == SCHEMA else [f"schema must equal {SCHEMA}"]
    missing_sections = [name for name in REQUIRED_SECTIONS if not isinstance(data.get(name), dict)]
    schema_findings.extend(f"missing section: {name}" for name in missing_sections)
    gates.append(_gate("manifest", not schema_findings, schema_findings))

    for name in REQUIRED_SECTIONS:
        if name in missing_sections:
            gates.append(_gate(name, False, [f"section {name} is required"]))
            continue
        section = data[name]
        findings: List[str] = []
        if name == "module":
            findings.extend(_required_fields(section, ("id", "kind", "scope", "maturity", "version")))
            if section.get("maturity") not in {"draft", "candidate", "validated", "common", "canonical", "deprecated", "archived", "quarantine", "revoked"}:
                findings.append("module.maturity is invalid")
        elif name == "artifacts":
            findings.extend(_required_fields(section, ("skill", "adapter", "runtime_manifest", "route_evals")))
            tests = section.get("tests")
            if not isinstance(tests, list) or not tests:
                findings.append("artifacts.tests must be a non-empty list")
            path_values = [section.get("skill"), section.get("adapter"), section.get("runtime_manifest"), section.get("route_evals")]
            path_values.extend(tests if isinstance(tests, list) else [])
            for relative in path_values:
                if relative and not (root / relative).is_file():
                    findings.append(f"artifact missing: {relative}")
            skill_relative = section.get("skill")
            if skill_relative and (root / skill_relative).is_file():
                findings.extend(_validate_skill(root / skill_relative))
            evals_relative = section.get("route_evals")
            if evals_relative and (root / evals_relative).is_file():
                findings.extend(_validate_route_evals(root / evals_relative))
        elif name == "credentials":
            findings.extend(_required_fields(section, ("mode",)))
            if section.get("plaintext_forbidden") is not True:
                findings.append("credentials.plaintext_forbidden must be true")
            findings.extend(_find_secret_fields(section, "credentials"))
        elif name == "runtime":
            pins = section.get("pinned_dependencies")
            if not isinstance(pins, dict) or not pins:
                findings.append("runtime.pinned_dependencies must be a non-empty object")
            else:
                for package, version in pins.items():
                    if not isinstance(version, str) or not EXACT_VERSION.fullmatch(version):
                        findings.append(f"dependency must use an exact version: {package}={version}")
            if not isinstance(section.get("daemon"), bool):
                findings.append("runtime.daemon must be boolean")
            if not isinstance(section.get("side_effects"), list):
                findings.append("runtime.side_effects must be a list")
        elif name == "verification":
            commands = section.get("commands")
            if not isinstance(commands, list) or not commands:
                findings.append("verification.commands must be a non-empty list")
            if section.get("fresh_smoke_required") is not True:
                findings.append("verification.fresh_smoke_required must be true")
            if section.get("secret_scan_required") is not True:
                findings.append("verification.secret_scan_required must be true")
        elif name == "lifecycle":
            findings.extend(_required_fields(section, ("owner", "rollback", "upgrade", "deprecate")))
        elif name == "git":
            if section.get("scoped_commit_required") is not True:
                findings.append("git.scoped_commit_required must be true")
            if section.get("push_requires_separate_authority") is not True:
                findings.append("git.push_requires_separate_authority must be true")
            excluded = section.get("exclude")
            if not isinstance(excluded, list) or not excluded:
                findings.append("git.exclude must be a non-empty list")
        gates.append(_gate(name, not findings, findings))

    failed = [gate["name"] for gate in gates if not gate["ok"]]
    return {
        "ok": not failed,
        "schema": SCHEMA,
        "manifest": str(manifest_path),
        "root": str(root),
        "gates": gates,
        "failed_gates": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path.home() / ".hermes")
    args = parser.parse_args()
    result = validate_manifest(args.manifest, args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
