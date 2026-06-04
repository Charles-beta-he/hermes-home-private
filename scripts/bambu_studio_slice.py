#!/usr/bin/env python3
"""Bambu Studio CLI slicing helper for Hermes manufacturing workflows.

This captures field-tested BambuStudio CLI quirks:
- Pass explicit machine/process/filament JSON files instead of editing GUI/vendor preset indexes.
- Use basename for --export-3mf plus absolute --outputdir; absolute --export-3mf can create doubled paths.
- Do not combine --export-png and --export-3mf in one invocation.
- Produces slicer/send artifacts only; no upload/start/physical action.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

SECRET_KEYS = ["BAMBU_ACCESS_CODE", "ACCESS_CODE", "LAN_ACCESS_CODE"]
SCHEMA = "hermes_bambu_studio_slice_v1"
BAMBU_STUDIO_CANDIDATES = [
    os.environ.get("BAMBU_STUDIO"),
    "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
    shutil.which("bambu-studio"),
    shutil.which("BambuStudio"),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_bambu_studio() -> str | None:
    for candidate in BAMBU_STUDIO_CANDIDATES:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def write_json(path: Path, obj: dict[str, Any]) -> None:
    raw = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
    for key in SECRET_KEYS:
        val = os.environ.get(key)
        if val and val in raw:
            raise RuntimeError(f"refusing to persist secret from env:{key}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw + "\n", encoding="utf-8")


def build_slice_command(
    *,
    slicer: str,
    models: Sequence[Path],
    output_3mf: Path | None,
    machine_json: Path,
    process_json: Path,
    filament_json: Path | None = None,
    output_png: Path | None = None,
    arrange: bool = True,
    orient: bool = True,
    slice_plate: bool = True,
) -> list[str]:
    """Build a safe BambuStudio CLI command without vendor preset mutation."""
    if output_3mf and output_png:
        raise ValueError("BambuStudio CLI export-png and export-3mf must run in separate invocations")
    if not models:
        raise ValueError("at least one model is required")
    if not output_3mf and not output_png:
        raise ValueError("one output artifact is required")

    cmd = [slicer, *[str(Path(m)) for m in models]]
    cmd += ["--load-settings", f"{machine_json};{process_json}"]
    if filament_json:
        cmd += ["--load-filaments", str(filament_json)]
    if orient:
        cmd += ["--orient", "1"]
    if arrange:
        cmd += ["--arrange", "1"]
    if slice_plate:
        cmd += ["--slice", "0"]

    if output_3mf:
        out = Path(output_3mf).expanduser().resolve()
        cmd += ["--export-3mf", out.name, "--outputdir", str(out.parent)]
    else:
        out = Path(output_png).expanduser().resolve()  # type: ignore[arg-type]
        cmd += ["--export-png", out.name, "--outputdir", str(out.parent)]
    return cmd


def repair_bambu_gui_project_xml(path: Path) -> list[str]:
    """Repair known BambuStudio CLI project XML defects in-place.

    Field case: custom process JSON with compatible_printers can be serialized
    into Metadata/model_settings.config as value=""Bambu Lab X2D 0.4 nozzle"",
    which is invalid XML. Bambu Studio may then warn "file contains no geometry"
    even though 3D/Objects/object_*.model contains vertices/triangles.
    """
    path = path.expanduser().resolve()
    if not path.exists() or path.suffix.lower() != ".3mf":
        return []
    patched: list[str] = []
    with zipfile.ZipFile(path, "r") as zin:
        entries = [(info, zin.read(info.filename)) for info in zin.infolist()]
    tmp = path.with_suffix(path.suffix + ".repairing")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in entries:
            if info.filename == "Metadata/model_settings.config":
                text = data.decode("utf-8", "ignore")
                before = text
                # Remove malformed CLI-emitted compatible_printers metadata. GUI
                # can infer compatibility from machine/settings; invalid XML is worse.
                text = re.sub(r'\n\s*<metadata key="compatible_printers" value=""[^"]+""/>', "", text)
                text = re.sub(r'value=""([^"]+)""', r'value="\1"', text)
                if text != before:
                    data = text.encode("utf-8")
                    patched.append(info.filename)
            zout.writestr(info, data)
    if patched:
        tmp.replace(path)
    else:
        tmp.unlink(missing_ok=True)
    return patched


def run_slice(
    *,
    models: Sequence[Path],
    output_3mf: Path,
    machine_json: Path,
    process_json: Path,
    filament_json: Path | None,
    report: Path | None,
    timeout: int,
    slicer: str | None = None,
    artifact_mode: str = "sliced",
) -> tuple[int, dict[str, Any]]:
    resolved_slicer = slicer or find_bambu_studio()
    if not resolved_slicer:
        obj = {"schema": SCHEMA, "generated_at": now(), "status": "fail_closed", "reason": "BambuStudio CLI not found", "physical_actions": []}
        if report:
            write_json(report, obj)
        return 2, obj

    missing = [str(p) for p in [*models, machine_json, process_json, *( [filament_json] if filament_json else [] )] if p and not Path(p).exists()]
    if missing:
        obj = {"schema": SCHEMA, "generated_at": now(), "status": "fail_closed", "reason": "required input missing", "missing": missing, "physical_actions": []}
        if report:
            write_json(report, obj)
        return 2, obj

    if artifact_mode not in {"sliced", "gui-reslice-project"}:
        obj = {"schema": SCHEMA, "generated_at": now(), "status": "fail_closed", "reason": "invalid artifact_mode", "artifact_mode": artifact_mode, "physical_actions": []}
        if report:
            write_json(report, obj)
        return 2, obj

    output_3mf = output_3mf.expanduser().resolve()
    output_3mf.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_slice_command(
        slicer=resolved_slicer,
        models=[Path(m).expanduser().resolve() for m in models],
        output_3mf=output_3mf,
        machine_json=machine_json.expanduser().resolve(),
        process_json=process_json.expanduser().resolve(),
        filament_json=filament_json.expanduser().resolve() if filament_json else None,
        slice_plate=artifact_mode == "sliced",
    )
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    ready = proc.returncode == 0 and output_3mf.exists() and output_3mf.stat().st_size > 0
    repaired_files: list[str] = []
    if ready and artifact_mode == "gui-reslice-project":
        repaired_files = repair_bambu_gui_project_xml(output_3mf)
    preprint_guard: dict[str, Any] | None = None
    if ready:
        from bambu_3mf_preprint_guard import decide, parse_3mf

        # CLI-sliced 3MFs are not automatically "click print" ready. They must
        # be checked against fresh printer/AMS state. Without live status, the
        # guard intentionally blocks direct-print claims and recommends GUI
        # re-slice or external-control verification.
        meta = parse_3mf(output_3mf)
        preprint_guard = decide(meta, live_status=None, requested_material=None, requested_color=None)
    obj = {
        "schema": SCHEMA,
        "generated_at": now(),
        "status": "ready" if ready else "fail_closed",
        "artifact_mode": artifact_mode,
        "models": [str(Path(m).expanduser().resolve()) for m in models],
        "slice": {"path": str(output_3mf), "exists": output_3mf.exists(), "size_bytes": output_3mf.stat().st_size if output_3mf.exists() else 0},
        "slicer": {
            "path": resolved_slicer,
            "argv_sanitized": [resolved_slicer, "<models...>", "--load-settings", "<machine_json>;<process_json>", *( ["--slice", "0"] if artifact_mode == "sliced" else [] ), "--export-3mf", output_3mf.name, "--outputdir", str(output_3mf.parent)],
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
        },
        "physical_actions": [],
        "repaired_files": repaired_files,
        "preprint_guard": preprint_guard,
        "next_gate": (
            preprint_guard.get("next_gate")
            if preprint_guard
            else "fix slicing failure before approval"
        ),
    }
    if report:
        write_json(report, obj)
    return (0 if ready else 2), obj


def cmd_slice(args: argparse.Namespace) -> int:
    code, obj = run_slice(
        models=[Path(x) for x in args.model],
        output_3mf=Path(args.output),
        machine_json=Path(args.machine_json),
        process_json=Path(args.process_json),
        filament_json=Path(args.filament_json) if args.filament_json else None,
        report=Path(args.report) if args.report else None,
        timeout=args.timeout,
        slicer=args.slicer,
        artifact_mode=args.artifact_mode,
    )
    print(json.dumps(obj, ensure_ascii=False, indent=2 if args.json else None))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="BambuStudio CLI safe slice helper; never uploads/starts printer")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("slice")
    p.add_argument("model", nargs="+", help="STL/3MF model path(s)")
    p.add_argument("--output", required=True, help="Output 3MF path")
    p.add_argument("--machine-json", required=True)
    p.add_argument("--process-json", required=True)
    p.add_argument("--filament-json")
    p.add_argument("--report")
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--slicer")
    p.add_argument("--artifact-mode", choices=["sliced", "gui-reslice-project"], default="sliced", help="sliced includes G-code and still needs live AMS guard; gui-reslice-project omits G-code for Bambu Studio re-slicing")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_slice)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
