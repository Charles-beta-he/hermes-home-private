# Core Works and Arguments
Created: 2026-07-02T18:43:34+08:00

This is an evidence-backed architecture reading list for the long-term embodied workflow plan. It is not a publication-grade bibliography yet; blocked sources are marked.

## Argument map
| Argument | Core works / evidence | Architectural consequence |
|---|---|---|
| Stable module boundaries prevent accidental complexity | Parnas 1972; Brooks 1986 | Define TaskGraph/Observation/ActionIntent/Evidence contracts before endpoints/hardware. |
| Core policy must be isolated from UI/framework/device/database details | Cockburn Ports & Adapters; Clean Architecture | Web/PWA/glasses/robot are adapters, not separate brains. |
| Domain language must be explicit and shared | DDD/Evans | Use TaskGraph, Actor, Capability, ActionIntent as ubiquitous language across human and robot actors. |
| State should be replayable and evidence-linked | Fowler Event Sourcing; DDIA | Append-only EvidenceLedger + reducers; NAS archives evidence, not hot runtime state. |
| Human/robot assistance depends on situation awareness | Endsley; NIST CPS | Observation -> WorldState -> Planner -> Verification loop; ask for better view when uncertain. |
| Operator surfaces should expose constraints, not fake certainty | Rasmussen/EID candidate; Apple HIG | Workbench shows gates/evidence/capabilities/action queue; mobile/glasses render short task-appropriate views. |
| Cyber-physical/robot safety is a separate boundary | NIST CPS; IEC 61508; ISO 10218 | SafetyGate + ExternalControlGate + telemetry/readback/audit before actuation. |

## Source ledger

### W-PARNAS-1972 — David L. Parnas, On the Criteria To Be Used in Decomposing Systems into Modules
- URL: https://dl.acm.org/doi/10.1145/361598.361623
- Evidence status: doi_known; ACM fetch blocked 403 in this session
- Supports: information hiding, stable module boundaries before implementation

### W-BROOKS-1986 — Frederick P. Brooks, No Silver Bullet
- URL: https://worrydream.com/refs/Brooks-NoSilverBullet.pdf
- Evidence status: HTTP 200 application/pdf sampled
- Supports: essential vs accidental complexity, avoid accidental complexity from platform-specific endpoint sprawl

### W-COCKBURN-PORTS — Alistair Cockburn, Hexagonal Architecture / Ports and Adapters
- URL: https://alistair.cockburn.us/hexagonal-architecture/
- Evidence status: HTTP 200; page title hexagonal-architecture
- Supports: core isolated from UI/device/database adapters, ports before adapters

### W-CLEAN-ARCH — Robert C. Martin, Clean Architecture
- URL: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Evidence status: HTTP 200; page title Clean Coder Blog
- Supports: dependency rule inward toward policy/core, UI/framework/database as details

### W-DDD-EVANS — Eric Evans / Domain Language DDD Resources
- URL: https://www.domainlanguage.com/ddd/
- Evidence status: HTTP 200; page title DDD Resources - Domain Language
- Supports: ubiquitous language: TaskGraph/ActionIntent/Observation as domain contracts

### W-FOWLER-EVENT-SOURCING — Martin Fowler, Event Sourcing
- URL: https://martinfowler.com/eaaDev/EventSourcing.html
- Evidence status: HTTP 200; page title Event Sourcing
- Supports: append-only event/evidence ledger, replay/debug/audit

### W-DDIA — Martin Kleppmann, Designing Data-Intensive Applications
- URL: https://dataintensive.net/
- Evidence status: HTTP 200; page title Designing Data-Intensive Applications
- Supports: logs, derived state, local state vs archive topology, replayable data systems

### W-ENDSLEY-SA — Mica R. Endsley, Toward a Theory of Situation Awareness in Dynamic Systems
- URL: https://doi.org/10.1518/001872095779049543
- Evidence status: DOI known; DOI fetch blocked 403 in this session
- Supports: Observation -> WorldState -> projection/decision loop, human/robot shared situation awareness

### W-RASMUSSEN-EID — Rasmussen & Vicente, Ecological Interface Design / work-domain constraints
- URL: https://doi.org/10.1016/0953-5438(92)90030-S
- Evidence status: DOI/page unresolved in session; keep as candidate requiring later bibliographic verification
- Supports: Workbench should expose constraints/gates/evidence, not only pretty UI

### W-NIST-CPS — NIST Framework for Cyber-Physical Systems
- URL: https://www.nist.gov/publications/framework-cyber-physical-systems-volume-1-overview
- Evidence status: HTTP 200 sampled
- Supports: cyber-physical separation, telemetry, actuation, trustworthiness concerns

### W-IEC-61508 — IEC 61508 Functional Safety overview
- URL: https://www.iec.ch/functional-safety
- Evidence status: fetch blocked 403 in this session; standard family cited as safety reference, not implementation proof
- Supports: fail-safe/default-off safety gate principle for physical actuation

### W-ISO-10218 — ISO 10218 Robots and robotic devices safety requirements
- URL: https://www.iso.org/standard/73933.html
- Evidence status: fetch blocked 403 in this session; standard family cited as robot-safety reference, not implementation proof
- Supports: robot actor requires safety-rated constraints, telemetry/readback, human gate

### W-APPLE-HIG — Apple Human Interface Guidelines
- URL: https://developer.apple.com/design/human-interface-guidelines/
- Evidence status: HTTP 200; page title Human Interface Guidelines
- Supports: mobile/PC/glasses surfaces should be experience-specific renderers over same core contract

## Open research gaps
- Verify blocked standards/DOIs through accessible library/standards pages before formal publication or implementation claims.
- Add robotics middleware comparison later (ROS 2, micro-ROS, MQTT, WebRTC, Matter) only after core contracts are frozen.
- Add HCI/wearable-specific papers when glasses UX moves beyond evidence intake into overlay guidance.
