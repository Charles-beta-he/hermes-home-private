# Web4.0 Agent OS Gap → Hermes Local Workstreams

Updated: 2026-07-06T13:57:39+08:00

## Gap map

| Web4.0 Agent OS gap | Local Hermes workstream | Internal status target | External dependency boundary |
|---|---|---|---|
| Machine-readable world/service semantics | Capability Graph + Service Contract Registry | Build local schema/projection/doctor; map tools/skills/profiles | Global service/provider adoption of agent-readable contracts |
| Identity/authorization/payment | Authority Ledger + grants + receipts | Build local grant/receipt/readback; sealed-secret handoff | DID/VC/wallet/bank/legal agent authorization |
| Personal context ownership | Personal Data Vault | Classify memory/profile/files; export gates; retention policy | OS/app data APIs, secure enclave, cross-device vault |
| Long-running autonomy | Mission Runtime + Taskpool/Cron integration | State machine, evidence DAG, wake signals, stop conditions | Platform background permissions, external service SLAs |
| Multi-model reliability | Multi-model Governance Layer | Role registry, route review, evidence packets, dissent/certification | Model provider SLA, private model hosting, cost budgets |
| Agent-to-agent collaboration | Proposal Inbox + A2A local schema | External/subagents proposal-only by default | A2A identity, reputation, liability, marketplace protocols |
| Physical/spatial world | Device Registry + observe-first policy | computer/smart-home/glasses as typed devices; physical gates | Hardware SDKs, sensor streams, robotics/IoT permissions |
| User control and audit UX | Personal OS Shell | CLI/dashboard receipts, permissions, missions, risk/model consoles | Mobile/desktop OS-level integration and notifications |

## Workstream ordering

1. Capability Graph and Service Contract v0.
2. Authority Ledger and side-effect taxonomy v0.
3. Data Vault classification v0.
4. Mission Runtime canonical state and Evidence DAG v0.
5. Multi-model Governance route/certification contracts.
6. Non-human boundary handling and external dependency tickets.
7. UX shell projections.
8. Device Registry observe-first projection.
9. Runtime integration slices after schema/read-only proof.

## Automation principle

When a boundary appears, the system must not default to “ask human”. It must:

1. classify the missing element;
2. prepare the maximum safe local artifact;
3. create a machine-readable AuthorityBoundary or ExternalDependency ticket;
4. continue adjacent safe workstreams;
5. surface a decision packet only when exact authority or external ecosystem support is truly required.
