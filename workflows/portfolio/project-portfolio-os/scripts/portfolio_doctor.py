#!/usr/bin/env python3
"""Portfolio OS doctor.

Local-only verifier for Hermes project portfolio registry/profile/ledger alignment.
It performs no network calls and has no side effects unless the caller redirects output.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERMES_HOME = ROOT.parents[2]
REGISTRY = ROOT / "01-registry" / "portfolio-registry.json"
PROFILE_DIR = HERMES_HOME / "project-profiles"


def load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # pragma: no cover - surfaced in report
        return None, f"{type(exc).__name__}: {exc}"


def project_id_from_profile(path: Path, payload: dict[str, Any]) -> str:
    return str(
        payload.get("id")
        or payload.get("project")
        or payload.get("project_id")
        or path.stem
    )


def as_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser()


def add(findings: list[dict[str, Any]], severity: str, project: str, check: str, message: str, path: str | None = None) -> None:
    item = {"severity": severity, "project": project, "check": check, "message": message}
    if path:
        item["path"] = path
    findings.append(item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    findings: list[dict[str, Any]] = []
    registry, err = load_json(REGISTRY)
    if err or not isinstance(registry, dict):
        add(findings, "error", "portfolio", "registry_json", err or "registry is not an object", str(REGISTRY))
        payload = {
            "ok": False,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "registry": str(REGISTRY),
            "counts": {"error": 1, "warning": 0},
            "findings": findings,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    projects = registry.get("projects")
    if not isinstance(projects, list):
        add(findings, "error", "portfolio", "registry_projects", "registry.projects must be a list", str(REGISTRY))
        projects = []

    registry_ids: set[str] = set()
    profile_ids: set[str] = set()
    profile_paths = sorted(PROFILE_DIR.glob("*.json"))
    profiles: dict[str, tuple[Path, dict[str, Any]]] = {}
    duplicate_profiles: dict[str, list[str]] = {}
    for path in profile_paths:
        data, perr = load_json(path)
        if perr or not isinstance(data, dict):
            add(findings, "error", path.stem, "profile_json", perr or "profile is not an object", str(path))
            continue
        pid = project_id_from_profile(path, data)
        if pid in profiles:
            duplicate_profiles.setdefault(pid, [str(profiles[pid][0])]).append(str(path))
        profiles[pid] = (path, data)
        profile_ids.add(pid)
    for pid, paths in duplicate_profiles.items():
        add(findings, "error", pid, "duplicate_profile_id", "duplicate project profile ids: " + ", ".join(paths))

    for entry in projects:
        if not isinstance(entry, dict):
            add(findings, "error", "portfolio", "project_entry_shape", "registry project entry must be an object")
            continue
        pid = str(entry.get("id") or entry.get("project_id") or "").strip()
        if not pid:
            add(findings, "error", "portfolio", "project_id", "registry project missing id")
            continue
        if pid in registry_ids:
            add(findings, "error", pid, "duplicate_registry_id", "duplicate project id in registry")
        registry_ids.add(pid)

        profile_path = as_path(entry.get("profile")) or (PROFILE_DIR / f"{pid}.json")
        if not profile_path.exists():
            add(findings, "error", pid, "profile_exists", "profile path missing", str(profile_path))
            continue
        profile, perr = load_json(profile_path)
        if perr or not isinstance(profile, dict):
            add(findings, "error", pid, "profile_json", perr or "profile is not an object", str(profile_path))
            continue
        actual_pid = project_id_from_profile(profile_path, profile)
        if actual_pid != pid:
            add(findings, "error", pid, "profile_id_match", f"profile id {actual_pid!r} does not match registry id {pid!r}", str(profile_path))

        ledger = as_path(profile.get("progress_ledger")) or as_path(entry.get("progress_ledger"))
        if not ledger:
            add(findings, "error", pid, "progress_ledger_declared", "missing progress_ledger in profile/registry", str(profile_path))
        elif not ledger.exists():
            add(findings, "error", pid, "progress_ledger_exists", "progress ledger path missing", str(ledger))

        ssot_root = as_path(profile.get("ssot_root")) or as_path(entry.get("ssot_root"))
        if not ssot_root:
            add(findings, "warning", pid, "ssot_root_declared", "missing ssot_root; status may be metadata-only", str(profile_path))
        elif not ssot_root.exists():
            add(findings, "error", pid, "ssot_root_exists", "ssot_root path missing", str(ssot_root))

        status = str(entry.get("status") or profile.get("status") or "")
        if "contract-ready" in status and (not ssot_root or not ssot_root.exists()):
            add(findings, "error", pid, "status_evidence", "contract-ready status without existing ssot_root", str(profile_path))

    registry_only = sorted(registry_ids - profile_ids)
    profile_only = sorted(profile_ids - registry_ids)
    for pid in registry_only:
        add(findings, "error", pid, "registry_profile_set", "project appears in registry but no matching profile id was loaded")
    for pid in profile_only:
        add(findings, "warning", pid, "profile_registry_set", "profile exists but project is absent from registry")

    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    payload = {
        "schema": "portfolio_doctor_v1",
        "ok": errors == 0,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(REGISTRY),
        "profile_dir": str(PROFILE_DIR),
        "project_count": len(projects),
        "profile_count": len(profile_ids),
        "registry_only": registry_only,
        "profile_only": profile_only,
        "counts": {"error": errors, "warning": warnings},
        "findings": findings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
