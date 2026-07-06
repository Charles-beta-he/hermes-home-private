#!/usr/bin/env python3
"""Build local AuthorityRecord projection for Personal AI OS work.

Projection only. It reads local artifacts and git commits, then writes a JSONL
ledger under the packet. It does not execute external actions.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()
ROOT = HOME / ".hermes" / "workflows" / "projects" / "hermes-agent-os-control-plane"
PACKET = ROOT / "12-personal-ai-os"
OUT = PACKET / "11-authority-ledger-projection.jsonl"
REPORT = PACKET / "11-authority-ledger-report.json"


def git(cmd: list[str]) -> str:
    return subprocess.check_output(["git", "-C", str(HOME / ".hermes"), *cmd], text=True).strip()


def record(**kwargs) -> dict:
    base = {
        "schema": "AuthorityRecord.v0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "risk_level": "S2/T1",
        "authorization_source": "user_broad_local_autonomous_progress_authority",
        "status": "verified",
        "external_side_effects_executed": False,
        "payment_or_credential_action_executed": False,
        "agent_typed_secret": False,
    }
    base.update(kwargs)
    return base


def main() -> int:
    commit = git(["log", "--oneline", "-1"])
    files = git(["show", "--name-only", "--format=", "HEAD"]).splitlines()
    records = [
        record(
            id="authority.paios.p0_packet",
            action="initialize_personal_ai_os_ssot_packet",
            target=str(PACKET),
            scope="local SSOT/schema/backlog/governance/profile artifacts only",
            input_digest="user accepted Web4.0 Agent OS direction and full local autonomous advancement",
            output_digest="13-file packet committed in ecd24871",
            evidence_refs=[str(PACKET / "09-doctor-report.json"), "git:ecd24871"],
            rollback_refs=["git revert ecd24871"],
        ),
        record(
            id="authority.paios.p1_control_surface",
            action="add_read_only_personal_ai_os_control_surface",
            target=str(PACKET / "personal_ai_os_control.py"),
            scope="read-only status/doctor/schema/backlog/capabilities; no runtime mutation",
            output_digest="local control commands returned ok true",
            evidence_refs=["command:PAIOS_CONTROL_PASS", str(PACKET / "09-doctor-report.json")],
            rollback_refs=["git revert 4a879b75 or remove script from packet"],
        ),
        record(
            id="authority.paios.p2_capability_projection",
            action="build_read_only_capability_graph_projection",
            target=str(PACKET / "10-capability-projection.json"),
            scope="project local tools/skills/profile to CapabilityNode records without execution",
            output_digest="299 nodes; would_execute=false; external_side_effects_executed=false",
            evidence_refs=[str(PACKET / "10-capability-projection.json"), "command:PAIOS_P2_PASS", "git:4a879b75"],
            rollback_refs=["git revert 4a879b75 or delete projection artifact"],
        ),
        record(
            id="authority.paios.precommit_classifier_repair",
            action="repair_local_brain_precommit_ui_visual_false_positive",
            target=str(HOME / ".hermes" / "scripts" / "local_brain_change_preflight.py"),
            scope="local precommit classifier only; prevent bare 'ui' substring from requiring screenshot/browser_console for non-UI code",
            output_digest="8 local-brain preflight tests passed",
            evidence_refs=["command:python3 -m pytest scripts/test_local_brain_change_preflight.py -q -> 8 passed", "git:4a879b75"],
            rollback_refs=["git revert 4a879b75"],
        ),
        record(
            id="authority.paios.current_commit_readback",
            action="read_back_current_scoped_commit",
            target="git:/Users/charles/.hermes",
            scope="read-only git log/show over current commit",
            risk_level="S1/T0",
            output_digest=commit,
            evidence_refs=["git show --name-only HEAD", *files[:20]],
            rollback_refs=["not_applicable_read_only"],
        ),
    ]
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records))
    report = {
        "ok": True,
        "mode": "authority_ledger_projection_v0",
        "record_count": len(records),
        "path": str(OUT),
        "runtime_mutation": False,
        "external_side_effects_executed": False,
        "payment_or_credential_action_executed": False,
        "agent_typed_secret": False,
        "records": [r["id"] for r in records],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
