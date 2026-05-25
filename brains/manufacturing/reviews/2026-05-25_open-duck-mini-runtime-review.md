# Open Duck Mini Runtime Reference Review

Source: https://github.com/apirrone/Open_Duck_Mini_Runtime
Reviewed commit: `32037347dc43186a017f2116bcfde7c461b81f54`
Local static clone: `/Users/charles/.hermes/runs/open-duck-mini-review-20260526-005722/repo`
Multi-model run: `/Users/charles/.hermes/tick-20260525-170109-142610-p58635-76e6127a-4a488ff3/`
Fanout certification: 4/5 planner success, min quorum 3, truth grounded by supplied evidence bundle.

## Scope

This is not an integration plan for operating Open Duck Mini hardware. The repository is used as a manufacturing-brain reference for printed mechatronic/robot assembly bring-up: actuator topology, calibration evidence, sensor readiness, policy-run gates, and physical-action boundaries.

No hardware scripts were run. Static verification only:

```bash
python3 -m compileall -q mini_bdx_runtime scripts
```

Exit code: 0.

## What the repo is

Open_Duck_Mini_Runtime is a Raspberry Pi / Python runtime for Open Duck Mini / mini BDX robot bring-up and operation. It is not a 3D slicer or CAD model repository.

Evidence:
- README describes Raspberry Pi Zero 2W setup, apt packages, I2C enablement, USB serial latency, Xbox Bluetooth pairing, IMU/motor tests, duck_config, joint offsets, and running an ONNX walking policy.
- `setup.cfg` dependencies include `rustypot`, `onnxruntime`, `adafruit-circuitpython-bno055`, `pygame`, Feetech `pypot`, and `openai`.

## Reusable patterns for Manufacturing Brain

| Source pattern | Manufacturing target | Risk if absent | Concrete next step |
| --- | --- | --- | --- |
| Raspberry Pi / I2C / USB serial / controller setup in README | `host_readiness` evidence block | physical runtime fails after print is assembled | Add mechatronic bring-up protocol with host readiness packet |
| `rustypot_position_hwi.py` joint-name to motor-ID map | actuator topology schema | wrong or mirrored motor moves | Require named actuator ID/channel map before motion packets |
| zero/init positions and `joints_offsets` | mechanical zero + soft-offset calibration | printed links start misaligned or fall | Require zero-pose proof, offset record, and human acceptance |
| low-torque ramp in HWI and one-by-one `check_motors.py` | low-power bench gate | sudden high-force movement | Only draft External-Control low-torque micro-move action_request after read-only proof |
| `check_voltage.py` per-joint voltage readout | power readiness signal | brownout/overvoltage hidden until movement | Add voltage/current/power evidence; hand off electrical risk |
| BNO055 IMU orientation/calibration in `raw_imu.py` | sensor orientation/freshness gate | balance policy sees inverted/stale state | Require IMU orientation/calibration evidence for closed-loop controllers |
| foot contacts on GPIO D22/D27 | contact sensor evidence | gait/controller lacks ground-truth contact | Require contact polarity/sample proof where policy uses contact input |
| ONNX walking loop at fixed control frequency | policy-run preflight | learned policy writes unsafe motor targets | Require artifact hash, observation/action contract, freq, filters, stop path |
| `fc_test.py` OpenAI function calls for movement/camera | External-Control boundary | LLM autonomously moves robot | Manufacturing fails closed and emits action_request only; External-Control owns execution |

## Key veto learned

A naive “robot runtime works, so let it walk” approach is unsafe. Manufacturing Brain must veto walking or powered motion when any of these are missing:

- actuator ID/channel map;
- zero pose and soft-offset evidence;
- low-torque/read-only motor check;
- IMU/contact sensor orientation and freshness;
- policy artifact hash and observation/action contract;
- power/current/thermal protection evidence;
- External-Control packet with fresh telemetry, idempotency, audit, and human confirmation.

## Multi-model synthesis

Consensus was weak but directional: all useful planner outputs converged on documentation/protocol additions rather than runtime integration. The strongest agreed direction was:

1. Add a dedicated mechatronic robot bring-up protocol.
2. Add routing hints/capabilities for actuator calibration, printed robot bring-up, policy-run preflight, and physical-action handoff.
3. Patch the Manufacturing Brain skill to load this protocol and preserve the External-Control boundary.
4. Keep an evidence review artifact for future source-driven improvements.

## Resulting Hermes changes

Implemented artifacts:

- `~/.hermes/brains/manufacturing/protocols/mechatronic-robot-bringup.md`
- `~/.hermes/brains/manufacturing/brain.yaml` routing/capability additions
- `~/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` protocol reference and workflow note

## Non-goals preserved

- No Open Duck Mini hardware operation.
- No motor, IMU, camera, Bluetooth, OpenAI API, GPIO, or serial scripts executed.
- No runtime auth material or robot pairing material stored.
- No claim that Hermes can operate Open Duck Mini hardware.
