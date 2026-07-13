#!/usr/bin/env python3
"""Deterministically project governed current state into JSON Canvas 1.0.

This is a local, one-way projection only. It does not execute Canvas nodes, mutate
canonical state from Canvas edits, call networks, or perform external side effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

SCHEMA_VERSION = "shared_canvas_state.v1"
NODE_KINDS = {
    "goal",
    "decision",
    "requirement",
    "task",
    "risk",
    "question",
    "evidence",
    "artifact",
    "agent",
}
NODE_STATUSES = {
    "proposed",
    "confirmed",
    "in_progress",
    "blocked",
    "superseded",
    "done",
    "archived",
}
AUTHORITIES = {"read_only", "human_owned", "agent_writable", "joint_review"}
EDGE_KINDS = {
    "depends_on",
    "blocks",
    "produces",
    "supports",
    "contradicts",
    "supersedes",
    "responsible_for",
    "input_to",
}
STATUS_COLORS = {
    "proposed": "3",
    "confirmed": "4",
    "in_progress": "5",
    "blocked": "1",
    "superseded": "2",
    "done": "4",
    "archived": "6",
}


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _require_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{field} must be a list of strings")
    return value


def validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    _require_int(state.get("revision"), "revision")
    nodes = state.get("nodes")
    edges = state.get("edges")
    if not isinstance(nodes, list):
        raise ValueError("nodes must be a list")
    if not isinstance(edges, list):
        raise ValueError("edges must be a list")

    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"nodes[{index}] must be an object")
        node_id = _require_text(node.get("id"), f"nodes[{index}].id")
        if node_id in node_ids:
            raise ValueError(f"duplicate node id: {node_id}")
        node_ids.add(node_id)
        kind = _require_text(node.get("kind"), f"nodes[{index}].kind")
        if kind not in NODE_KINDS:
            raise ValueError(f"unsupported node kind: {kind}")
        status = _require_text(node.get("status"), f"nodes[{index}].status")
        if status not in NODE_STATUSES:
            raise ValueError(f"unsupported node status: {status}")
        _require_text(node.get("owner"), f"nodes[{index}].owner")
        _require_int(node.get("revision"), f"nodes[{index}].revision")
        _require_text(node.get("summary"), f"nodes[{index}].summary")
        _require_string_list(node.get("source_refs"), f"nodes[{index}].source_refs")
        _require_string_list(node.get("evidence_refs"), f"nodes[{index}].evidence_refs")
        authority = _require_text(node.get("authority"), f"nodes[{index}].authority")
        if authority not in AUTHORITIES:
            raise ValueError(f"unsupported authority: {authority}")

    edge_ids: set[str] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError(f"edges[{index}] must be an object")
        edge_id = _require_text(edge.get("id"), f"edges[{index}].id")
        if edge_id in edge_ids:
            raise ValueError(f"duplicate edge id: {edge_id}")
        edge_ids.add(edge_id)
        kind = _require_text(edge.get("kind"), f"edges[{index}].kind")
        if kind not in EDGE_KINDS:
            raise ValueError(f"unsupported edge kind: {kind}")
        source = _require_text(edge.get("from"), f"edges[{index}].from")
        target = _require_text(edge.get("to"), f"edges[{index}].to")
        if source not in node_ids or target not in node_ids:
            raise ValueError(f"edge {edge_id} has unknown endpoint")
        label = edge.get("label", "")
        if not isinstance(label, str):
            raise ValueError(f"edges[{index}].label must be a string")
    return state


def _node_text(node: dict[str, Any]) -> str:
    source_refs = ", ".join(node["source_refs"]) or "none"
    evidence_refs = ", ".join(node["evidence_refs"]) or "none"
    return "\n".join(
        [
            f"# {node['summary']}",
            "",
            f"id: {node['id']}",
            f"kind: {node['kind']}",
            f"status: {node['status']}",
            f"owner: {node['owner']}",
            f"revision: {node['revision']}",
            f"authority: {node['authority']}",
            f"source_refs: {source_refs}",
            f"evidence_refs: {evidence_refs}",
        ]
    )


def project_state(state: Any) -> dict[str, Any]:
    validated = validate_state(state)
    projected_nodes: list[dict[str, Any]] = []
    for index, node in enumerate(validated["nodes"]):
        projected_nodes.append(
            {
                "id": node["id"],
                "type": "text",
                "text": _node_text(node),
                "x": (index % 3) * 420,
                "y": (index // 3) * 280,
                "width": 360,
                "height": 220,
                "color": STATUS_COLORS[node["status"]],
            }
        )

    projected_edges: list[dict[str, Any]] = []
    for edge in validated["edges"]:
        label = edge["kind"]
        if edge.get("label"):
            label += f": {edge['label']}"
        projected_edges.append(
            {
                "id": edge["id"],
                "fromNode": edge["from"],
                "toNode": edge["to"],
                "label": label,
            }
        )
    return {"nodes": projected_nodes, "edges": projected_edges}


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="canonical shared_canvas_state.v1 JSON")
    parser.add_argument("output", type=Path, help="JSON Canvas .canvas output")
    parser.add_argument("--receipt", type=Path, help="optional local projection receipt")
    args = parser.parse_args(argv)

    source_bytes = args.source.read_bytes()
    state = json.loads(source_bytes.decode("utf-8"))
    canvas = project_state(state)
    canvas_bytes = _canonical_bytes(canvas)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canvas_bytes)

    if args.receipt is not None:
        receipt = {
            "schema_version": "shared_canvas_projection_receipt.v1",
            "source_revision": state["revision"],
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "canvas_sha256": hashlib.sha256(canvas_bytes).hexdigest(),
            "node_count": len(canvas["nodes"]),
            "edge_count": len(canvas["edges"]),
            "runtime_effect": "local_projection_only",
            "external_side_effects": False,
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_bytes(_canonical_bytes(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
