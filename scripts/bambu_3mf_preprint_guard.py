#!/usr/bin/env python3
"""Pre-print guard for Bambu/X2D 3MF artifacts.

Classifies artifacts into:
- gui_reslice_project: project-only 3MF, safe to open in GUI and slice with live printer/AMS state.
- direct_print_candidate: sliced 3MF, but only printable after live AMS/material/nozzle verification.
- direct_print_ready: sliced 3MF whose metadata matches supplied live status assumptions.
- fail_closed: unsafe/unknown for direct print.

This script never uploads or starts a printer.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SCHEMA = "hermes_bambu_3mf_preprint_guard_v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text(zf: zipfile.ZipFile, name: str) -> str:
    try:
        return zf.read(name).decode("utf-8", "ignore")
    except KeyError:
        return ""


def _xml_metadata_values(xml_text: str) -> dict[str, str]:
    if not xml_text.strip():
        return {}
    out: dict[str, str] = {}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    for elem in root.iter():
        if elem.tag.endswith("metadata"):
            key = elem.attrib.get("key")
            value = elem.attrib.get("value")
            if key is not None and value is not None:
                out[key] = value
    return out


def _slice_filaments(xml_text: str) -> list[dict[str, Any]]:
    if not xml_text.strip():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    filaments: list[dict[str, Any]] = []
    for elem in root.iter("filament"):
        filaments.append(dict(elem.attrib))
    return filaments


def _gcode_config(gcode_head: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in gcode_head.splitlines():
        if not line.startswith("; ") or " = " not in line:
            continue
        key, value = line[2:].split(" = ", 1)
        out[key.strip()] = value.strip()
    return out


def parse_3mf(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.exists():
        return {"path": str(path), "exists": False, "error": "file_missing"}
    if path.suffix.lower() != ".3mf":
        return {"path": str(path), "exists": True, "error": "not_3mf"}

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        gcode_files = sorted(n for n in names if re.fullmatch(r"Metadata/plate_\d+\.gcode", n))
        slice_info = _read_text(zf, "Metadata/slice_info.config")
        project_settings = _read_text(zf, "Metadata/project_settings.config")
        plate_json_raw = _read_text(zf, "Metadata/plate_1.json")
        plate_json: dict[str, Any] = {}
        if plate_json_raw:
            try:
                plate_json = json.loads(plate_json_raw)
            except json.JSONDecodeError:
                plate_json = {"parse_error": True}
        gcode_cfg: dict[str, str] = {}
        if gcode_files:
            gcode_cfg = _gcode_config(_read_text(zf, gcode_files[0])[:200000])

    slice_meta = _xml_metadata_values(slice_info)
    project_cfg: dict[str, Any] = {}
    if project_settings:
        try:
            project_cfg = json.loads(project_settings)
        except json.JSONDecodeError:
            project_cfg = {"parse_error": True}

    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "gcode_files": gcode_files,
        "has_gcode": bool(gcode_files),
        "slice_info": {
            "present": bool(slice_info),
            "has_filament_switcher": slice_meta.get("has_filament_switcher"),
            "enable_filament_dynamic_map": slice_meta.get("enable_filament_dynamic_map"),
            "filament_maps": slice_meta.get("filament_maps"),
            "limit_filament_maps": slice_meta.get("limit_filament_maps"),
            "extruder_type": slice_meta.get("extruder_type"),
            "nozzle_diameters": slice_meta.get("nozzle_diameters"),
            "support_used": slice_meta.get("support_used"),
            "filaments": _slice_filaments(slice_info),
        },
        "plate": {
            "bed_type": plate_json.get("bed_type"),
            "nozzle_diameter": plate_json.get("nozzle_diameter"),
            "filament_colors": plate_json.get("filament_colors"),
            "filament_ids": plate_json.get("filament_ids"),
        },
        "project_settings": {
            "curr_bed_type": project_cfg.get("curr_bed_type"),
            "default_filament_profile": project_cfg.get("default_filament_profile"),
            "filament_type": project_cfg.get("filament_type"),
            "filament_colour": project_cfg.get("filament_colour"),
        },
        "gcode_config": {
            "curr_bed_type": gcode_cfg.get("curr_bed_type"),
            "default_filament_profile": gcode_cfg.get("default_filament_profile"),
            "filament_type": gcode_cfg.get("filament_type"),
            "filament_colour": gcode_cfg.get("filament_colour"),
            "default_nozzle_volume_type": gcode_cfg.get("default_nozzle_volume_type"),
        },
    }


def _norm_color(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().upper().lstrip("#")
    if len(value) == 6:
        value += "FF"
    return value


def _loaded_trays(status: dict[str, Any]) -> list[dict[str, Any]]:
    trays = status.get("ams", {}).get("trays")
    return trays if isinstance(trays, list) else []


def _material_matches(requested: str | None, tray: dict[str, Any]) -> bool:
    if not requested:
        return True
    req = requested.strip().upper()
    tray_type = str(tray.get("type", "")).strip().upper()
    sub = str(tray.get("sub_brand", "")).strip().upper()
    return req == tray_type or req in sub or tray_type in req


def decide(meta: dict[str, Any], live_status: dict[str, Any] | None, requested_material: str | None, requested_color: str | None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    artifact_type = "sliced_package" if meta.get("has_gcode") else "gui_reslice_project"

    if meta.get("error"):
        return {"status": "fail_closed", "artifact_type": artifact_type, "direct_print_allowed": False, "issues": [{"id": meta["error"], "severity": "blocker"}], "next_gate": "provide a valid 3MF"}

    if not meta.get("has_gcode"):
        return {
            "status": "gui_reslice_project",
            "artifact_type": artifact_type,
            "direct_print_allowed": False,
            "issues": [],
            "next_gate": "Open in Bambu Studio, map live printer/AMS material, click Slice, then print after warning-free preview.",
            "safe_claim": "not_click_print_ready_until_gui_resliced",
        }

    if not meta.get("slice_info", {}).get("present"):
        issues.append({"id": "missing_slice_info", "severity": "blocker"})

    if live_status is None:
        issues.append({"id": "live_ams_status_not_verified", "severity": "blocker"})
        return {
            "status": "requires_live_ams_verification",
            "artifact_type": artifact_type,
            "direct_print_allowed": False,
            "issues": issues,
            "next_gate": "Fetch fresh X2D status and compare AMS/material/nozzle/plate before claiming direct print readiness; otherwise export GUI-reslice project.",
            "safe_claim": "do_not_claim_click_print_ready",
        }

    trays = _loaded_trays(live_status)
    if not trays:
        issues.append({"id": "live_status_has_no_ams_trays", "severity": "blocker"})

    if requested_material and not any(_material_matches(requested_material, t) for t in trays):
        issues.append({"id": "requested_material_not_loaded", "severity": "blocker"})

    req_color = _norm_color(requested_color)
    if req_color and not any(_norm_color(str(t.get("color", ""))) == req_color for t in trays):
        issues.append({"id": "requested_color_not_loaded", "severity": "warn"})

    filaments = meta.get("slice_info", {}).get("filaments") or []
    used_filaments = [f for f in filaments if f.get("used_for_object", "true") != "false"]
    used_types = {str(f.get("type", "")).upper() for f in used_filaments if f.get("type")}
    for ftype in used_types:
        if ftype and not any(_material_matches(ftype, t) for t in trays):
            issues.append({"id": f"sliced_filament_type_not_loaded:{ftype}", "severity": "blocker"})

    # For direct dispatch, requested material/color must match both live AMS and
    # the already-sliced G-code metadata. A sliced artifact with stale green/Basic
    # metadata can otherwise pass merely because some PLA is loaded.
    if req_color:
        sliced_colors = {_norm_color(str(f.get("color", ""))) for f in used_filaments if f.get("color")}
        sliced_colors.update(_norm_color(c) for c in (meta.get("plate", {}).get("filament_colors") or []) if c)
        sliced_colors.discard(None)
        if sliced_colors and req_color not in sliced_colors:
            issues.append({"id": "sliced_color_mismatch_requested_color", "severity": "blocker"})

    if requested_material:
        profile_values = [
            str(meta.get("gcode_config", {}).get("default_filament_profile") or ""),
            str(meta.get("project_settings", {}).get("default_filament_profile") or ""),
        ]
        profile_joined = " ".join(profile_values).strip().upper()
        # PLA vs PLA Matte: if the user requested a specific sub-brand and the
        # sliced profile names a different sub-brand/basic profile, block direct dispatch.
        req = requested_material.strip().upper()
        if "MATTE" in req and profile_joined and "MATTE" not in profile_joined:
            issues.append({"id": "sliced_filament_profile_not_requested_subbrand", "severity": "blocker"})

    status = "direct_print_ready" if not any(i["severity"] == "blocker" for i in issues) else "fail_closed"
    return {
        "status": status,
        "artifact_type": artifact_type,
        "direct_print_allowed": status == "direct_print_ready",
        "issues": issues,
        "next_gate": "external-control action packet + fresh telemetry + human confirmation" if status == "direct_print_ready" else "re-slice in GUI with live printer/AMS mapping or fix mismatches",
        "safe_claim": "click_print_ready_only_after_warning_free_gui_send_screen" if status == "direct_print_ready" else "do_not_claim_click_print_ready",
    }


def run(path: Path, status_path: Path | None, requested_material: str | None, requested_color: str | None) -> dict[str, Any]:
    live_status = None
    if status_path:
        live_status = json.loads(status_path.expanduser().read_text(encoding="utf-8"))
    meta = parse_3mf(path)
    decision = decide(meta, live_status, requested_material, requested_color)
    return {
        "schema": SCHEMA,
        "generated_at": now(),
        "artifact": meta,
        "decision": decision,
        "physical_actions": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify Bambu 3MF direct-print readiness against live AMS/material assumptions")
    parser.add_argument("three_mf")
    parser.add_argument("--status-json", help="Fresh X2D status/summary JSON with ams.trays")
    parser.add_argument("--requested-material")
    parser.add_argument("--requested-color", help="Hex color, e.g. FFFFFFFF for white")
    parser.add_argument("--output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    obj = run(
        Path(args.three_mf),
        Path(args.status_json) if args.status_json else None,
        args.requested_material,
        args.requested_color,
    )
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(obj, ensure_ascii=False, indent=2 if args.json else None, sort_keys=True))
    return 0 if obj["decision"]["status"] in {"gui_reslice_project", "direct_print_ready", "requires_live_ams_verification"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
