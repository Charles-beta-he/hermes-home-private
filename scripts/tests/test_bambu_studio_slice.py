#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def test_bambu_studio_export_3mf_uses_basename_and_outputdir() -> None:
    import bambu_studio_slice

    out_dir = Path('/tmp/hermes slice out')
    out_path = out_dir / 'smoke-box-v3.3mf'
    cmd = bambu_studio_slice.build_slice_command(
        slicer='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio',
        models=[Path('/tmp/base.stl'), Path('/tmp/lid.stl')],
        output_3mf=out_path,
        machine_json=Path('/tmp/machine.json'),
        process_json=Path('/tmp/process.json'),
        filament_json=Path('/tmp/filament.json'),
    )
    assert '--export-3mf' in cmd
    export_arg = cmd[cmd.index('--export-3mf') + 1]
    assert export_arg == 'smoke-box-v3.3mf'
    outputdir_arg = cmd[cmd.index('--outputdir') + 1]
    assert Path(outputdir_arg) == out_dir.resolve()
    assert str(out_path) not in cmd


def test_bambu_studio_gui_reslice_project_mode_omits_slice_flag() -> None:
    import bambu_studio_slice

    cmd = bambu_studio_slice.build_slice_command(
        slicer='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio',
        models=[Path('/tmp/base.stl')],
        output_3mf=Path('/tmp/project.3mf'),
        machine_json=Path('/tmp/machine.json'),
        process_json=Path('/tmp/process.json'),
        filament_json=Path('/tmp/filament.json'),
        slice_plate=False,
    )
    assert '--export-3mf' in cmd
    assert '--slice' not in cmd


def test_bambu_studio_command_refuses_export_png_and_3mf_together() -> None:
    import bambu_studio_slice

    try:
        bambu_studio_slice.build_slice_command(
            slicer='BambuStudio',
            models=[Path('/tmp/base.stl')],
            output_3mf=Path('/tmp/out.3mf'),
            output_png=Path('/tmp/out.png'),
            machine_json=Path('/tmp/machine.json'),
            process_json=Path('/tmp/process.json'),
            filament_json=Path('/tmp/filament.json'),
        )
    except ValueError as exc:
        assert 'export-png' in str(exc) and 'export-3mf' in str(exc)
    else:
        raise AssertionError('expected ValueError for combined export-png/export-3mf')
