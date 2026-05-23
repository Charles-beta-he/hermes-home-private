#!/usr/bin/env python3
"""Experience Ratchet Maze — external dev-brain overlay for reusable project experience.

This script is intentionally outside Hermes core. It stores evidence-gated
ExperienceAtom records, validates state transitions, and emits promotion
proposals instead of mutating memory/skills/profiles/taskpool directly.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SCHEMA_VERSION = "experience_atom.v1"
DEFAULT_HOME = Path(os.environ.get("HERMES_EXPERIENCE_HOME", Path.home() / ".hermes" / "experience-ratchet"))
STATUSES = [
    "captured",
    "normalized",
    "challenged",
    "validated",
    "promoted_candidate",
    "promoted",
    "deprecated",
    "rolled_back",
    "revoked",
]
LANDING_ZONES = ["skill", "memory", "profile", "taskpool", "project_doc", "public_consensus", "noop"]
RELATION_TYPES = ["similar_to", "depends_on", "contradicts", "supersedes", "derived_from", "applies_to", "verified_by", "falsified_by"]
FORWARD_TRANSITIONS = {
    "captured": {"normalized", "challenged", "deprecated", "revoked"},
    "normalized": {"challenged", "validated", "deprecated", "revoked"},
    "challenged": {"normalized", "validated", "deprecated", "revoked"},
    "validated": {"promoted_candidate", "deprecated", "revoked"},
    "promoted_candidate": {"promoted", "validated", "deprecated", "revoked"},
    "promoted": {"deprecated", "rolled_back", "revoked"},
    "deprecated": {"normalized", "revoked"},
    "rolled_back": {"validated", "deprecated", "revoked"},
    "revoked": set(),
}
EVIDENCE_REQUIRED = {"validated", "promoted_candidate", "promoted"}
REASON_REQUIRED = {"challenged", "deprecated", "rolled_back", "revoked"}


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", text.strip().lower()).strip("-")
    return (slug or "atom")[:limit]


def ensure_store(home: Path) -> None:
    for sub in ["atoms", "proposals", "logs", "schema", "maze"]:
        (home / sub).mkdir(parents=True, exist_ok=True)


def atom_path(home: Path, atom_id: str) -> Path:
    return home / "atoms" / f"{atom_id}.json"


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_log(home: Path, event: Dict[str, Any]) -> None:
    event = {"at": now_iso(), **event}
    with (home / "logs" / "events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def parse_kv_list(items: Iterable[str]) -> List[Dict[str, str]]:
    out = []
    for raw in items or []:
        if ":" in raw:
            kind, ref = raw.split(":", 1)
        else:
            kind, ref = "note", raw
        out.append({"kind": kind.strip() or "note", "ref": ref.strip()})
    return out


def new_atom(args: argparse.Namespace) -> Dict[str, Any]:
    home = Path(args.home).expanduser()
    ensure_store(home)
    seed = f"{args.project}\n{args.claim}\n{now_iso()}\n{uuid.uuid4()}"
    atom_id = f"{slugify(args.project)}-{hashlib.sha256(seed.encode()).hexdigest()[:12]}"
    atom = {
        "schema_version": SCHEMA_VERSION,
        "atom_id": atom_id,
        "title": args.title or args.claim[:80],
        "claim_text": args.claim,
        "source": {
            "project": args.project,
            "event": args.event or "manual_capture",
            "captured_at": now_iso(),
            "author": args.author or "hermes-agent",
        },
        "classification": {
            "pattern_type": args.pattern_type,
            "abstraction_level": "L0_raw_trace",
            "target_landing_zone": args.landing_zone,
            "domain_tags": [x for x in args.tag if x],
        },
        "guards": {
            "applicability_conditions": [x for x in args.applies if x],
            "anti_conditions": [x for x in args.anti if x],
            "falsifiers": [x for x in args.falsifier if x],
        },
        "evidence_refs": parse_kv_list(args.evidence),
        "dissent_refs": parse_kv_list(args.dissent),
        "relations": [],
        "status": "captured",
        "promotion": {
            "state": "none",
            "candidate_at": None,
            "promoted_at": None,
            "landing_zone": args.landing_zone,
            "proposal_ref": None,
        },
        "rollback": {
            "supersedes": None,
            "superseded_by": None,
            "revoked_reason": None,
            "rollback_pointer": None,
        },
        "metrics": {
            "reuse_count": 0,
            "failure_count": 0,
            "confidence": args.confidence,
        },
        "history": [{"at": now_iso(), "event": "captured", "reason": args.reason or "initial capture"}],
    }
    errors = validate_atom(atom)
    if errors:
        raise SystemExit("invalid new atom: " + "; ".join(errors))
    write_json(atom_path(home, atom_id), atom)
    append_log(home, {"event": "atom_created", "atom_id": atom_id, "path": str(atom_path(home, atom_id))})
    return {"ok": True, "atom_id": atom_id, "path": str(atom_path(home, atom_id))}


def validate_atom(atom: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = ["schema_version", "atom_id", "title", "claim_text", "source", "classification", "guards", "evidence_refs", "dissent_refs", "relations", "status", "promotion", "rollback", "history"]
    for key in required:
        if key not in atom:
            errors.append(f"missing {key}")
    if atom.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if atom.get("status") not in STATUSES:
        errors.append(f"status must be one of {STATUSES}")
    classification = atom.get("classification") or {}
    if classification.get("target_landing_zone") not in LANDING_ZONES:
        errors.append(f"target_landing_zone must be one of {LANDING_ZONES}")
    if atom.get("status") in EVIDENCE_REQUIRED and not atom.get("evidence_refs"):
        errors.append(f"status {atom.get('status')} requires evidence_refs")
    for relation in atom.get("relations") or []:
        if relation.get("type") not in RELATION_TYPES:
            errors.append(f"invalid relation type: {relation.get('type')}")
        if not relation.get("target_atom_id"):
            errors.append("relation missing target_atom_id")
    for idx, ev in enumerate(atom.get("evidence_refs") or []):
        if not isinstance(ev, dict) or not ev.get("ref"):
            errors.append(f"evidence_refs[{idx}] missing ref")
    guards = atom.get("guards") or {}
    if atom.get("status") in {"promoted_candidate", "promoted"} and not guards.get("falsifiers"):
        errors.append("promotion states require at least one falsifier")
    return errors


def transition(args: argparse.Namespace) -> Dict[str, Any]:
    home = Path(args.home).expanduser()
    path = atom_path(home, args.atom_id)
    atom = read_json(path)
    old = atom.get("status")
    new = args.status
    if new not in FORWARD_TRANSITIONS.get(old, set()):
        raise SystemExit(f"illegal transition {old} -> {new}")
    if new in REASON_REQUIRED and not args.reason:
        raise SystemExit(f"transition to {new} requires --reason")
    added_evidence = parse_kv_list(args.evidence)
    if added_evidence:
        atom.setdefault("evidence_refs", []).extend(added_evidence)
    added_dissent = parse_kv_list(args.dissent)
    if added_dissent:
        atom.setdefault("dissent_refs", []).extend(added_dissent)
    atom["status"] = new
    if new == "promoted_candidate":
        atom.setdefault("promotion", {})["state"] = "candidate"
        atom["promotion"]["candidate_at"] = now_iso()
    elif new == "promoted":
        atom.setdefault("promotion", {})["state"] = "promoted"
        atom["promotion"]["promoted_at"] = now_iso()
    elif new in {"deprecated", "rolled_back", "revoked"}:
        atom.setdefault("rollback", {})["revoked_reason"] = args.reason
    atom.setdefault("history", []).append({"at": now_iso(), "event": f"transition:{old}->{new}", "reason": args.reason or "", "evidence_added": added_evidence, "dissent_added": added_dissent})
    errors = validate_atom(atom)
    if errors:
        raise SystemExit("invalid transition result: " + "; ".join(errors))
    write_json(path, atom)
    append_log(home, {"event": "transition", "atom_id": args.atom_id, "from": old, "to": new, "reason": args.reason or ""})
    return {"ok": True, "atom_id": args.atom_id, "from": old, "to": new, "path": str(path)}


def add_relation(args: argparse.Namespace) -> Dict[str, Any]:
    home = Path(args.home).expanduser()
    path = atom_path(home, args.atom_id)
    target = atom_path(home, args.target_atom_id)
    if not target.exists():
        raise SystemExit(f"target atom not found: {args.target_atom_id}")
    atom = read_json(path)
    atom.setdefault("relations", []).append({"type": args.type, "target_atom_id": args.target_atom_id, "weight": args.weight, "reason": args.reason or ""})
    errors = validate_atom(atom)
    if errors:
        raise SystemExit("invalid relation result: " + "; ".join(errors))
    write_json(path, atom)
    append_log(home, {"event": "relation_added", "atom_id": args.atom_id, "type": args.type, "target_atom_id": args.target_atom_id})
    return {"ok": True, "atom_id": args.atom_id, "target_atom_id": args.target_atom_id, "type": args.type}


def load_atoms(home: Path) -> List[Dict[str, Any]]:
    ensure_store(home)
    atoms = []
    for p in sorted((home / "atoms").glob("*.json")):
        atoms.append(read_json(p))
    return atoms


def validate_cmd(args: argparse.Namespace) -> Dict[str, Any]:
    home = Path(args.home).expanduser()
    paths = [Path(args.file).expanduser()] if args.file else sorted((home / "atoms").glob("*.json"))
    results = []
    ok = True
    for p in paths:
        atom = read_json(p)
        errors = validate_atom(atom)
        if errors:
            ok = False
        results.append({"path": str(p), "atom_id": atom.get("atom_id"), "ok": not errors, "errors": errors})
    return {"ok": ok, "checked": len(results), "results": results}


def propose(args: argparse.Namespace) -> Dict[str, Any]:
    home = Path(args.home).expanduser()
    path = atom_path(home, args.atom_id)
    atom = read_json(path)
    errors = validate_atom(atom)
    if errors:
        raise SystemExit("cannot propose invalid atom: " + "; ".join(errors))
    if atom.get("status") not in {"validated", "promoted_candidate", "promoted"}:
        raise SystemExit("promotion proposal requires status validated/promoted_candidate/promoted")
    if not atom.get("evidence_refs"):
        raise SystemExit("promotion proposal requires evidence_refs")
    zone = atom.get("classification", {}).get("target_landing_zone")
    proposal = {
        "schema_version": "experience_promotion_proposal.v1",
        "proposal_id": f"proposal-{args.atom_id}-{now_iso().replace(':','').replace('-','')}",
        "created_at": now_iso(),
        "atom_id": args.atom_id,
        "landing_zone": zone,
        "claim_text": atom.get("claim_text"),
        "suggested_side_effect": {
            "skill": "suggest_skill_patch",
            "memory": "suggest_memory_write",
            "profile": "suggest_profile_patch",
            "taskpool": "suggest_taskpool_item",
            "project_doc": "suggest_project_doc_update",
            "public_consensus": "suggest_public_consensus_update",
            "noop": "no_op",
        }[zone],
        "evidence_refs": atom.get("evidence_refs", []),
        "dissent_refs": atom.get("dissent_refs", []),
        "falsifiers": atom.get("guards", {}).get("falsifiers", []),
        "required_human_review": zone in {"memory", "public_consensus"},
        "write_policy": "proposal_only_no_direct_mutation",
    }
    p = home / "proposals" / f"{proposal['proposal_id']}.json"
    write_json(p, proposal)
    atom.setdefault("promotion", {})["proposal_ref"] = str(p)
    if atom.get("status") == "validated":
        atom["status"] = "promoted_candidate"
        atom["promotion"]["state"] = "candidate"
        atom["promotion"]["candidate_at"] = now_iso()
        atom.setdefault("history", []).append({"at": now_iso(), "event": "proposal_created_and_candidate", "proposal_ref": str(p)})
        write_json(path, atom)
    append_log(home, {"event": "proposal_created", "atom_id": args.atom_id, "proposal": str(p), "landing_zone": zone})
    return {"ok": True, "proposal": str(p), "atom_status": atom.get("status"), "write_policy": "proposal_only_no_direct_mutation"}


def query(args: argparse.Namespace) -> Dict[str, Any]:
    home = Path(args.home).expanduser()
    atoms = load_atoms(home)
    if args.status:
        atoms = [a for a in atoms if a.get("status") == args.status]
    if args.landing_zone:
        atoms = [a for a in atoms if a.get("classification", {}).get("target_landing_zone") == args.landing_zone]
    if args.project:
        atoms = [a for a in atoms if a.get("source", {}).get("project") == args.project]
    if args.tag:
        atoms = [a for a in atoms if args.tag in a.get("classification", {}).get("domain_tags", [])]
    return {"ok": True, "count": len(atoms), "atoms": [{"atom_id": a.get("atom_id"), "title": a.get("title"), "status": a.get("status"), "landing_zone": a.get("classification", {}).get("target_landing_zone"), "project": a.get("source", {}).get("project")} for a in atoms]}


def init_cmd(args: argparse.Namespace) -> Dict[str, Any]:
    home = Path(args.home).expanduser()
    ensure_store(home)
    write_json(home / "schema" / "experience_atom.schema.json", schema_doc())
    write_json(home / "schema" / "core_hook_contract.schema.json", core_hook_contract())
    readme = home / "README.md"
    if not readme.exists():
        readme.write_text("# Experience Ratchet Maze\n\nExternal dev-brain overlay. Proposal-only by default; no Hermes core mutation.\n", encoding="utf-8")
    return {"ok": True, "home": str(home), "schema": str(home / "schema" / "experience_atom.schema.json")}


def schema_doc() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ExperienceAtom",
        "schema_version": SCHEMA_VERSION,
        "type": "object",
        "required": ["schema_version", "atom_id", "title", "claim_text", "source", "classification", "guards", "evidence_refs", "dissent_refs", "relations", "status", "promotion", "rollback", "history"],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "status": {"enum": STATUSES},
            "classification": {"type": "object", "properties": {"target_landing_zone": {"enum": LANDING_ZONES}}},
            "relations": {"type": "array", "items": {"type": "object", "properties": {"type": {"enum": RELATION_TYPES}, "target_atom_id": {"type": "string"}}}},
        },
    }


def core_hook_contract() -> Dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ExperienceRatchetCoreHookContract",
        "policy": "default_off_proposal_only_no_direct_mutation",
        "input_status_allowed": ["promoted_candidate", "promoted"],
        "allowed_side_effects": ["no_op", "suggest_skill_patch", "suggest_memory_write", "suggest_profile_patch", "suggest_taskpool_item", "suggest_project_doc_update", "suggest_public_consensus_update"],
        "forbidden_side_effects": ["direct_memory_write", "direct_skill_edit", "direct_profile_edit", "direct_taskpool_add", "direct_core_patch"],
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Experience Ratchet Maze external dev-brain overlay")
    parser.add_argument("--home", default=str(DEFAULT_HOME), help="store directory (default: ~/.hermes/experience-ratchet)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create store directories and schema docs")
    p.set_defaults(func=init_cmd)

    p = sub.add_parser("new", help="capture a new ExperienceAtom")
    p.add_argument("--project", required=True)
    p.add_argument("--claim", required=True)
    p.add_argument("--title")
    p.add_argument("--event")
    p.add_argument("--author")
    p.add_argument("--pattern-type", default="heuristic", choices=["architecture", "implementation", "pitfall", "config", "heuristic", "ux", "testing", "workflow"])
    p.add_argument("--landing-zone", default="noop", choices=LANDING_ZONES)
    p.add_argument("--tag", action="append", default=[])
    p.add_argument("--applies", action="append", default=[])
    p.add_argument("--anti", action="append", default=[])
    p.add_argument("--falsifier", action="append", default=[])
    p.add_argument("--evidence", action="append", default=[])
    p.add_argument("--dissent", action="append", default=[])
    p.add_argument("--confidence", type=float, default=0.2)
    p.add_argument("--reason")
    p.set_defaults(func=new_atom)

    p = sub.add_parser("validate", help="validate one atom or all atoms")
    p.add_argument("--file")
    p.set_defaults(func=validate_cmd)

    p = sub.add_parser("transition", help="transition atom status with gates")
    p.add_argument("atom_id")
    p.add_argument("status", choices=STATUSES)
    p.add_argument("--reason")
    p.add_argument("--evidence", action="append", default=[])
    p.add_argument("--dissent", action="append", default=[])
    p.set_defaults(func=transition)

    p = sub.add_parser("relate", help="add a MemoryMaze edge")
    p.add_argument("atom_id")
    p.add_argument("type", choices=RELATION_TYPES)
    p.add_argument("target_atom_id")
    p.add_argument("--weight", type=float, default=0.5)
    p.add_argument("--reason")
    p.set_defaults(func=add_relation)

    p = sub.add_parser("propose", help="emit proposal-only landing-zone artifact")
    p.add_argument("atom_id")
    p.set_defaults(func=propose)

    p = sub.add_parser("query", help="query atoms")
    p.add_argument("--status", choices=STATUSES)
    p.add_argument("--landing-zone", choices=LANDING_ZONES)
    p.add_argument("--project")
    p.add_argument("--tag")
    p.set_defaults(func=query)

    args = parser.parse_args(argv)
    try:
        result = args.func(args)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result.get("ok", False) else 2
    except SystemExit:
        raise
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
