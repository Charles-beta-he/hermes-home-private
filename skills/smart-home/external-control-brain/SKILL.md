---
name: external-control-brain
description: Use when handling IoT/local devices or any Hermes action that can affect the physical world, including device adapters, transport, credentials, command confirmation, idempotency, audit logs, and fail-closed safety gates.
---

# External Control Brain

## Overview

Use when handling IoT/local devices or any Hermes action that can affect the physical world, including device adapters, transport, credentials, command confirmation, idempotency, audit logs, and fail-closed safety gates. It is organized as a capability wrapper with explicit safety, idempotency, credential, and read-back checks before any side effect is treated as complete.

## When to Use

Use this skill when the request matches the `external-control-brain` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

This is the physical-world actuation authority for Hermes.

Use this skill when the user asks to:
- control a printer, camera, light, appliance, lock, sensor, robot, or other physical device,
- connect to local network device protocols (MQTT/FTPS/RTSP/HTTP/BLE/Zigbee/Matter),
- execute pause/resume/stop/start/upload/heat/move commands,
- design safety gates for physical actuation.

## Non-negotiables

- Default mode is read-only.
- Fail closed if device identity, telemetry freshness, credentials, audit sink, or command scope are uncertain.
- Secrets never go into brain files, skill files, plans, logs, or git.
- Domain brains can recommend actions but cannot execute them directly.

## Required packet before non-readonly action

```yaml
external_control_action:
  schema: hermes_external_control_action_v1
  device_id: ...
  adapter: ...
  intent: start_print|pause|resume|stop|upload_file|set_temperature|move_or_home
  job_id: ...
  current_telemetry:
    timestamp: ...
    fresh: true|false
  command_preview: ...
  risk: low|medium|high|emergency
  confirmation_required: true|false
  confirmation_token: ...
  idempotency_key: ...
  audit_path: ...
```

For photo-to-print, Manufacturing may generate this packet via `python3 ~/.hermes/scripts/photo_to_print_job.py action-request ...`, but external-control must still validate and confirm before any physical command.

Baseline dry-run gate:

```bash
python3 ~/.hermes/scripts/external_control_gate.py execute /path/action.json --confirm-token TOKEN --dry-run --json
```

The gate additionally validates telemetry age <=5s, start_print idle/no-HMS state, optional device/material/nozzle/plate/AMS assumptions, packet-bound confirmation hashes, idempotency key, and audit path.

The baseline gate validates packet schema, device id, supported intent, fresh telemetry, confirmation token, idempotency key, and audit path. It writes dry-run audit evidence and refuses real execution until a deliberately audited executor is added.

## Virtual desktop / computer-use boundary

Treat GUI computer-use agents as external-control surfaces when they can click, type, download, write files, install apps, or log into accounts. Default to read-only screenshot/cursor/status probes. Mutating GUI actions require scoped target desktop identity, action allowlist, retention/redaction policy for screenshots, idempotency/audit, and a fail-closed `needs_help`/review path instead of silent success.

Reference: `references/bytebot-computer-use-safety.md` captures Bytebot-style containerized desktop safety gates, including default unauthenticated local ports, privileged-container caution, takeover screenshot/action trace risks, and staged read-only-to-mutating adoption.

## Bambu/X2D boundary

Manufacturing brain owns print semantics and recommendations.
External-control owns:
- MQTT TLS connection and publish,
- FTPS upload/delete,
- RTSPS/camera privacy gate,
- pause/resume/stop/start execution,
- credential source and audit.

## Safe default commands

Read-only status/watch may run with runtime credential source:

`BAMBU_ACCESS_CODE=... python3 ~/.hermes/scripts/bambu_x2d.py status`

## Mutating commands (upload + start_print)

The full print-from-file pipeline:

1. Generate action packet with `current_telemetry.timestamp` set to NOW
2. Call `external_control_gate.py execute --dry-run` **in the same invocation** (see telemetry pitfall)
3. After dry-run passes: FTPS upload then MQTT start_print

