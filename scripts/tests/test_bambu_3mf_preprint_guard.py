#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def write_3mf(path: Path, *, gcode: bool) -> None:
    slice_info = '''<?xml version="1.0" encoding="UTF-8"?>
<config><plate>
  <metadata key="has_filament_switcher" value="false"/>
  <metadata key="nozzle_diameters" value="0.4,0.4"/>
  <metadata key="support_used" value="false"/>
  <filament id="1" type="PLA" color="#FFFFFFFF" used_m="1.0" used_g="3.0" used_for_object="true" nozzle_diameter="0.40"/>
</plate></config>'''
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml", "")
        zf.writestr("Metadata/slice_info.config", slice_info)
        zf.writestr("Metadata/plate_1.json", json.dumps({"bed_type": "textured_plate", "nozzle_diameter": 0.4, "filament_colors": ["#FFFFFFFF"], "filament_ids": [0]}))
        if gcode:
            zf.writestr("Metadata/plate_1.gcode", "; CONFIG_BLOCK_START\n; filament_type = PLA\n; filament_colour = #FFFFFFFF\n; curr_bed_type = Textured PEI Plate\n")


def test_project_only_3mf_is_gui_reslice_not_direct_print() -> None:
    import bambu_3mf_preprint_guard as guard

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "project.3mf"
        write_3mf(p, gcode=False)
        obj = guard.run(p, None, "PLA Matte", "FFFFFFFF")
        assert obj["decision"]["status"] == "gui_reslice_project"
        assert obj["decision"]["direct_print_allowed"] is False
        assert obj["decision"]["safe_claim"] == "not_click_print_ready_until_gui_resliced"


def test_sliced_3mf_without_live_ams_blocks_click_print_claim() -> None:
    import bambu_3mf_preprint_guard as guard

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sliced.3mf"
        write_3mf(p, gcode=True)
        obj = guard.run(p, None, "PLA Matte", "FFFFFFFF")
        assert obj["decision"]["status"] == "requires_live_ams_verification"
        assert obj["decision"]["direct_print_allowed"] is False
        assert any(i["id"] == "live_ams_status_not_verified" for i in obj["decision"]["issues"])


def test_sliced_3mf_with_matching_live_ams_can_pass_to_external_control() -> None:
    import bambu_3mf_preprint_guard as guard

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sliced.3mf"
        s = Path(td) / "status.json"
        write_3mf(p, gcode=True)
        s.write_text(json.dumps({"ams": {"trays": [{"id": "2", "type": "PLA", "sub_brand": "PLA Matte", "color": "FFFFFFFF"}]}}), encoding="utf-8")
        obj = guard.run(p, s, "PLA Matte", "FFFFFFFF")
        assert obj["decision"]["status"] == "direct_print_ready"
        assert obj["decision"]["direct_print_allowed"] is True
        assert "external-control" in obj["decision"]["next_gate"]
