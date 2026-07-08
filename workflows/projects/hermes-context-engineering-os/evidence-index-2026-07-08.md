# Evidence Index — Context Engineering OS

Timestamp: 2026-07-08T03:11:00Z
Scope: local foundation for Hermes Context Engineering OS.

## Source Packet

| id | source | locator | claim | landing |
|---|---|---|---|---|
| SRC_SURVEY | arXiv | https://arxiv.org/abs/2507.13334 | Context Engineering systematically optimizes LLM inference information payloads across retrieval/generation, processing, management, RAG, memory, tool reasoning, and multi-agent systems. | Context Packet schema + Evidence DAG |
| SRC_COLEAM | GitHub | https://github.com/coleam00/context-engineering-intro | AI coding reliability improves when docs, examples, project rules, PRP, and validation gates are assembled as context. | Spec Packet + validation gates |
| SRC_SMOOTHAGENT | arXiv | https://arxiv.org/abs/2607.00151 | Long-horizon agents use context engineering strategies such as offloading, reduction, isolation, and lookahead transformations to manage growing context and TTFT. | Future runtime compression/isolation/cache-aware stage |
| SRC_HERMES_SKILL | local skill | /Users/charles/.hermes/skills/context-engineering-os/SKILL.md | Hermes Context Engineering OS should assemble objective, evidence, memory, skills, project state, tools/authority, execution, and verification into minimal sufficient packets. | Installed skill |

## Readback Requirements

- Validate JSON packet sample with `scripts/context_packet_lint.py`.
- Parse profile/schema/receipt JSON.
- Read back skill and linked reference.
- Do not claim core runtime/taskpool/cron/dashboard integration until those surfaces are separately authorized and tested.
