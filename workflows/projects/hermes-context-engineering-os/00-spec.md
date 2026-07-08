# Spec Packet — Hermes Context Engineering OS

## Goal

Make Context Engineering operational inside Hermes as a reusable, evidence-governed workflow and future runtime surface.

## Source Facts

- `A Survey of Context Engineering for Large Language Models` defines CE as systematic optimization of LLM information payloads and decomposes retrieval/generation, processing, management, RAG, memory, tool reasoning, and multi-agent systems.
- `context-engineering-intro` frames AI coding failures as context failures and uses PRP + validation gates.
- `SmoothAgent` shows context engineering has runtime/serving consequences: offloading, reduction, isolation, transformation overhead, KV cache/TTFT.
- Hermes already has adjacent surfaces: skills, memory, project profiles, SSOT, taskpool, tool authority, readback, verification gates.

## Business / Runtime Rules

1. Context Packet is the unit of work for complex tasks.
2. Evidence DAG is the unit of truth for material claims.
3. Authority boundary is independent from knowledge availability.
4. Durable learning must pass landing-zone classification.
5. Completion claims require claim-linked evidence.

## Acceptance Criteria

- Local SSOT and project profile exist.
- JSON schema validates a sample packet.
- Lint script fails on missing required fields and passes on the sample.
- Skill has a core works reference and can be read back.
- Extension stages classify safe local work vs authority-gated work.

## Negative Cases

- Do not claim runtime integration until Hermes core code/prompt path is changed and tested.
- Do not claim taskpool/cron integration until exact local lifecycle or scheduler authority is opened and read back.
- Do not put task progress into memory.
- Do not use external dispatch or production side effects.