```bash
# Preferred audited X2D dispatch wrapper (connects, fetches fresh status, runs preprint guard,
# records external-control dry-run, then only starts after a typed token):
python3 ~/.hermes/scripts/x2d_dispatch_print.py /path/sliced.3mf \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --dry-run
python3 ~/.hermes/scripts/x2d_dispatch_print.py /path/sliced.3mf \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --yes-start

# Lower-level atomic gate only, if an action packet already exists:
python3 ~/.hermes/scripts/external_control_gate.py execute \
  /path/action-packet.json \
  --confirm-token TOKEN --dry-run --json

# Legacy fallback (after dry-run passes and only if the storage path is known writable):
BAMBU_ACCESS_CODE=... bash ~/.hermes/scripts/upload_and_start.sh /path/sliced.3mf filename.3mf
```

Do not use the adapter CLI directly for mutating actions. `bambu_x2d.py upload` and `bambu_x2d.py start` are intentionally fail-closed CLI commands; the underlying upload/start library functions require `HERMES_EXTERNAL_CONTROL_EXECUTOR=1`, set only by a future audited executor after the dry-run gate passes.

## Credential handling for mutating commands

- Preferred automation source is macOS Keychain, not plaintext files: `python3 ~/.hermes/scripts/bambu_credentials.py set` stores `hermes-bambu-x2d/lan-access-code`; adapters read it at runtime and do not print it.
- `BAMBU_ACCESS_CODE` remains a temporary override environment variable for one-off commands; never persist it to brain files, skill files, shell scripts, logs, or git.
- Glasses/taskpool automation must enter through `x2d_print_intent_worker.py`; P0 non-interactive start is allowed only after fresh status, preprint guard, external-control dry-run gate, and explicit `--allow-autostart`. P1/P2 must not invoke `--non-interactive-confirm`.
- `upload_and_start.sh` wrapper: `BAMBU_ACCESS_CODE=... bash ~/.hermes/scripts/upload_and_start.sh <local_3mf> <remote_name>`
- FTPS: Bambu LAN uses implicit FTPS on port 990. Upload target is `/cache/<name>`; MQTT later references it as `file:///sdcard/cache/<name>`. Printer vsFTPd may require TLS session reuse on the data channel; macOS/Python `ftplib.FTP_TLS` and some curl/lftp flows can fail with `522 SSL connection failed: session reuse required`. Use the manual implicit-FTPS implementation in `~/.hermes/scripts/bambu_x2d.py`.
- MQTT start: publish to `device/{SERIAL}/request` with `{"print": {"command": "project_file", "url": "file:///sdcard/cache/<name>", "param": "Metadata/plate_1.gcode", "subtask_id": "0", "use_ams": true}}`, wait up to 10s for ack on report topic matching sequence_id.
- If FTPS upload returns `553 Could not create file` for `/cache/<name>`, fail closed: the printer/storage currently refuses local writes (e.g. storage unavailable, LAN upload disabled, firmware/storage mode mismatch). Do not bypass by streaming ad-hoc G-code unless an explicit audited workflow exists.
- Field case 2026-05-22: official `bambu_local_print` can also fail with `start_local_print_with_record_rc=-2130` / `Failed FTP upload: 553`; `bambu_ft_tunnel.py ability` may segfault with the current dylib binding. In that case, do not keep retrying physical starts; preserve generated artifacts and use Bambu Studio GUI/cloud send until the eMMC tunnel executor is repaired.
- The 3MF must be a sliced print package containing `Metadata/plate_1.gcode`; a plain project 3MF with only model/settings is not directly printable via `project_file`. Verify with `zipinfo file.3mf | grep 'Metadata/plate_.*\.gcode'` before upload/start.

## References

- `~/.hermes/brains/external-control/brain.yaml`
- `~/.hermes/brains/external-control/tool-policy.md`
- `~/.hermes/brains/manufacturing/protocols/external-control-boundary.md`
- `references/rokid-bridge-replay-optimization.md` — Rokid Bridge replay verifier pitfalls, L0 tuning methodology, needs_attention signal calibration
- `references/bytebot-computer-use-safety.md` — Bytebot-style containerized desktop safety gates
- `references/telemetry-freshness-pitfall.md` — action-packet timestamp must be <=5s old when gate runs; generate+gate atomically

## Common Pitfalls

1. Reporting a tool/API mutation as complete without reading back target state.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] For mutations or external-system actions, command success was paired with target-state read-back.
