# Mechatronic Robot Bring-up Protocol

Purpose: extend the Manufacturing Brain from passive print/model workflows into 3D-printed mechatronic assemblies: robots, fixtures with actuators, sensorized prints, and printed shells that carry motors/electronics/control policies.

This protocol was distilled from the static review of `apirrone/Open_Duck_Mini_Runtime` at commit `32037347dc43186a017f2116bcfde7c461b81f54`. It is a reference pattern, not an integration. Do not run upstream robot scripts from Hermes.

## Ownership boundary

Manufacturing Brain owns:
- printed/mechanical assembly readiness and manufacturability;
- actuator/sensor topology documentation;
- calibration evidence schemas;
- power/thermal/mechanical risk notes for the printed assembly;
- policy-run readiness verdicts for learned/control software;
- external-control action_request drafts.

Manufacturing Brain does not own:
- serial/Bluetooth/GPIO/I2C/MQTT/USB transport execution;
- torque enable/disable, motor movement, walking, camera capture, microphone recording, heating, or any other physical action;
- runtime auth material, robot pairing material, or local device sessions;
- autonomous LLM function-calling that can move a physical robot.

All physical actions route to External-Control. Powered low-voltage/electronics design routes to Electrical Brain when current, wiring, fusing, connectors, adapter ratings, thermal soak, or certification are in scope.

## Reference patterns from Open Duck Mini Runtime

Observed patterns worth preserving:

1. Staged host bring-up
   - Raspberry Pi OS, SSH/WiFi, apt packages, I2C enablement, USB serial latency rule, and controller pairing are completed before robot runtime.
   - Hermes lesson: host prerequisites belong in a `host_readiness` evidence block, not in an action executor.

2. Explicit actuator topology
   - The runtime maps named joints to Feetech motor IDs and keeps zero/init positions and soft offsets.
   - Hermes lesson: every mechatronic print needs a named joint/actuator map, expected neutral pose, allowed range, and physical labels before powered tests.

3. Low-torque and one-by-one bring-up
   - Motor checks set low torque per motor, read position, prompt before small movement, and disable torque on exit.
   - Hermes lesson: powered motion is never the first proof. Manufacturing can require the operator to produce evidence from low-torque/read-only checks before asking External-Control for movement.

4. Sensor readiness before policy run
   - The runtime validates IMU orientation/calibration and foot contact GPIO before using the walking loop.
   - Hermes lesson: learned policies or closed-loop controllers require fresh sensor validity evidence before any policy-run action packet.

5. Policy runtime preflight
   - The walking loop depends on an ONNX model, fixed control frequency, IMU/contact/joint observations, command source, filters, and motor-target writes.
   - Hermes lesson: Manufacturing can judge whether a policy-run is ready, but only External-Control may execute it.

6. Vision/LLM action loop is high-risk
   - The repo contains an experimental OpenAI function-calling loop that can move the robot and take pictures.
   - Hermes lesson: LLM-to-robot tools must be behind External-Control gates with device identity, command scope, fresh telemetry, idempotency, audit, confirmation, and a stop/rollback path.

## Required evidence packet

For any printed mechatronic assembly, create a packet shaped like:

```yaml
schema: hermes_mechatronic_bringup_v1
assembly_id: unique-human-readable-id
source:
  repository_or_model_url: ...
  commit_or_version: ...
  local_artifact_hashes: []
printed_parts:
  material: PLA|PETG|ABS|...
  printer_profile: ...
  slicer_report: /path/report.json
  post_processing_required: []
actuators:
  - name: left_hip_pitch
    id_or_channel: 22
    bus_or_driver: feetech_serial|pwm|stepper|servo|...
    neutral_position: ...
    safe_range: ...
    low_power_test_required: true
sensors:
  - name: imu
    bus: i2c
    orientation_assumption: ...
    calibration_artifact: ...
  - name: left_foot_contact
    pin_or_channel: ...
power_and_thermal:
  voltage_nominal: ...
  current_budget: ...
  fuse_or_protection: ...
  thermal_soak_required: true
calibration:
  mechanical_zero_proof: ...
  soft_offsets: ...
  sensor_calibration: ...
policy_or_firmware:
  artifact_path: ...
  artifact_hash: ...
  control_frequency_hz: ...
  input_observation_contract: ...
  output_action_contract: ...
  simulation_or_bench_proof: ...
readiness:
  verdict: blocked|read_only_ready|bench_ready|external_control_action_request_ready
  blockers: []
  required_human_checkpoints: []
external_control:
  physical_action_required: false
  action_request_path: null
```

