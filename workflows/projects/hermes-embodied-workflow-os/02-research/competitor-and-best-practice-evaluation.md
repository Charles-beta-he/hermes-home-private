# Competitor and Best-Practice Evaluation — Hermes Embodied Workflow OS

Generated: 2026-07-02T18:58:00+08:00
Status: advisory evidence pack; no runtime implementation claim.
Source samples: `02-research/competitor-source-samples-20260702.json`

## Evaluation frame

Hermes should not copy one competitor category. The target combines:

- local-first agent brain and evidence ledger;
- workflow graph/state/replay;
- adapter/port architecture;
- operator workbench;
- smart-home/IoT integration patterns;
- cyber-physical/robot safety gates;
- mobile/glasses lightweight observation surfaces;
- NAS/archive topology.

## Competitor / reference classes

| Class | Examples sampled | What to absorb | What not to copy blindly | Hermes consequence |
|---|---|---|---|---|
| Smart-home automation | Home Assistant, openHAB, Matter | device registry, integration catalog, local-control bias, entity state model | device-centric worldview as the whole product; assuming homes/devices are trusted | `CapabilityManifest` + `AdapterRegistry`; external devices are capabilities with gates, not trusted actors |
| Flow-based automation | Node-RED | visible flow graph, low-code adapter wiring, debugability | letting arbitrary flows become policy/core; spaghetti flows with no evidence/readback | Web Workbench may visualize flows, but Core owns state, gates, and evidence |
| Robotics middleware | ROS 2, micro-ROS | explicit nodes/topics/actions, robot telemetry, embedded bridge patterns | starting with robot stack before workflow contracts; robot as separate brain | robot is an `Actor`/adapter consuming `ActionIntent`; ROS layer stays behind adapter |
| Messaging/protocol | MQTT, WebRTC | lightweight pub/sub; realtime media/data channels | protocol as architecture; coupling core state to transport | transports feed `Observation` and receive render/action packets only |
| Connectivity | Tailscale, Cloudflare Tunnel | secure connectivity, remote node reachability, access boundaries | proxy/tunnel layer owning business logic or authority | domestic/proxy layer remains transport-only |
| Agent workflow frameworks | LangGraph, AutoGen, OpenAI Agents SDK | graph/state/checkpointing, multi-agent handoff, guardrails/tools concepts | delegating safety/authority to model framework; framework lock-in | Hermes Core contracts remain framework-neutral; model runners are implementation detail |
| HCI/operator guidance | Apple HIG, NASA TLX | task-appropriate surfaces, workload/attention constraints | one UI for every context | EntryRecommendationEngine chooses Web/mobile/glasses/embedded by required capability/workload |

## Product positioning

Hermes Embodied Workflow OS should position as:

> A stable workflow and capability core for Hermes that lets multiple human, software, and physical actors collaborate over the same evidence-backed task graph.

It is not:

- a replacement for Home Assistant;
- a robot OS;
- a Web app first;
- a generic low-code automation board;
- a model-framework-specific agent stack.

## Differentiation

1. Evidence-first: every state change and action claim links to evidence/readback.
2. Entry-agnostic: Web/PWA/glasses/CLI/robot all submit normalized events/observations.
3. Actor-agnostic: human, robot, embedded node, external service are capability-bearing actors.
4. Safety-default: physical/external/destructive actions require SafetyGate + ExternalControlGate.
5. Replayable: EvidenceLedger + reducer can reconstruct WorldState.
6. Portfolio-aware: integrates existing Hermes projects as modules instead of merging facts/secrets.

## Best-practice patterns to adopt

| Pattern | Source class | Concrete design rule |
|---|---|---|
| Ports/adapters | Hexagonal/Clean Architecture | Core imports no adapter/platform code. |
| Device/entity registry | Home Assistant/openHAB/Matter | Capabilities declare identity, risk, auth, schema, readback, audit. |
| Flow visibility | Node-RED | Workbench visualizes but does not become authoritative runtime. |
| Topics/actions/readback | ROS/MQTT | All external actions have action id, telemetry freshness, idempotency, readback. |
| State graph/checkpoint | LangGraph-style agent workflows | WorkflowKernel state is reducer/checkpoint driven, not chat transcript driven. |
| Guardrails | Agent SDKs/safety frameworks | Safety policies are deterministic gates around model outputs. |
| Task-appropriate UI | HIG/workload methods | EntryRecommendationEngine selects the least-burdensome adequate surface. |

## Kill criteria / stop signs

Stop and ask for human intervention if any next step requires:

- real hardware control, robot actuation, locks, heating, mains, high-power, grippers, cutters;
- external dispatch, broad fan-out, publish/deploy/push, destructive operations, payment/credential entry;
- committing through a degraded/not-certified local governance hook;
- choosing a physical device/protocol stack with cost/procurement implications;
- accepting formal citation quality for blocked DOI/standards sources.
