#!/usr/bin/env python3
"""
Autonomous Evolution — Nightly Self-Audit (candidate-only, Loop A)

Transitional main for docs/private/dreaming-v1-frozen-spec-20260801.md Loop A:
selects one active skill via hermes_dreaming's deterministic selector state,
runs the full orchestrated cycle (selection -> ownership preflight ->
candidate-only generation -> evaluation), and writes a typed run receipt.

This script never mutates an active ``skills/<name>/SKILL.md`` — every
generated change lands as one flat V2 regular-file artifact under the
pre-provisioned ``HERMES_HOME/state/dreaming/candidates/`` root
(``candidate-v2--<run_id>--<skill>--<nonce>.json`` envelope), and
``promoted``/``state_advanced`` stay False on every receipt: Loop A has no
promotion gate.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import hermes_dreaming as hd
from hermes_evolution_store import default_store, resolved_to_dict

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
SKILLS_DIR = HERMES_HOME / "skills"
LOG_PATH = HERMES_HOME / "state" / "dreaming" / "autonomous-evolution-log.jsonl"
DEFAULT_RECEIPT_PATH = HERMES_HOME / "state" / "dreaming" / "last_run_receipt.json"

STORE = default_store()
DB_RESOLUTION = STORE.resolve_artifact(os.path.join("bayesian-agent", "confidence-db.json"), intent="read")
RESULTS_RESOLUTION = STORE.resolve_artifact(os.path.join("darwin-skill", "results.tsv"), intent="read")
DB_PATH = Path(DB_RESOLUTION.path)
RESULTS_PATH = Path(RESULTS_RESOLUTION.path)
DB_SOURCE = DB_RESOLUTION.source
RESULTS_SOURCE = RESULTS_RESOLUTION.source


def log_event(event_type: str, details: dict) -> None:
    if hd.dreaming_write_boundary_preflight(HERMES_HOME, LOG_PATH) is not None:
        return
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": event_type,
                    "details": details,
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def build_candidates() -> list[dict]:
    """Read-only candidate list for the selector: active skills the confidence
    DB knows about, scored by its existing (possibly stale) darwin_score."""
    if not DB_PATH.is_file():
        log_event("autonomous_evolution_degraded", {"reason": "confidence_db_missing", "path": str(DB_PATH)})
        return []

    try:
        db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        log_event("autonomous_evolution_degraded", {"reason": "confidence_db_unreadable", "path": str(DB_PATH)})
        return []

    candidates = []
    for name, data in (db.get("skills") or {}).items():
        if not (SKILLS_DIR / name / "SKILL.md").is_file():
            # DB may carry archived/historical entries; only active skills are candidates.
            continue
        candidates.append(
            {
                "name": name,
                "score": data.get("darwin_score", 0) or 0,
                "last_audit": data.get("last_audit"),
            }
        )

    if not candidates:
        log_event("autonomous_evolution_degraded", {"reason": "no_active_skill_candidates", "db_path": str(DB_PATH)})
    return candidates


def receipt_output_path() -> Path:
    override = os.environ.get("HERMES_DREAMING_RECEIPT_PATH")
    return Path(override) if override else DEFAULT_RECEIPT_PATH


def resolve_euid() -> int:
    override = os.environ.get("HERMES_DREAMING_EUID_OVERRIDE")
    if override is not None and override.strip():
        return int(override)
    return hd.current_euid()


def _emit_failure_receipt(receipt_path: Path, run_id: str, ts: datetime, exc: Exception) -> None:
    """Best-effort typed failure receipt for an unexpected top-level exception.

    Only the exception's class name is recorded — never its message or
    traceback — so a receipt can never leak internal state. The receipt
    write itself is boundary-gated: a ``receipt_path`` that escapes the real
    ``HERMES_HOME/state/dreaming`` tree is never written to, falling back to
    the safe default location; if even that is unsafe, nothing is written
    and ``main`` still returns a non-zero exit code either way.
    """
    receipt = hd.RunReceipt(run_id=run_id, ts=hd.format_ts(ts))
    receipt.job_success = False
    receipt.degraded = True
    receipt.add_reason(hd.REASON_UNEXPECTED_EXCEPTION)
    receipt.add_stage(
        hd.StageReceipt(hd.STAGE_RUN, False, hd.REASON_UNEXPECTED_EXCEPTION, {"error_type": type(exc).__name__})
    )
    boundary_reason = hd.dreaming_write_boundary_preflight(HERMES_HOME, receipt_path)
    if boundary_reason is not None:
        receipt.add_reason(boundary_reason)
        receipt_path = DEFAULT_RECEIPT_PATH
        if hd.dreaming_write_boundary_preflight(HERMES_HOME, receipt_path) is not None:
            return
    try:
        hd.atomic_write_text(
            receipt_path, json.dumps(receipt.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)
        )
    except OSError:
        pass


def main() -> int:
    print("=" * 60)
    print("Autonomous Evolution — Nightly Self-Audit (candidate-only, Loop A)")
    print("=" * 60)
    print(f"confidence_db: {DB_PATH} ({DB_SOURCE})")
    print(f"darwin_results: {RESULTS_PATH} ({RESULTS_SOURCE})")

    now = datetime.now(timezone.utc)
    run_id = os.environ.get("HERMES_DREAMING_RUN_ID") or now.strftime("nightly-%Y%m%dT%H%M%SZ")

    try:
        return _run(now, run_id)
    except Exception as exc:
        _emit_failure_receipt(receipt_output_path(), run_id, now, exc)
        return 1


def _run(now: datetime, run_id: str) -> int:
    # Root missing: entire Loop A fail-closed with zero state/dreaming writes.
    if not hd.candidates_root_is_provisioned(HERMES_HOME):
        print("ERROR candidate_root_unprovisioned")
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "job_success": False,
                    "candidate_generated": False,
                    "state_advanced": False,
                    "promoted": False,
                    "write_blocked": True,
                    "degraded": True,
                    "reasons": [hd.REASON_CANDIDATE_ROOT_UNPROVISIONED],
                    "candidate_artifact": None,
                    "run_id": run_id,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2

    candidates = build_candidates()
    euid = resolve_euid()

    receipt = hd.run_dreaming_cycle(HERMES_HOME, candidates, now, run_id=run_id, euid=euid)
    original_write_blocked = receipt.write_blocked

    # If the cycle still reports unprovisioned root, do not create sinks.
    if hd.REASON_CANDIDATE_ROOT_UNPROVISIONED in receipt.reasons:
        print("ERROR candidate_root_unprovisioned")
        print(json.dumps(receipt.to_dict(), ensure_ascii=False, sort_keys=True))
        return 2

    receipt_path = receipt_output_path()
    receipt_boundary_reason = hd.dreaming_write_boundary_preflight(HERMES_HOME, receipt_path)
    if receipt_boundary_reason is not None:
        receipt.write_blocked = True
        receipt.degraded = True
        receipt.job_success = False
        receipt.add_reason(receipt_boundary_reason)
        receipt_path = DEFAULT_RECEIPT_PATH
        if hd.dreaming_write_boundary_preflight(HERMES_HOME, receipt_path) is None:
            hd.atomic_write_text(
                receipt_path, json.dumps(receipt.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)
            )
        else:
            receipt_path = None
    else:
        hd.atomic_write_text(receipt_path, json.dumps(receipt.to_dict(), ensure_ascii=False, sort_keys=True, indent=2))

    health = hd.classify_receipt(receipt.to_dict())
    if hd.dreaming_write_boundary_preflight(HERMES_HOME, STORE.runs_path) is None:
        STORE.append_dream_run(
            {
                "run_id": run_id,
                "status": health["status"],
                "job_success": health["job_success"],
                "effective_audit": health["effective_audit"],
                "candidate_generated": health["candidate_generated"],
                "state_advanced": health["state_advanced"],
                "promoted": health["promoted"],
                "degraded": health["degraded"],
                "write_blocked": health["write_blocked"],
                "reasons": health["reasons"],
                "target": receipt.target,
                "candidate_artifact": health.get("candidate_artifact"),
                "confidence_db": resolved_to_dict(DB_RESOLUTION),
                "darwin_results": resolved_to_dict(RESULTS_RESOLUTION),
            }
        )

    print(f"\n目标: {receipt.target}")
    if receipt.target is None:
        print("无 skill 需要审计")
    elif original_write_blocked:
        print(f"⚠️ ownership preflight 阻止候选生成 [{receipt.target}]: {', '.join(receipt.reasons)}")
    elif receipt.candidate_generated:
        old_score = next((c["score"] for c in candidates if c["name"] == receipt.target), 0)
        generation = next(stage for stage in receipt.stages if stage.stage == hd.STAGE_GENERATION)
        evaluation = next(stage for stage in receipt.stages if stage.stage == hd.STAGE_EVALUATION)
        digest = generation.details["candidate_sha256"]
        size = generation.details["candidate_size"]
        applied = generation.details["applied_sections"]
        print(f"✓ 候选已生成（未晋升 active）[{receipt.target}]")
        print(f"  typed evidence: sha256={digest} size={size} applied_sections={','.join(applied)}")
        print(
            f"  evaluator: satisfied={evaluation.details['satisfied']} "
            f"missing_after={','.join(evaluation.details['missing_after']) or '(none)'}"
        )
        print(f"  active confidence score（只读既有值，未重算/未写入）: {old_score}")
    else:
        print(f"= 无变化 [{receipt.target}]: {', '.join(receipt.reasons) or '(none)'}")
    print(
        f"effective_audit={receipt.effective_audit} candidate_generated={receipt.candidate_generated} "
        f"state_advanced={receipt.state_advanced} promoted={receipt.promoted}"
    )
    print(f"receipt: {receipt_path}")

    log_event(
        "discussion_result",
        {
            "skill_audited": receipt.target,
            "run_type": "nightly_autonomous_evolution_candidate_only",
            "receipt": receipt.to_dict(),
        },
    )

    print("\n" + "=" * 60)
    return 0 if receipt.job_success else 2


if __name__ == "__main__":
    raise SystemExit(main())