## Gate sequence

1. Source and print artifact provenance
   - Require source URL/version, local hashes, license/provenance notes, STL/3MF/G-code/slicer reports, and material/profile assumptions.
   - Block if the printed assembly has unknown scale, unknown material, missing critical parts, or unclear post-processing.

2. Passive mechanical inspection
   - Verify all printed parts fit, joints move unpowered, fasteners/seats are present, cable paths do not pinch, and service access exists.
   - Block if a motor/gear/linkage can hard-stop before software limits, if cables can snag, or if the center of mass/support stance is unknown for a mobile robot.

3. Electrical/power handoff
   - If power budget, wiring, battery, charger, fusing, adapter, connector, LED/heater, or thermal risk appears, request Electrical Brain review before any powered action.
   - Manufacturing may document assumptions but must not bless unsafe electrical design alone.

4. Actuator identity and read-only telemetry
   - Require actuator ID/channel map, bus/driver type, expected neutral pose, read-only position/status evidence where possible, and a disabled-torque or low-power start plan.
   - Block if any actuator identity is ambiguous or mirrored left/right mapping is unverified.

5. Sensor orientation and freshness
   - Require IMU orientation/remap proof, calibration artifact when available, contact-switch polarity, camera/mic privacy notes, and telemetry age thresholds.
   - Block if a closed-loop policy depends on a stale/missing sensor.

6. Low-risk bench motion proposal
   - Manufacturing may prepare an External-Control action_request for a bounded bench test: one actuator, low torque/power, tiny delta, short timeout, operator hands-clear confirmation, emergency stop path, and audit.
   - Manufacturing must not execute the motion.

7. Policy/controller run readiness
   - Before a walking/closed-loop action request, require policy artifact hash, input/output contract, control frequency, observation shape, simulation/replay proof, action scaling, filters/limits, command source, stop condition, and rollback plan.
   - Block if any learned policy can write motor targets without fresh telemetry and operator confirmation.

8. Field/mobile action gate
   - Mobile robot motion, autonomous navigation, LLM function calls, or camera-guided movement is high-risk. Route to External-Control with explicit geofence, duration, speed/torque limit, command whitelist, collision/people/pet exclusion, and manual stop.

## Hard vetoes

Manufacturing verdict must be `blocked` when any of these are true:
- no actuator ID/channel map;
- motor direction, zero pose, or left/right mapping is unknown;
- low-torque/read-only check is missing before first powered movement;
- IMU/sensor orientation is unknown for a balancing or walking policy;
- policy artifact hash or observation/action contract is unknown;
- LLM/tool loop can call movement functions without External-Control;
- power/current/thermal/fusing is unknown for a powered build;
- physical action would occur without fresh telemetry, idempotency, audit, and human confirmation.

## Output verdicts

Use one of:

- `blocked`: missing critical evidence or unsafe boundary.
- `read_only_ready`: static/model/mechanical review can continue, no power/motion.
- `bench_ready`: enough evidence exists to draft a bounded External-Control bench-test action_request.
- `external_control_action_request_ready`: packet is complete for External-Control review/execution, but Manufacturing still does not execute.

## Gap matrix template

| Source pattern | Manufacturing target | Risk if absent | Concrete next step |
| --- | --- | --- | --- |
| Host setup / bus prerequisites | `host_readiness` evidence | runtime fails unpredictably | capture OS/bus/driver/controller setup proof |
| Joint name -> motor ID map | actuator topology | wrong motor moves | require labelled map and read-only position proof |
| Low-torque per-motor test | bench motion gate | sudden high-force movement | draft one-actuator low-torque action_request |
| Soft offsets / zero pose | calibration schema | misaligned mechanisms / falls | record zero pose photo + offsets + acceptance |
| IMU/contact validation | sensor freshness gate | closed-loop instability | require sensor sample and orientation proof |
| ONNX policy loop | policy-run preflight | unbounded learned action | require hash, observation/action contract, frequency, filters, stop path |
| LLM movement tools | External-Control boundary | autonomous physical harm | fail closed unless gated by external-control packet |

## Verification

After editing this protocol or related routing, run:

```bash
python3 ~/.hermes/scripts/brainctl.py --json brains validate
python3 ~/.hermes/scripts/brainctl.py --json brains route '3D打印机器人舵机校准和行走前检查'
```
