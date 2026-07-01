# BambuStudio CLI Support-Slice Pitfall

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## BambuStudio CLI support-slice pitfall

When fixing `floating regions` by enabling support from CLI, a minimal process JSON can fail with `process not compatible with printer`. Load the X2D machine profile together with the custom process profile:

```bash
'/Applications/BambuStudio.app/Contents/MacOS/BambuStudio' \
  model_a.stl model_b.stl \
  --load-settings '/Users/charles/Library/Application Support/BambuStudio/system/BBL/machine/Bambu Lab X2D 0.4 nozzle.json;/path/support_tree_x2d_process.json' \
  --orient 1 --arrange 1 --slice 0 --export-3mf output-name.3mf --outputdir /path/out
```

Prefer the persisted helper instead of hand-building commands:

```bash
python3 ~/.hermes/scripts/bambu_studio_slice.py slice \
  /path/base.stl /path/lid.stl \
  --output /path/out/job.3mf \
  --machine-json '/Users/charles/Library/Application Support/BambuStudio/system/BBL/machine/Bambu Lab X2D 0.4 nozzle.json' \
  --process-json /path/tree-support-process.json \
  --json
```

BambuStudio CLI quirks verified on the smoke-box run:
- pass a **basename** to `--export-3mf` and an absolute `--outputdir`; absolute `--export-3mf` can create doubled output paths,
- do not combine `--export-png` and `--export-3mf` in one CLI invocation,
- use explicit machine/process/filament JSON file paths for automation; do **not** mutate `system/BBL.json` or `ota/presets/BBL.json` just to make a custom GUI dropdown preset appear,
- GUI lane should load original STL files and stock presets; CLI-exported projects/sliced packages are send artifacts, not reliable GUI-edit artifacts.

For BambuStudio CLI, trust `result.json` (`return_code: 0`, `warning_message: ""`, support feature times present) over scary but non-fatal stderr lines like `update_values_to_printer_extruders... could not found extruder_type Bowden` when valid G-code/3MF artifacts are produced. Multi-plate jobs must not be started by a hardcoded `Metadata/plate_1.gcode` path unless intentionally printing only plate 1.

Pre-print guard pitfall: a CLI-sliced 3MF that contains `Metadata/plate_1.gcode` is not automatically “ready to click print”. Bambu Studio / Handy may warn “打印机上安装的耗材变轨器与切片文件不匹配” when the embedded sliced package has stale/incorrect AMS, filament switcher, color/profile, nozzle, or plate assumptions (field case: `slice_info.config` had `has_filament_switcher=false` and mismatched filament color/profile against live X2D AMS). Before saying “只需要点击打印”, run:

```bash
python3 ~/.hermes/scripts/bambu_3mf_preprint_guard.py /path/job.3mf \
  --status-json /path/fresh-x2d-status-or-summary.json \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --json
```

Decision policy:
- `direct_print_ready`: still requires external-control action packet + fresh telemetry + human confirmation before upload/start.
- `requires_live_ams_verification` / `fail_closed`: do not claim click-print readiness; fetch fresh X2D status or export a GUI-reslice project.
- `gui_reslice_project`: safe to open in Bambu Studio, but not directly printable until the user maps current AMS/material, clicks Slice, and confirms a warning-free send screen.

Use `bambu_studio_slice.py --artifact-mode gui-reslice-project` to produce a GUI recovery file without embedded stale G-code. Use `--artifact-mode sliced` only for direct-print candidates, and only after the guard confirms material/AMS/nozzle/plate compatibility.

Audited local dispatch helper:
```bash
python3 ~/.hermes/scripts/x2d_dispatch_print.py /path/sliced.3mf \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --dry-run
python3 ~/.hermes/scripts/x2d_dispatch_print.py /path/sliced.3mf \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --yes-start
```
This wrapper reads the Bambu access code from env/Keychain, fetches fresh status, refuses project-only/stale-G-code artifacts, records an external-control dry-run packet, then executes the official Bambu local print helper only after a typed token.

Glasses/taskpool intent worker:
```bash
python3 ~/.hermes/scripts/x2d_print_intent_worker.py \
  --three-mf /path/sliced.3mf \
  --source rokid \
  --autonomy auto \
  --risk-tier P0 \
  --allow-autostart
```
The worker classifies P0/P1/P2, performs dispatch dry-run first, and autostarts only for P0 trusted repeat/calibration/test jobs after all external-control gates pass. See `~/.hermes/brains/manufacturing/protocols/x2d-glasses-autoprint-pipeline.md`.

GUI pitfall: BambuStudio CLI-exported project 3MFs can be unsuitable for GUI reopening if the custom process JSON contains `compatible_printers`; BambuStudio may write invalid XML like `value=""Bambu Lab X2D 0.4 nozzle""`, causing GUI warnings such as “此文件不包含任何几何数据” or CLI errors like “Archive does not contain a valid model config”. `bambu_studio_slice.py` now auto-repairs this narrow defect for `--artifact-mode gui-reslice-project` by removing malformed `Metadata/model_settings.config` compatible-printers metadata; verify XML and vertex/triangle counts before opening. If repaired project still fails, open the original STL files and re-apply settings inside GUI.
