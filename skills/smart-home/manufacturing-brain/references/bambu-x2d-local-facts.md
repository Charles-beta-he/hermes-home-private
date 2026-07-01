# Bambu X2D Local Facts

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Bambu X2D local facts

Current local adapter profile lives at:
`~/.hermes/brains/manufacturing/devices/bambu-x2d.yaml`

Current safe status CLI:
`BAMBU_ACCESS_CODE=... python3 ~/.hermes/scripts/bambu_x2d.py status`

Upload + start (mutating, requires external-control gate approval):
```bash
- BambuStudio dispatch is not just raw FTP + MQTT: it first exports a valid sliced print file (`send_gcode`), validates AMS/nozzle mapping, then calls `bambu_network_start_local_print_with_record` or cloud fallback via the official networking module.
- For newer/eMMC-capable machines, BambuStudio checks a port-6000 `FileTransferTunnel` URL shaped like `bambu:///local/<ip>?port=6000&user=bblp&passwd=<code>` before/alongside legacy FTP/SD-card upload. Prefer this route for X2D/H2D automation instead of assuming writable FTPS.
- Legacy LAN FTP upload may fail even with correct access code: `553 Could not create file` means the printer/storage refused local FTP writes. Treat as fail-closed and switch to official network module / eMMC tunnel / BambuStudio automation.
- `BAMBU_ACCESS_CODE=... python3 ~/.hermes/scripts/bambu_x2d.py start --remote name.3mf` sends MQTT `project_file` with URL `file:///sdcard/cache/name.3mf` and param `Metadata/plate_1.gcode`, but only after a verified upload of a sliced package.
- Before start, verify the 3MF is sliced and contains `Metadata/plate_1.gcode`; a project-only 3MF is not directly printable. AMS/nozzle mapping, then calls `bambu_network_start_local_print_with_record` or cloud fallback via the official networking module.
- For newer/eMMC-capable machines, BambuStudio checks a port-6000 `FileTransferTunnel` URL shaped like `bambu:///local/<ip>?port=6000&user=bblp&passwd=<code>` before/alongside legacy FTP/SD-card upload. Prefer this route for X2D/H2D automation instead of assuming writable FTPS.
- Legacy LAN FTP upload may fail even with correct access code: `553 Could not create file` means the printer/storage refused local FTP writes. Treat as fail-closed and switch to official network module / eMMC tunnel / BambuStudio automation.
- `BAMBU_ACCESS_CODE=... python3 ~/.hermes/scripts/bambu_x2d.py start --remote name.3mf` sends MQTT `project_file` with URL `file:///sdcard/cache/name.3mf` and param `Metadata/plate_1.gcode`, but only after a verified upload of a sliced package.
- Before start, verify the 3MF is sliced and contains `Metadata/plate_1.gcode`; a project-only 3MF is not directly printable.
```

Do not persist the access code in plaintext. For glasses/agent automation, store it once in macOS Keychain:
```bash
python3 ~/.hermes/scripts/bambu_credentials.py set
python3 ~/.hermes/scripts/bambu_credentials.py status
```
Adapters prefer `BAMBU_ACCESS_CODE` env for one-off overrides, then Keychain `hermes-bambu-x2d/lan-access-code` for unattended automation.
