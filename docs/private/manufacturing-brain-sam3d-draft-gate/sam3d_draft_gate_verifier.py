#!/usr/bin/env python3
"""Local-only verifier for SAM3D / photo-to-3D candidate manifests.

This is a draft evidence harness, not an active Hermes skill or production gate.
It encodes the existing draft-gate reference into deterministic checks so future
mission/taskpool reviews can distinguish preview evidence from printable assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_ENUMS = {
    "consent_scope": {"private", "public_sample", "user_approved"},
    "output_format": {"ply", "glb", "gltf", "obj", "stl", "3mf", "other"},
    "license_status": {"unknown", "known", "incompatible"},
    "provenance_status": {"unknown", "verified_source", "generated_local", "cloud_output"},
    "unit_scale_assumption": {"unknown", "explicit"},
    "visual_fidelity_class": {
        "exact_replacement",
        "functional_part",
        "decorative_equivalent",
        "inspiration_only",
        "failed",
        "unknown",
    },
    "mesh_validity": {"unknown", "valid", "needs_repair", "invalid"},
    "printability_state": {"draft_only", "studio_preview", "candidate_model", "model_ready", "blocked"},
    "human_approval": {"pending", "approved", "rejected"},
}

REQUIRED_FIELDS = [
    "source_photo_path",
    "source_photo_sha256",
    "consent_scope",
    "provider_or_repo",
    "model_name_or_checkpoint",
    "wrapper_or_workflow",
    "output_format",
    "local_output_path",
    "output_sha256",
    "license_status",
    "provenance_status",
    "unit_scale_assumption",
    "bounding_box_mm",
    "preview_path",
    "visual_fidelity_class",
    "mesh_validity",
    "printability_state",
    "human_approval",
]

PREVIEW_FORMATS = {"ply", "glb", "gltf", "obj", "other"}
PRINTABLE_FORMATS = {"stl", "3mf"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "photo_to_3d_candidate" in data:
        data = data["photo_to_3d_candidate"]
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object or contain photo_to_3d_candidate object")
    return data


def verify(candidate: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in candidate:
            errors.append(f"missing:{field}")

    for field, allowed in ALLOWED_ENUMS.items():
        value = candidate.get(field)
        if value not in allowed:
            errors.append(f"enum:{field}:{value!r}")

    fmt = candidate.get("output_format")
    state = candidate.get("printability_state")
    consent = candidate.get("consent_scope")
    license_status = candidate.get("license_status")
    provenance = candidate.get("provenance_status")
    scale = candidate.get("unit_scale_assumption")
    bbox = candidate.get("bounding_box_mm")
    preview = candidate.get("preview_path")
    fidelity = candidate.get("visual_fidelity_class")
    mesh = candidate.get("mesh_validity")
    approval = candidate.get("human_approval")

    if fmt in PREVIEW_FORMATS and state in {"candidate_model", "model_ready"}:
        errors.append("preview_format_cannot_claim_printable_state")
    if fmt in {"ply", "other"} and state != "draft_only":
        warnings.append("ply_or_other_should_remain_draft_only_until_mesh_conversion_and_qa")
    if consent == "private" and approval != "approved":
        errors.append("private_source_requires_human_approval_before_advancing")
    if license_status in {"unknown", "incompatible"} and state in {"candidate_model", "model_ready"}:
        errors.append("license_must_be_known_before_candidate_or_model_ready")
    if provenance == "unknown" and state in {"candidate_model", "model_ready"}:
        errors.append("provenance_must_be_verified_before_candidate_or_model_ready")
    if state == "model_ready":
        if fmt not in PRINTABLE_FORMATS:
            errors.append("model_ready_requires_stl_or_3mf")
        if scale != "explicit":
            errors.append("model_ready_requires_explicit_units")
        if not isinstance(bbox, dict) or not all(k in bbox for k in ("x", "y", "z", "unit")):
            errors.append("model_ready_requires_bounding_box_xyz_unit")
        if not preview:
            errors.append("model_ready_requires_preview_path")
        if fidelity not in {"exact_replacement", "functional_part", "decorative_equivalent"}:
            errors.append("model_ready_requires_acceptable_visual_fidelity")
        if mesh != "valid":
            errors.append("model_ready_requires_valid_mesh")
        if approval != "approved":
            errors.append("model_ready_requires_human_approval")

    # Retrieval-before-generation and slicer/external-control are process gates.
    # This verifier records them as out-of-scope warnings unless explicit manifest
    # extensions are later approved.
    if candidate.get("retrieval_before_generation") is not True:
        warnings.append("retrieval_before_generation_not_proven_by_manifest")
    if state == "model_ready" and candidate.get("slicer_preview_path") is None:
        errors.append("model_ready_requires_slicer_preview_path")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "checked_fields": len(REQUIRED_FIELDS),
        "manifest_sha256": sha256_text(json.dumps(candidate, ensure_ascii=False, sort_keys=True)),
        "policy": "draft_only verifier; no generation/install/cloud/deploy/external-send side effects",
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--expect", choices=["PASS", "FAIL"])
    args = parser.parse_args(argv)
    result = verify(load_manifest(args.manifest))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if args.expect and result["status"] != args.expect:
        return 2
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
