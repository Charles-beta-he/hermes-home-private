#!/usr/bin/env python3
"""Build DataVaultItem projection for Personal AI OS packet/profile files.

Read-only classification over project artifacts. It does not read secrets, export
raw private data, or mutate memory.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()
PACKET = HOME / ".hermes" / "workflows" / "projects" / "hermes-agent-os-control-plane" / "12-personal-ai-os"
PROFILE = HOME / ".hermes" / "project-profiles" / "hermes-agent-os-control-plane.json"
OUT = PACKET / "12-data-vault-projection.json"


def sensitivity_for(path: Path) -> tuple[str, str, str]:
    name = path.name.lower()
    text = str(path).lower()
    if any(k in name for k in ["credential", "secret", "password", "token", "key"]):
        return "D5", "forbidden", "never"
    if any(k in name for k in ["authority", "ledger", "boundary"]):
        return "D2", "local_execution", "summary"
    if any(k in name for k in ["profile"]):
        return "D2", "reasoning", "redacted"
    if any(k in name for k in ["progress", "backlog", "roadmap"]):
        return "D2", "reasoning", "summary"
    if path.suffix == ".py":
        return "D1", "local_execution", "summary"
    if path.suffix == ".json" or path.suffix == ".jsonl":
        return "D2", "reasoning", "summary"
    if "personal-ai-os" in text:
        return "D1", "reasoning", "summary"
    return "D1", "reasoning", "summary"


def item_for(path: Path, category: str) -> dict:
    sensitivity, allowed_use, allowed_export = sensitivity_for(path)
    return {
        "schema": "DataVaultItem.v0",
        "id": "data." + str(path.relative_to(HOME / ".hermes")).replace("/", "."),
        "category": category,
        "sensitivity": sensitivity,
        "source": "local_project_artifact",
        "source_path": str(path),
        "owner": "user_project",
        "allowed_use": allowed_use,
        "allowed_export": allowed_export,
        "retention": "project",
        "last_verified": datetime.now(timezone.utc).isoformat(),
        "raw_secret_exported": False,
        "global_memory_target": False,
    }


def main() -> int:
    paths = [PROFILE] if PROFILE.exists() else []
    paths.extend(sorted(p for p in PACKET.iterdir() if p.is_file() and p.name != OUT.name))
    items = []
    for path in paths:
        category = "project_profile" if path == PROFILE else "project_ssot_artifact"
        items.append(item_for(path, category))
    findings = []
    for item in items:
        if item["sensitivity"] in {"D5", "D6"} and item["allowed_export"] != "never":
            findings.append({"severity": "fail", "code": "sensitive_export_not_never", "id": item["id"]})
        if item["global_memory_target"]:
            findings.append({"severity": "fail", "code": "wip_project_artifact_targets_global_memory", "id": item["id"]})
    payload = {
        "ok": not any(f["severity"] == "fail" for f in findings),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "data_vault_projection_v0",
        "item_count": len(items),
        "sensitivity_counts": {s: sum(1 for i in items if i["sensitivity"] == s) for s in sorted({i["sensitivity"] for i in items})},
        "raw_secret_exported": False,
        "global_memory_wip_write": False,
        "runtime_mutation": False,
        "external_side_effects_executed": False,
        "findings": findings,
        "items": items,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ["ok", "mode", "item_count", "sensitivity_counts", "raw_secret_exported", "global_memory_wip_write", "findings"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
