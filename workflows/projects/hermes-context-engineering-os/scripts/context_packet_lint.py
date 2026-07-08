#!/usr/bin/env python3
"""Minimal dependency-free lint for Hermes Context Packet JSON.

This intentionally validates the operational contract rather than the full JSON Schema spec,
so it runs on stock Python without jsonschema/PyYAML.
"""
import json, sys
from pathlib import Path

REQUIRED = [
    "objective", "non_goals", "constraints", "sources", "selected_context",
    "authority", "execution_plan", "validation_plan", "negative_cases", "learning_boundary"
]
SOURCE_REQUIRED = ["id", "type", "locator", "claims"]
AUTH_REQUIRED = ["allowed", "closed", "readback_required"]
LEARNING_REQUIRED = ["durable_memory_allowed", "skill_update_allowed", "ssot_update_allowed", "do_not_save"]
ALLOWED_SOURCE_TYPES = {"file", "url", "session", "tool_output", "screenshot", "api", "log", "profile", "skill"}


def fail(msg):
    print(f"FAIL: {msg}")
    return 1


def main(path):
    p = Path(path)
    if not p.exists():
        return fail(f"packet not found: {p}")
    try:
        packet = json.loads(p.read_text())
    except Exception as e:
        return fail(f"invalid JSON: {e}")
    if not isinstance(packet, dict):
        return fail("top-level packet must be an object")
    missing = [k for k in REQUIRED if k not in packet]
    if missing:
        return fail(f"missing required fields: {missing}")
    if len(str(packet.get("objective", "")).strip()) < 8:
        return fail("objective too short")
    sources = packet["sources"]
    if not isinstance(sources, list) or not sources:
        return fail("sources must be a non-empty list")
    ids = set()
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            return fail(f"source[{i}] must be object")
        sm = [k for k in SOURCE_REQUIRED if k not in src]
        if sm:
            return fail(f"source[{i}] missing {sm}")
        if src["type"] not in ALLOWED_SOURCE_TYPES:
            return fail(f"source[{i}] invalid type {src['type']}")
        if not src.get("claims"):
            return fail(f"source[{i}] has no claims")
        if src["id"] in ids:
            return fail(f"duplicate source id {src['id']}")
        ids.add(src["id"])
    sel = packet["selected_context"]
    if not isinstance(sel, dict):
        return fail("selected_context must be object")
    evidence_ids = set(sel.get("evidence_ids", []))
    unknown = sorted(evidence_ids - ids)
    if unknown:
        return fail(f"selected_context.evidence_ids not in sources: {unknown}")
    auth = packet["authority"]
    if not isinstance(auth, dict):
        return fail("authority must be object")
    am = [k for k in AUTH_REQUIRED if k not in auth]
    if am:
        return fail(f"authority missing {am}")
    if not auth.get("readback_required"):
        return fail("authority.readback_required must not be empty")
    lb = packet["learning_boundary"]
    if not isinstance(lb, dict):
        return fail("learning_boundary must be object")
    lm = [k for k in LEARNING_REQUIRED if k not in lb]
    if lm:
        return fail(f"learning_boundary missing {lm}")
    if not lb.get("do_not_save"):
        return fail("learning_boundary.do_not_save must not be empty")
    print(f"PASS: {p}")
    print(f"sources={len(sources)} evidence_ids={len(evidence_ids)} closed_authority={len(auth.get('closed', []))}")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: context_packet_lint.py PACKET.json")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
