#!/usr/bin/env python3
"""Classify JSON Canvas edits into non-executing, reviewable change intents.

The classifier never mutates canonical state, executes nodes, invokes tools, calls
networks, or applies any change. Its output is a proposal packet only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

PRESENTATION_FIELDS = {"x", "y", "width", "height", "color"}


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _index_items(items: Any, kind: str) -> tuple[list[str], dict[str, dict[str, Any]]]:
    if not isinstance(items, list):
        raise ValueError(f"{kind} must be a list")
    order: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"{kind}[{index}] must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(f"{kind}[{index}].id must be a non-empty string")
        if item_id in indexed:
            raise ValueError(f"duplicate {kind[:-1]} id: {item_id}")
        order.append(item_id)
        indexed[item_id] = item
    return order, indexed


def validate_canvas(canvas: Any) -> dict[str, Any]:
    if not isinstance(canvas, dict):
        raise ValueError("canvas must be an object")
    node_order, nodes = _index_items(canvas.get("nodes"), "nodes")
    edge_order, edges = _index_items(canvas.get("edges"), "edges")
    node_ids = set(nodes)
    for node_id in node_order:
        node = nodes[node_id]
        node_type = node.get("type")
        if not isinstance(node_type, str) or not node_type:
            raise ValueError(f"node {node_id} has invalid type")
        for field in ("x", "y", "width", "height"):
            if not isinstance(node.get(field), (int, float)) or isinstance(node.get(field), bool):
                raise ValueError(f"node {node_id} has invalid {field}")
    for edge_id in edge_order:
        edge = edges[edge_id]
        source = edge.get("fromNode")
        target = edge.get("toNode")
        if source not in node_ids or target not in node_ids:
            raise ValueError(f"edge {edge_id} has unknown endpoint")
    return canvas


def _changed_fields(before: dict[str, Any], after: dict[str, Any], fields: set[str] | None = None) -> list[str]:
    keys = set(before) | set(after)
    if fields is not None:
        keys &= fields
    return sorted(key for key in keys if before.get(key) != after.get(key))


def _intent_id(kind: str, target_id: str) -> str:
    return f"intent:{kind}:{target_id}"


def classify_changes(baseline: Any, edited: Any, *, source_revision: int) -> dict[str, Any]:
    if isinstance(source_revision, bool) or not isinstance(source_revision, int) or source_revision < 0:
        raise ValueError("source_revision must be a non-negative integer")
    baseline = validate_canvas(baseline)
    edited = validate_canvas(edited)
    base_node_order, base_nodes = _index_items(baseline["nodes"], "nodes")
    edited_node_order, edited_nodes = _index_items(edited["nodes"], "nodes")
    base_edge_order, base_edges = _index_items(baseline["edges"], "edges")
    edited_edge_order, edited_edges = _index_items(edited["edges"], "edges")

    intents: list[dict[str, Any]] = []

    for node_id in base_node_order:
        before = base_nodes[node_id]
        after = edited_nodes.get(node_id)
        if after is None:
            intents.append(
                {
                    "id": _intent_id("node_delete_request", node_id),
                    "kind": "node_delete_request",
                    "target_id": node_id,
                    "requires_human_review": True,
                    "destructive_action_performed": False,
                    "before_sha256": _sha256(before),
                }
            )
            continue
        layout_fields = _changed_fields(before, after, PRESENTATION_FIELDS)
        if layout_fields:
            intents.append(
                {
                    "id": _intent_id("layout_change", node_id),
                    "kind": "layout_change",
                    "target_id": node_id,
                    "changed_fields": layout_fields,
                    "before": {field: before.get(field) for field in layout_fields},
                    "after": {field: after.get(field) for field in layout_fields},
                    "requires_human_review": False,
                }
            )
        semantic_fields = _changed_fields(before, after, (set(before) | set(after)) - PRESENTATION_FIELDS)
        if semantic_fields:
            intents.append(
                {
                    "id": _intent_id("semantic_edit_request", node_id),
                    "kind": "semantic_edit_request",
                    "target_id": node_id,
                    "changed_fields": semantic_fields,
                    "before_sha256": _sha256(before),
                    "after_sha256": _sha256(after),
                    "requires_human_review": True,
                }
            )

    for node_id in edited_node_order:
        if node_id not in base_nodes:
            node = edited_nodes[node_id]
            intents.append(
                {
                    "id": _intent_id("node_add_request", node_id),
                    "kind": "node_add_request",
                    "target_id": node_id,
                    "node_type": node.get("type"),
                    "after_sha256": _sha256(node),
                    "requires_human_review": True,
                }
            )

    for edge_id in base_edge_order:
        before = base_edges[edge_id]
        after = edited_edges.get(edge_id)
        if after is None:
            intents.append(
                {
                    "id": _intent_id("relationship_remove_request", edge_id),
                    "kind": "relationship_remove_request",
                    "target_id": edge_id,
                    "requires_human_review": True,
                    "destructive_action_performed": False,
                    "before_sha256": _sha256(before),
                }
            )
        elif before != after:
            intents.append(
                {
                    "id": _intent_id("relationship_edit_request", edge_id),
                    "kind": "relationship_edit_request",
                    "target_id": edge_id,
                    "changed_fields": _changed_fields(before, after),
                    "before_sha256": _sha256(before),
                    "after_sha256": _sha256(after),
                    "requires_human_review": True,
                }
            )

    for edge_id in edited_edge_order:
        if edge_id not in base_edges:
            edge = edited_edges[edge_id]
            intents.append(
                {
                    "id": _intent_id("relationship_add_request", edge_id),
                    "kind": "relationship_add_request",
                    "target_id": edge_id,
                    "from_node": edge["fromNode"],
                    "to_node": edge["toNode"],
                    "label": edge.get("label", ""),
                    "requires_human_review": True,
                }
            )

    return {
        "schema_version": "shared_canvas_change_intents.v1",
        "source_revision": source_revision,
        "baseline_sha256": _sha256(baseline),
        "edited_sha256": _sha256(edited),
        "intent_count": len(intents),
        "intents": intents,
        "apply_performed": False,
        "external_side_effects": False,
        "runtime_effect": "proposal_only",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="projected baseline .canvas")
    parser.add_argument("edited", type=Path, help="human/agent edited .canvas")
    parser.add_argument("output", type=Path, help="change-intent proposal packet")
    parser.add_argument("--source-revision", type=int, required=True)
    args = parser.parse_args(argv)

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    edited = json.loads(args.edited.read_text(encoding="utf-8"))
    packet = classify_changes(baseline, edited, source_revision=args.source_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(_canonical_bytes(packet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
