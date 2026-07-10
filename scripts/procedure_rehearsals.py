#!/usr/bin/env python3
"""Explicit local-only rehearsals for procedures safe to exercise on demand.

This script is intentionally separate from the high-frequency selfcheck evaluator:
the evaluator consumes receipts but never executes declared procedures.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def load_lifecycle_module():
    path = Path(__file__).with_name("experience_ratchet_lifecycle.py")
    spec = importlib.util.spec_from_file_location("experience_ratchet_lifecycle", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load lifecycle module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lifecycle_fixture(atom_id: str, status: str, at: str, failures: int = 0) -> dict[str, Any]:
    return {
        "schema_version": "experience_atom.v1",
        "atom_id": atom_id,
        "title": atom_id,
        "claim_text": f"isolated lifecycle rehearsal fixture {atom_id}",
        "source": {"project": "isolated-lifecycle-rehearsal", "captured_at": at},
        "classification": {"target_landing_zone": "noop"},
        "guards": {"applicability_conditions": [], "anti_conditions": ["fixture-only"], "falsifiers": ["counterexample"]},
        "evidence_refs": [{"kind": "fixture", "ref": "isolated-local-rehearsal"}],
        "dissent_refs": [],
        "relations": [],
        "status": status,
        "promotion": {"state": "candidate" if status == "promoted_candidate" else "promoted" if status == "promoted" else "none"},
        "rollback": {"revoked_reason": None},
        "metrics": {"failure_count": failures},
        "history": [{"at": at, "event": f"fixture:{status}", "reason": "isolated rehearsal"}],
    }


def rehearse_local_delivery(output_dir: Path, payload: str = "hermes-local-delivery-canary") -> dict[str, Any]:
    if not payload.strip():
        raise ValueError("payload must be non-empty")
    output_dir = Path(output_dir).expanduser().resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    nonce = uuid.uuid4().hex
    receipt_id = f"delivery.local.output-{stamp}-{nonce}"
    run_dir = output_dir / "procedure-rehearsals" / receipt_id
    payload_path = run_dir / "payload.txt"
    readback_path = run_dir / "receipt-readback.json"
    receipt_dir = output_dir / "procedure-receipts"
    receipt_path = receipt_dir / f"{receipt_id}.json"
    receipt_temp = receipt_dir / f".{receipt_id}.{nonce}.tmp"
    started_at = utc_now()

    run_dir.mkdir(parents=True, exist_ok=False)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(payload.rstrip("\n") + "\n", encoding="utf-8")
    if payload_path.read_text(encoding="utf-8") != payload.rstrip("\n") + "\n":
        raise RuntimeError("local payload readback mismatch")

    receipt = {
        "schema": "hermes_procedure_e2e_receipt_v1",
        "receipt_id": receipt_id,
        "procedure_id": "delivery.local.output",
        "started_at": started_at,
        "completed_at": utc_now(),
        "result": "PASS",
        "execution_mode": "live_e2e",
        "evidence_refs": [str(payload_path), str(readback_path)],
        "acceptance_atoms": {"payload_written": True, "receipt_readback": True},
        "negative_assertions": {"no_external_send": True},
        "cleanup_readback": "PASS",
        "authority": {"status": "not_required", "ref": "explicit-local-rehearsal"},
        "side_effects_observed": ["local_write"],
        "emitter": "procedure_rehearsals.rehearse_local_delivery",
    }
    if receipt_path.exists():
        raise FileExistsError(f"immutable receipt already exists: {receipt_path}")
    receipt_temp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readback_receipt = json.loads(receipt_temp.read_text(encoding="utf-8"))
    if readback_receipt.get("receipt_id") != receipt_id or readback_receipt.get("result") != "PASS":
        receipt_temp.unlink(missing_ok=True)
        raise RuntimeError("receipt pre-commit readback failed")
    write_json_atomic(readback_path, {"schema": "hermes_procedure_receipt_readback_v1", "receipt_id": receipt_id, "status": "PASS", "read_at": utc_now()})
    os.replace(receipt_temp, receipt_path)
    committed = json.loads(receipt_path.read_text(encoding="utf-8"))
    if committed != receipt:
        raise RuntimeError("committed receipt readback mismatch")
    return {
        "ok": True,
        "procedure_id": "delivery.local.output",
        "receipt_id": receipt_id,
        "payload_path": str(payload_path),
        "readback_path": str(readback_path),
        "receipt_path": str(receipt_path),
        "side_effects": ["local_write"],
        "external_send": False,
    }


def rehearse_experience_ratchet_lifecycle(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir).expanduser().resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    nonce = uuid.uuid4().hex
    receipt_id = f"experience.ratchet.lifecycle-{stamp}-{nonce}"
    run_dir = output_dir / "procedure-rehearsals" / receipt_id
    store = run_dir / "experience-home"
    atoms_dir = store / "atoms"
    receipt_dir = output_dir / "procedure-receipts"
    receipt_path = receipt_dir / f"{receipt_id}.json"
    lifecycle_result_path = run_dir / "lifecycle-result.json"
    readback_path = run_dir / "lifecycle-readback.json"
    started_at = utc_now()
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=45)).isoformat().replace("+00:00", "Z")
    recent = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")

    atoms_dir.mkdir(parents=True, exist_ok=False)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    fixtures = [
        lifecycle_fixture("stale-candidate", "promoted_candidate", old),
        lifecycle_fixture("failed-promotion", "promoted", recent, failures=2),
        lifecycle_fixture("terminal-retention", "revoked", old),
    ]
    for fixture in fixtures:
        write_json_atomic(atoms_dir / f"{fixture['atom_id']}.json", fixture)

    lifecycle = load_lifecycle_module()
    result = lifecycle.reconcile_store(
        store,
        now=now,
        stale_days=14,
        failure_threshold=1,
        retention_days=30,
        apply=True,
    )
    summary = result["summary"]
    acceptance_atoms = {
        "promotion_guarded": summary["promotion_actions"] == 0,
        "stale_demoted": summary["stale_demoted"] == 1,
        "failure_reopened": summary["failure_reopened"] == 1,
        "retention_applied": summary["retention_applied"] == 1,
    }
    negative_assertions = {
        "no_silent_promotion": summary["promotion_actions"] == 0,
        "no_history_erasure": summary["history_erased"] == 0,
    }
    if not result.get("ok") or not all(acceptance_atoms.values()) or not all(negative_assertions.values()):
        raise RuntimeError("isolated lifecycle rehearsal did not satisfy all gates")
    write_json_atomic(lifecycle_result_path, result)
    temp_files = [str(path) for path in run_dir.rglob(".*.tmp")]
    write_json_atomic(readback_path, {
        "schema": "hermes_experience_ratchet_lifecycle_readback_v1",
        "receipt_id": receipt_id,
        "status": "PASS" if not temp_files else "FAIL",
        "isolated_store": store.is_relative_to(run_dir),
        "temp_files_remaining": temp_files,
        "read_at": utc_now(),
    })
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    if readback["status"] != "PASS" or not readback["isolated_store"]:
        raise RuntimeError("lifecycle cleanup/readback failed")

    receipt = {
        "schema": "hermes_procedure_e2e_receipt_v1",
        "receipt_id": receipt_id,
        "procedure_id": "experience.ratchet.lifecycle",
        "started_at": started_at,
        "completed_at": utc_now(),
        "result": "PASS",
        "execution_mode": "live_e2e",
        "evidence_refs": [str(lifecycle_result_path), str(readback_path)],
        "acceptance_atoms": acceptance_atoms,
        "negative_assertions": negative_assertions,
        "cleanup_readback": "PASS",
        "authority": {"status": "not_required", "ref": "explicit-local-isolated-rehearsal"},
        "side_effects_observed": ["local_write"],
        "emitter": "procedure_rehearsals.rehearse_experience_ratchet_lifecycle",
    }
    if receipt_path.exists():
        raise FileExistsError(f"immutable receipt already exists: {receipt_path}")
    write_json_atomic(receipt_path, receipt)
    if json.loads(receipt_path.read_text(encoding="utf-8")) != receipt:
        raise RuntimeError("committed lifecycle receipt readback mismatch")
    return {
        "ok": True,
        "procedure_id": "experience.ratchet.lifecycle",
        "receipt_id": receipt_id,
        "receipt_path": str(receipt_path),
        "lifecycle_result_path": str(lifecycle_result_path),
        "readback_path": str(readback_path),
        "isolated_store": str(store),
        "side_effects": ["local_write"],
        "external_send": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explicit local-only Hermes procedure rehearsals")
    sub = parser.add_subparsers(dest="command", required=True)
    local = sub.add_parser("local-delivery")
    local.add_argument("--output-dir", default=os.path.expanduser("~/.hermes/state/selfcheck"))
    local.add_argument("--payload", default="hermes-local-delivery-canary")
    lifecycle = sub.add_parser("experience-ratchet-lifecycle")
    lifecycle.add_argument("--output-dir", default=os.path.expanduser("~/.hermes/state/selfcheck"))
    args = parser.parse_args(argv)
    if args.command == "local-delivery":
        result = rehearse_local_delivery(Path(args.output_dir), args.payload)
    elif args.command == "experience-ratchet-lifecycle":
        result = rehearse_experience_ratchet_lifecycle(Path(args.output_dir))
    else:  # pragma: no cover - argparse enforces commands
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
